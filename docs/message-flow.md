# Message flow

This page follows one chat line from the keyboard to the socket, and one line from the socket to the chat view. For protocol details (registration, numerics, CTCP) see [irc-protocol.md](irc-protocol.md). For the widgets and thread pool, see [pyqt.md](pyqt.md). For the Qt and asyncio bridge, see [architecture.md](architecture.md).

Files and methods named here live in [`rude_gui.py`](../src/rudechat4/rude_gui.py) and [`rude_client.py`](../src/rudechat4/rude_client.py) unless noted. Everything runs on the main thread except text decoding, which runs in Qt's global thread pool.

## Overview

```
 OUTGOING                                         INCOMING

 RudeMessageEntry (QLineEdit)                     TCP / TLS socket
   | returnPressed                                  |  StreamReader.read(4096), 256 s timeout
   v                                                v
 bind_return_key lambda                           handle_incoming_message
   | loop.create_task                               |  decode UTF-8, strip controls,
   v                                                |  buffer, split on \r\n, tokenise
 RudeGui.on_enter_key                               v
   | history, clear field                         match tokens.command
   v                                                |  PRIVMSG
 command_parser                                     v
   |-- "/cmd ..."  -> cmd_* / inline cases        prtcl_PRIVMSG
   |-- plain text  -> handle_user_input             |  ignore list, mode symbol,
   v                                                |  emoji, green text, CTCP check
 handle_user_input                                  v
   | away reset, escape, pronouns,                 +-- target is you ---> prepare_direct_message
   | split at 420 chars                            |
   v                                               +-- else ------------> handle_channel_message
 send_message_chunks                                      |  save_message -> channel_messages
   | per line: emoji, green text                          |  log_message  -> Logs/*.txt
   v                                                      |  display_message or pop-out or highlight
 send_message  (PRIVMSG ... \r\n, drain)                  v
   |                                                 gui.insert_text_widget
   +--> local echo + history + log                      |
        (the server does not echo)                      v
                                                     BatchDecoderWorker (thread pool)
                                                        |  decoder: IRC and ANSI codes -> (text, format)
                                                        |  find_urls
                                                        v
                                                     message_decoded signal (queued to main thread)
                                                        v
                                                     handle_decoded_text -> tag_text -> tag_urls
                                                        v
                                                     insert_and_scroll
                                                     then: notify_user_if_mentioned
```

The client never reads its own `PRIVMSG` back from the server, because it doesn't request `echo-message` (see [capabilities](irc-protocol.md#capabilities)). Outgoing lines are drawn and stored locally at send time.

## Outgoing: keyboard to socket

### 1. Input box to `on_enter_key`

