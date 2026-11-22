# Architecture

## The big pieces

```
__main__.py            Qt app, main window, event loop bridge
  └─ rude_gui.RudeGui   The main widget: layout, lists, chat view, input box
       ├─ Components/   Small Qt widget subclasses used by RudeGui
       ├─ GUI/          Dialogs and secondary windows (config, colours, pop-outs)
       └─ one rude_client.RudeChatClient per server
            ├─ Client/  Helpers: auto away, friends list, pronouns, mock text
            └─ Util/    Config copy, logging setup, nickname validation
```

`RudeGui` owns the windows and widgets. Each `RudeChatClient` owns one IRC connection, and holds that server's channels, users, history and settings. The client calls back into the GUI (`self.gui`) to draw text and update lists, so the two classes depend on each other.

## Startup sequence

`__main__.__main__()` in [`__main__.py`](../src/rudechat4/__main__.py) runs these steps in order:

1. `CopyConfigs()` copies the files in `DefaultConfig/` into `~/.config/rudechat` when that folder is empty.
2. A `QApplication` is created and named.
3. `FirstRun` checks `first_run.txt`. If the setup hasn't been done, it opens the server config window.
4. A new asyncio event loop is created and set as current. Python 3.14 no longer creates one implicitly.
5. `Window` (a `QMainWindow`) and `RudeGui` are built, and the GUI becomes the central widget.
6. `initialize_clients(gui)` is scheduled on the loop. It finds every `*.rudeserver` file in the config folder, sorted by name, and calls `gui.init_client_with_config()` for each one. A failure on one server is logged and the next server still connects.
7. The Qt event loop starts with `app.exec()`.

## Qt and asyncio on one thread

Qt wants to own the main thread, and the IRC code is `async`. RudeChat avoids a second thread with a timer. `qt_update()` fires every 100 ms, calls `loop.stop()` then `loop.run_forever()` so asyncio runs any ready tasks, then stops again and reschedules itself with `QTimer.singleShot`.

What this means in practice:

- Async work only progresses while the Qt loop is idle and the timer fires, so a long blocking call inside a coroutine freezes the GUI.
- GUI code starts async work with `loop.create_task(...)`. The input box does this in `RudeGui.bind_return_key`.
- Input and timing latency is bounded by the 100 ms tick.

## The IRC client

`RudeChatClient` in [`rude_client.py`](../src/rudechat4/rude_client.py) is the largest file in the project. Its main areas are:

- **Connection:** `connect`, `connect_to_server`, `reconnect`, `disconnect`, `keep_alive`. It reads the server's `.rudeserver` file with `read_config`.
- **Receive loop:** `handle_incoming_message` reads lines, decodes them with `irctokens`, and dispatches by IRC command (PRIVMSG, JOIN, MODE, numerics and so on).
- **Send path:** `handle_user_input` takes what the user typed. Lines starting with `/` go to `command_parser`. Everything else is split into chunks and sent as a message to the current channel or DM.
- **Channels, users and DMs:** `joined_channels`, `channel_users`, `dm_list`, `detached_channels`, plus the `update_gui_*` methods that push state to the GUI.
- **Display:** `display_message`, `format_message`, `ansi_color_nickname` and `green_texter` prepare text for the chat view.
- **Background tasks:** `auto_save`, `auto_trim`, `the_worker`, `away_watcher`, `whois_worker` and similar coroutines run for the life of the connection and are tracked in `self.tasks`.
- **Fun and utilities:** `cowsay`, `fortune_cowsay`, ASCII art macros, ignore list handling.

IRC capabilities the client tracks include `away-notify`, `extended-join` and `account-notify`. Server limits (`NICKLEN`, `CHANLIMIT`, `CHANNELLEN`, `TOPICLEN`, `PREFIX`, `CHANTYPES`, `CHANMODES`) are read from the ISUPPORT reply and stored on the client.

## The GUI

`RudeGui` in [`rude_gui.py`](../src/rudechat4/rude_gui.py) builds the main window: server list, channel list, user list, topic label, chat view and input box. It also:

- reads `gui_config.ini` for fonts and colours,
- keeps a dictionary of clients (`self.clients`, keyed by server name) and switches between them when you pick a server,
- handles tab completion and arrow-key history through event filters,
- stores per-nickname colours in `nickname_colours.json`,
- shows a tray icon and hides to the tray when `minimize_to_tray` is on.

Pop-out windows for channels and DMs live in [`GUI/rude_popout.py`](../src/rudechat4/GUI/rude_popout.py).

## Shared imports and globals

Most modules start with `from rudechat4.shared_imports import *` and `from rudechat4.global_variables import *`. `shared_imports.py` pulls in the standard library and PyQt6 names used across the project. `global_variables.py` defines paths (`G_SOURCE_DIR`, `G_CONFIG_DIR`) and colour tables for IRC and ANSI rendering. Because of the star imports, a name used in one module often comes from one of these two files.

## Cleanup on exit

Closing the window with `minimize_to_tray` off calls `Window.on_app_exit`, which schedules `save_channel_messages()` on every client so history is written to disk. With `minimize_to_tray` on, closing hides the window instead.

## Things worth knowing

- `build/lib/` holds a stale copy of the source from a past build. Edit `src/`, not `build/`.
- `__main__.py` sets the app version to `4.1.2` while `pyproject.toml` says `4.2.0`. One of them is out of date.
- Some class names repeat across files (`RudeUserListWidget` in `Components/` and `GUI/rude_popout.py`, and `TabEventFilter` and `ArrowKeyEventFilter` in both `rude_gui.py` and `GUI/rude_popout.py`). Check the import path when reading code.