`RudeGui.__init__` schedules `bind_return_key` with `QTimer.singleShot(0, ...)` ([line 358](../src/rudechat4/rude_gui.py#L358)). That method ([line 626](../src/rudechat4/rude_gui.py#L626)) connects `text_field.returnPressed` to a lambda that calls `loop.create_task(self.on_enter_key(), name="on_enter_key")`. The task name matters: `stop_async_loop` skips tasks named `on_enter_key` and `quit_client_task` when it cancels everything on quit, so a `/quit` typed in the box can finish.

[`on_enter_key`](../src/rudechat4/rude_gui.py#L1522) does four things:

1. Reads `text_field.text()`.
2. If the text isn't empty, appends it to `entry_history` and keeps only the last 10 entries. The Up and Down keys (`ArrowKeyEventFilter`) walk that list.
3. Clears the field and scrolls the chat view to the bottom.
4. Awaits `self.irc_client.command_parser(user_input)`.

`self.irc_client` is whichever server is selected. Your line goes to that server's client and to its `current_channel`. Empty input still reaches `command_parser` and stops in `handle_user_input`.

### 2. `command_parser`

[`command_parser`](../src/rudechat4/rude_client.py#L2523) splits the line into `args` only when it starts with `/`. For plain text, `args` is empty and `primary_command` is `None`, which matches `case None` and calls `handle_user_input`. A lone `/` also gives empty `args`, so it is sent as chat text.

A `/word` that matches no `case` does nothing and prints no error. [commands.md](commands.md) lists the commands. The ones that send chat or raw lines themselves are:

| Command | Send path |
| --- | --- |
| `/msg nick text` | `send_message("PRIVMSG ...")`, then `query_msg_handler` stores and logs it, then `open_dm` if needed |
| `/query nick [text]` | `cmd_query`: `open_dm`, then the same as `/msg` |
| `/me text` | `cmd_me`: sends `\x01ACTION ...\x01`, draws and stores it locally. It doesn't call `log_message`. |
| `/notice`, `/broadcast`, `/mac`, `/cowsay`, `/fortune`, `/mock` | Their own `cmd_*` methods |
| `/quote raw` | Sends the text after `/quote` as a raw line with no checks |

These bypass `handle_user_input`, so they skip the 420 character chunking, the pronoun replacement and the color escaping described next. `/me` does call `escape_color_codes`.

### 3. `handle_user_input`

[`handle_user_input`](../src/rudechat4/rude_client.py#L2842) prepares a normal chat line:

1. Returns if the text is empty.
2. If `use_auto_away` is on, calls `watcher.update_last_message_time()` so the auto-away timer restarts.
3. `remove_away_status()`: if you are marked away, deletes the entry, clears the highlight and sends `AWAY`.
4. `escape_color_codes` ([line 2916](../src/rudechat4/rude_client.py#L2916)): rewrites a typed `\xNN` (four characters) into the character with that hex value. This is how you type `\x03` to send a color code by hand. The formatting shortcuts in `RudeMessageEntry` insert the real control characters.
5. If `replace_pronouns` is on, calls `replace_pronouns(text, current_channel)`.
6. If there's no `current_channel`, prints "No channel selected" and stops.
7. Chunks the text.

Chunking is simple. If the first line is longer than 420 characters, the whole string is cut into 420 character slices. Otherwise it stays as one chunk. Things to know:

- The test only looks at the first line. A multi-line paste with a short first line isn't cut by this step, but `send_message_chunks` later sends each line separately.
- The cut is by characters, not bytes, and it falls wherever the 420th character is, including mid-word. A line of many multi-byte characters can go past the 512 byte IRC limit, and the client doesn't subtract the prefix the server adds. I didn't see a check for either.
- Nothing strips `\r` or `\n` from the text at the `send_message` level.

### 4. `send_message_chunks`

[`send_message_chunks`](../src/rudechat4/rude_client.py#L2703) loops over chunks, then over `chunk.split('\n')`, skipping empty lines. For each line:

1. `replace_emojis`, then `green_texter` (wraps lines that start with `>` or similar arrows in green when `green_text` is on).
2. `await send_message("PRIVMSG <channel> :<line>")`.
3. Looks up your mode symbol for the channel with `get_user_mode` and `get_mode_symbol`, and colors any known nicknames in the line with `color_message_mentions`.
4. If the target is the current channel, inserts the line into the chat view through `gui.insert_text_widget`. It does not go through `display_message`.
5. Stores and logs the line. For a channel target, `user_input_channel_message` appends to `channel_messages[server][channel]` and calls `log_message(..., is_sent=True)`. For a DM, `user_input_dm_message` does the same and then `_away_user_helper` warns you if the other person is away.
6. Sleeps 0.7 s before the next line, unless this was the only chunk with the only line. This is the client's flood control.

The channel versus DM decision is `channel.startswith(...)` against `chantypes` from ISUPPORT.

[`user_input_dm_message`](../src/rudechat4/rude_client.py#L2812) checks `self.current_channel` against `channel_messages` but then creates the list for `channel`. If the current tab isn't in the dict, this would replace the history for the DM target with an empty list. Most of the time the current tab is in the dict, so it rarely matters. I haven't triggered it.

### 5. `send_message`

[`send_message`](../src/rudechat4/rude_client.py#L688) is the only place the client writes to the socket. It encodes `f'{message}\r\n'` as UTF-8, writes it, and awaits `drain()` with a 10 second timeout. A connection error prints a notice in the chat view and the line is lost. There is no send queue and no retry. See [irc-protocol.md](irc-protocol.md#keep-alive-and-timeouts) for what does and doesn't trigger a reconnect.

### Pop-out windows

A pop-out has its own input box. [`RudePopout.insert_and_send_message`](../src/rudechat4/GUI/rude_popout.py#L761) builds the line itself and does not use `command_parser` for plain text. It sends `PRIVMSG` through its own `send_message` method as a new task, so it skips chunking, emoji replacement, green text, pronoun replacement and the away reset. It then calls `save_message` and `log_message` with `is_sent=False`.

Inside the pop-out, `/mac` and `/me` have special cases. The `case None` branch for other slash commands can't match, because the code does `match args[0]` on a string. As written, a command such as `/join #x` typed in a pop-out appears to be sent to the channel as chat text. I haven't run it.

## Incoming: socket to chat view

### 1. Read, decode and frame

[`handle_incoming_message`](../src/rudechat4/rude_client.py#L2143) is a task started by `create_tasks`. Each pass:

1. `await asyncio.wait_for(reader.read(4096), 256)`. A timeout, an `OSError` or an empty read triggers `reconnect` (details in [irc-protocol.md](irc-protocol.md#reconnect)). `CancelledError` ends the loop.
2. `data.decode('UTF-8', errors='ignore')`. Characters split across two reads are lost.
3. Removes a few terminal control sequences, and IRC color codes if `use_irc_colors` is off.
4. Appends to `buffer` and peels off lines at each `\r\n`. A partial last line stays in the buffer for the next read.
5. `irctokens.tokenise(line)`. A `ValueError` or `IndexError` prints a notice in the chat view and skips the line.

### 2. Dispatch

A `match tokens.command` sends the line to a handler. Chat lines go to `prtcl_PRIVMSG`. The full table of commands and numerics is in [irc-protocol.md](irc-protocol.md#commands-and-numerics). Each dispatch sits inside one `try` that logs and moves on, so a handler error costs one line, not the connection.

### 3. `prtcl_PRIVMSG`

[`prtcl_PRIVMSG`](../src/rudechat4/rude_client.py#L4465) takes the nick, target and text, and applies these steps in order:

1. `should_ignore_sender`: `fnmatch` of the full `nick!user@host` string against every pattern in `ignore_list`. A match drops the line with no trace.
2. Builds a `[HH:MM:SS] ` timestamp from the local clock. The server's time isn't used because `server-time` isn't requested.
3. Looks up the sender's mode symbol from `user_modes[target]` (only if `display_user_modes` is on).
4. `replace_emojis`, then `green_texter`, on the incoming text. The result is `gmessage`.
5. If the raw text is a CTCP (`\x01...\x01`), hands it to `handle_ctcp` and returns. See [CTCP](irc-protocol.md#ctcp).
6. If `target == self.nickname`, it's a DM. Otherwise it's a channel message. The test is a plain, case-sensitive string compare.
7. Calls `prepare_direct_message` (after `get_direct_message_target`, which may send a `WHOIS`) or `handle_channel_message`.
8. Calls `notify_user_if_mentioned`.

The same method runs for ZNC playback, with `znc_privmsg=True`. That flag changes the storing step below.

### 4. Channel messages

[`handle_channel_message`](../src/rudechat4/rude_client.py#L1684) has three branches:

| Branch | When | What it does |
| --- | --- | --- |
| ZNC playback | `znc_privmsg` is true | `save_message`, `log_message`, then highlight. Nothing is drawn. |
| Background channel | The target isn't the current channel and isn't popped out | `save_message`, `log_message`, then `highlight_channel_if_not_current` |
| Visible | Everything else (current channel, or a popped-out channel) | `save_message`, `log_message`. Then `display_message`, or `pip_to_pop_out` if the channel has its own window. |

The helpers:

- [`save_message`](../src/rudechat4/rude_client.py#L1812) appends a formatted line (`[time] <@nick> text\n`, with the nick colored by `ansi_color_nickname` and known nicknames in the text colored by `color_message_mentions`) to `channel_messages[server][channel]`. For a DM it keys the list by the sender. This list is the source for redrawing a channel when you switch to it.
- [`log_message`](../src/rudechat4/rude_client.py#L2280) appends to `Logs/irc_log_<server_name>_<channel>.txt` in the config folder, but only when `use_logging` is on. It writes `[date time] <nick> text` using the text before nick coloring. IRC control codes in the text stay in the file. Multi-line text gets continuation lines.
- [`display_message`](../src/rudechat4/rude_client.py#L1859) draws the line only if the target is the current channel and this client is the selected one. It builds `timestamp<symbol nick> text`, colors known nicknames, and calls `gui.insert_text_widget`. If the channel isn't the visible one, it falls to the highlight step.
- `pip_to_pop_out` builds the same line and calls `window.insert_text` on the pop-out window object stored in `gui.pop_out_windows`.
- [`highlight_channel_if_not_current`](../src/rudechat4/rude_client.py#L1899) marks the entry in the channel list. A mention (the nickname appears anywhere in the text, case-insensitive substring) gets the mention color, other traffic gets the activity color. `save_highlight` remembers the choice in `highlighted_channels` so it survives a redraw of the list. The code skips activity coloring when the entry is already `#ff0000`, which is the default mention color. A custom `mention_note_color` wouldn't be recognised there.

### 5. Direct messages

[`prepare_direct_message`](../src/rudechat4/rude_client.py#L1614) calls `log_message` first, then:

1. Ignores lines from your own nick (this matters for ZNC echo).
2. Makes sure a history list exists for the sender and adds the sender to `cap_who_for_chan` so the auto-WHO pass skips them.
3. If the sender isn't in `joined_channels`, adds a DM tab, adds the nick to `dm_list`, and saves the list (`save_dm_list`).
4. A sender starting with `*status` (ZNC) goes to `handle_znc_status_message` and returns.
5. Otherwise it follows the same three-way split as channels: ZNC playback (save and highlight), background DM (save and highlight), visible DM (save, then `display_message` with `is_direct=True`, or `pip_to_pop_out`).

For a DM, `display_message` takes its second branch: the line is drawn if the sender's name is the current tab. DM lines show the sender without a mode symbol.

### 6. Notifications

[`notify_user_if_mentioned`](../src/rudechat4/rude_client.py#L1525) runs after every non-CTCP `PRIVMSG`, DM or channel. It matches `\b<nickname>\b` (case-insensitive) against the text. Note this is stricter than the highlight test above, which is a plain substring check. On a match:

1. `notify_user_of_mention` ([line 1273](../src/rudechat4/rude_client.py#L1273)) colors the channel entry with the mention color (unless it's the current channel), colors the server entry if you're viewing a different server, and, if `use_beep_noise` is on, calls `trigger_beep_notification`.
2. `trigger_beep_notification` ([line 1350](../src/rudechat4/rude_client.py#L1350)) starts a thread that plays a sound: `afplay` on macOS, `paplay` or a terminal bell on Linux, `winsound.Beep` on Windows. The thread is kept in `ping_threads` and `thread_killer` reaps it. It then calls `gui.trigger_desktop_notification`.
3. [`trigger_desktop_notification`](../src/rudechat4/rude_gui.py#L689) shows a tray balloon, but only if `QApplication.activeWindow()` is `None`. The sound plays whether or not the window has focus.
4. In ZNC mode, a mention in a channel that is detached or unknown calls `auto_attach`, which adds the channel to the list and sends `NAMES` and `TOPIC`.
5. The line is appended to `mentions[target]`, which `/mentions` shows in the `!MENTIONS!` tab.

The mac and Linux sound helpers build a shell command with `os.system(f"afplay {sound_path}")`. The path comes from the install folder, not from network input. If the install path contains spaces, the command won't work. I haven't tested it.

Other notification-like events skip this path. A friend coming online calls `trigger_desktop_notification` from `prtcl_JOIN`.

### 7. Persistence

`channel_messages` is held in memory and written to `channel_messages_<server_name>.json` in the config folder by `auto_save` every 30 seconds ([`save_channel_messages`](../src/rudechat4/rude_client.py#L248), using a `.lock` file and merging with the file on disk). `auto_trim` cuts each channel to its last 800 entries every 125 seconds. The comment in `trim_messages` says 500, the code keeps 800. The saved strings include the ANSI sequences used for nick coloring. See [data-files.md](data-files.md) for the files.

## Text decode path into the chat view

Every line shown in the chat view goes through the same route, whether it's a chat message, a join notice, an error or a history redraw.

```
gui.insert_text_widget(str)                      one string
gui.display_last_messages(channel, num=800)      a list, oldest first
        |
        v
BatchDecoderWorker(messages, self.decoder, self.find_urls)      QRunnable
        |  signals.message_decoded.connect(handle_decoded_text)
        v
QThreadPool.globalInstance().start(worker)
        |
        |  worker thread
        |    for each message:
        |       formatted = decoder(message)       -> [(text, QTextCharFormat), ...]
        |       urls      = find_urls(message)     -> [str, ...]
        |       emit message_decoded(formatted, urls)
        |    emit finished
        v
main thread (queued signal)
   handle_decoded_text(formatted, urls)
        |-- tag_text(formatted)     insert each run at the end of the document
        |-- tag_urls(urls)          search the whole document for each URL, merge link format
        v
   insert_and_scroll()              scroll down if you were within 60 px of the bottom
```

### Where the work happens

- [`BatchDecoderWorker`](../src/rudechat4/rude_gui.py#L31) accepts a string (wrapped in a list) or a list of strings. `run` loops over them and emits one `message_decoded(list, list)` per message. A failure logs the error and skips that message.
- [`RudeGui.decoder`](../src/rudechat4/rude_gui.py#L1570) is a method on the GUI that the worker calls from its own thread. It walks the string one character at a time and keeps an attribute dict (bold, italic, underline, strikethrough, inverse, foreground, background). Each time an attribute changes it calls `flush()`, which makes a `QTextCharFormat` through `configure_tag_based_on_attributes` and appends `(text, format)` to the output. It handles:
  - IRC control codes: `\x02` bold, `\x1D` italic, `\x1F` underline, `\x1E` strikethrough, `\x16` inverse, `\x0F` reset, and `\x03` color with one or two digits for foreground and an optional `,` plus one or two digits for background.
  - ANSI SGR sequences (`ESC [ ... m`): reset, bold, italic, underline, strikethrough, inverse, basic 16 colors, 256 colors (`38;5;n`, `48;5;n`) and 24-bit color (`38;2;r;g;b`). The client uses 24-bit sequences for nickname colors (`ansi_color_nickname`).
- `find_urls` runs the compiled `url_pattern` regex on the raw string.
- `tag_text` and `tag_urls` run on the main thread. `tag_text` inserts at the end of the document through a fresh `QTextCursor`, so your selection and scroll position stay put. `tag_urls` calls `document().find(url)` in a loop, so it scans the whole document once per URL per message. In a long chat this gets slower.

### Rules and risks

- The worker thread only builds data (`QTextCharFormat` objects and strings). It never touches a widget. Keep it that way.
- `insert_text_widget` starts one worker per call. Two calls in quick succession may land on two pool threads, and the signals are queued in whichever order the workers finish. I haven't seen the code force ordering between workers, so two lines sent a few milliseconds apart could appear swapped. A history redraw uses one worker for the whole list, so its lines stay in order.
- `switch_channel` clears the chat view and then starts the history worker. A line drawn by `insert_text_widget` while that worker runs would interleave with history lines. The code doesn't guard against it.
- `tag_urls` only finds URLs by text match, so every identical string in the document gets the link format, not just the new one.

### Channel switch

`on_channel_click` ([line 1395](../src/rudechat4/rude_gui.py#L1395)) calls `switch_channel` ([line 1474](../src/rudechat4/rude_gui.py#L1474)), which clears the chat view, sets `irc_client.current_channel`, updates the topic and nick labels, and calls `display_last_messages(channel, server_name=...)`. That method slices the last 800 entries of `channel_messages[server][channel]` and runs them through the worker above. This is why `save_message` stores the already colored text: a redraw replays the same strings through the same decoder.

## Quick reference

| Step | Method | File |
| --- | --- | --- |
| Enter pressed | `bind_return_key`, `on_enter_key` | `rude_gui.py` |
| Slash or text split | `command_parser` | `rude_client.py` |
| Prepare chat text | `handle_user_input` | `rude_client.py` |
| Send per line | `send_message_chunks`, `send_message` | `rude_client.py` |
| Read and frame | `handle_incoming_message` | `rude_client.py` |
| Parse chat line | `prtcl_PRIVMSG` | `rude_client.py` |
| Store | `save_message`, `log_message`, `save_channel_messages` | `rude_client.py` |
| Show | `display_message`, `pip_to_pop_out`, `insert_text_widget` | both |
| Decode | `BatchDecoderWorker`, `decoder` | `rude_gui.py` |
| Notify | `notify_user_if_mentioned`, `trigger_beep_notification`, `trigger_desktop_notification` | both |
