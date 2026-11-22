# State and persistence

This page lists what `RudeChatClient` and `RudeGui` keep in memory, who changes it, who reads it, and what reaches the disk. It also lists every background task, how history is trimmed, and what happens when a server drops, a client reconnects or the app exits.

For the startup order and the Qt/asyncio bridge, see [architecture.md](architecture.md). For the files themselves, see [data-files.md](data-files.md). Slash commands are in [commands.md](commands.md). Terms are in [glossary.md](glossary.md). Bugs found while tracing this code are in [known-issues.md](known-issues.md).

Everything here comes from reading the source. Where a path was traced but not run, the text says so.

## Two names for one server

A client has two server identifiers, and different dictionaries use different ones.

| Attribute | Comes from | Used as the key for |
| --- | --- | --- |
| `server` | `server =` in the `.rudeserver` file (a hostname) | `channel_messages` (outer key) |
| `server_name` | `server_name =` in the `.rudeserver` file (a label) | `highlighted_channels`, `motd_dict`, GUI `clients`, `popped_out_channels`, `channel_topics`, `channel_lists`, and the file names `channel_messages_<server_name>.json`, `<server_name>_away_users.json`, `<server_name>_open_dms.txt` |

If `server_name` is empty, `init_client_with_config` falls back to `Server_1`, `Server_2` and so on for the GUI key, but the client's own `server_name` attribute stays `None`. See [known-issues.md](known-issues.md).

## RudeChatClient state

Attributes below are created in `RudeChatClient.__init__` ([`rude_client.py`](../src/rudechat4/rude_client.py)) unless the table says otherwise. "Saved" means written to a file in `~/.config/rudechat`.

### Wiring and runtime handles

| Attribute | Shape | Written by | Read by | Saved |
| --- | --- | --- | --- | --- |
| `master`, `entry_widget`, `server_text_widget`, `gui` | Qt objects passed to the constructor. Every client shares the same widgets. | `__init__`, `set_gui` | Everywhere that draws text | No |
| `loop` | The asyncio loop from `get_event_loop()` | `__init__` | `loop.create_task(...)` calls in the client and GUI | No |
| `time_zone` | `tzlocal` zone | `__init__` | CTCP `TIME` reply | No |
| `reader`, `writer` | asyncio stream pair, `None` until connected | `connect_to_server` | `handle_incoming_message`, `_await_welcome_message`, `send_message` | No. Nothing ever calls `writer.close()`. |
| `tasks` | `{task key: asyncio.Task}` | `RudeGui.init_client_with_config` and `create_tasks` | Nothing. `stop_async_loop` uses `asyncio.all_tasks` instead. | No |
| `client_event_loops` | `{client: loop}` | `RudeGui.init_client_with_config` | Nothing | No |
| `ping_threads` | `list[threading.Thread]` of notification sound threads | `trigger_beep_notification` | `wait_for_threads` (run by `thread_killer`) | No |
| `decoder`, `encoder` | `irctokens` stateful objects | `__init__` | Nothing found | No |
| `watcher` | `AutoAway` (created in `read_config`, replaced in `reload_config`; not in `__init__`) | `read_config`, `reload_config` | `handle_user_input`, `cmd_me`, `away_watcher` | No |

### Config values

`read_config` ([line 74](../src/rudechat4/rude_client.py#L74)) copies every key of the `[IRC]` section onto the client: `server`, `port`, `ssl_enabled`, `nickname`, `server_name`, the NickServ, SASL and ZNC settings, `ignore_cert`, `auto_join_channels` (a list), the notification colours and the on/off switches such as `use_logging`, `use_emojis`, `green_text` and `replace_pronouns`. None of these exist before `read_config` runs. It also loads history, away users, the ignore list and the DM list, so reading a config touches the disk.

`reload_config` runs after the server config window closes. It refreshes only the display and behaviour switches, the colours and `auto_join_channels`. It does not refresh `server`, `port`, `ssl_enabled`, `nickname`, any password, the SASL or ZNC settings, `ignore_cert`, `use_auto_join`, `auto_rejoin` or `auto_connect_to_networks`. Changing those needs a restart. It then calls `join_new_channels`.

### Connection and protocol flags

| Attribute | Meaning | Written by | Read by |
| --- | --- | --- | --- |
| `is_connected` | The GUI thinks this client is connected | `create_tasks` sets it before `connect()` runs. `disconnect` clears it. | `client_connect`, `join_channel`, `disconnect` |
| `disconnect_requested` | The user asked to disconnect | `disconnect` sets it. `client_connect` clears it. | `reconnect` |
| `loop_running` | Shared on/off switch for every background loop | `disconnect`, `spec_quit`, `tray_quit`, `/quit`, each task's `CancelledError` handler, `reconnect`, `client_connect` | Every `while self.loop_running` loop |
| `isupport_flag` | A `005` line was seen during registration | `_await_welcome_message` | The same function |
| `away_notify`, `extended_join`, `account_notify` | Capability acknowledged by the server | `prtcl_CAP`, `handle_znc_status_message` (clears all three when a `*status` message contains "disconnected") | `prtcl_JOIN`, `send_who`, `prtcl_CAP` |
| `who_for_chan_complete` | The first WHO sweep finished | `request_who_for_all_channels` | `the_worker` |
| `whois_gathering_complete` | The one-time WHOIS pass finished | `the_worker` | `away_updater` |
| `who_user_request`, `whois_user_request` | The user typed `/who` or `/whois`, so show the reply | `command_parser`, `get_direct_message_target`, GUI user list menu | `bprtcl_who_replies`, `bprtcl_whois_replies`, `whois_display` |
| `ping_start_time` | `time.time()` when a ping went out, or `None` | `keep_alive`, `ping_server`, `ping_user` | `prtcl_PONG` |

None of these are saved. `reset_state` leaves all of them alone.

### Server limits

Set by `prtcl_005` from the `ISUPPORT` line during registration. Each call first resets them to defaults, then applies the parameters on that one line.

| Attribute | Shape | Default |
| --- | --- | --- |
| `nicknamelen`, `chan_limit`, `channellen`, `topiclen` | `int` (all `0` in `__init__`) | 16, 250, 50, 390 |
| `chantypes` | `list[str]` of channel prefixes | `['#', '&']` |
| `chanmodes` | `{'list': [...], 'parameter': [...], 'setting': [...], 'no_parameter': [...]}`. Not in `__init__`. | Built-in lists: `list` is `e I b q`, `parameter` is `k`, `setting` is `f l j`, the rest go in `no_parameter` |
| `mode_to_symbol` | `{mode letter: symbol}` in `PREFIX` order, so the first entry is the highest rank | `{'o': '@', 'v': '+'}` |
| `mode_keys`, `mode_values` | The keys and values of `mode_to_symbol` as lists. `mode_values` is what the code strips from nicknames. | `[]` |

`reset_state` clears `mode_to_symbol` but not `mode_values`, so `mode_values` keeps the old symbols until the next `005` line.

### Channels, DMs and users

| Attribute | Shape | Written by | Read by | Saved |
| --- | --- | --- | --- | --- |
| `current_channel` | `str`, `''` or `None` when nothing is selected | `RudeGui.switch_channel`, `on_server_change` | Almost every display path | No |
| `joined_channels` | `list[str]` of joined channels, open DM nicknames and bang channels such as `!HELP!` | `join_channel`, `open_dm`, `prepare_direct_message`, `auto_attach`, `whois_display`, `display_help`, `cmd_mentions`, removal in `leave_channel`, `close_dm`, `remove_kicked_channel` | `update_gui_channel_list`, `join_channel` (counts against `chan_limit`), `request_who_for_all_channels` | No |
| `detached_channels` | `list[str]`, ZNC channels the user detached | `detach_channel` | `notify_user_if_mentioned`. Nothing removes an entry. | No |
| `dm_list` | `list[str]` of nicknames with an open DM | `open_dm`, `close_dm`, `prepare_direct_message`, `prtcl_NICK_dm_helper`, `load_dm_list` | `replace_dms_in_gui`, `prtcl_QUIT` | `<server_name>_open_dms.txt`, by `save_dm_list` on every change |
| `cap_who_for_chan` | `list[str]` of channels and DMs where WHO was already sent. The name is not explained in the code. | `request_who_for_all_channels`, `/join`, `/who`, `open_dm`, `load_dm_list`, info tabs | `request_who_for_all_channels`, `RudeGui.highlight_who_channels` (greyed text means "not yet queried") | No |
| `channel_users` | `{channel: list[str]}`. Entries carry a mode symbol prefix such as `@nick`. | `prtcl_353` (raw names), `sort_users` (rewrites with prefixes), `prtcl_JOIN`, `prtcl_PART`, `prtcl_QUIT`, `prtcl_KICK`, `prtcl_NICK`, `prtcl_MODE` | `update_gui_user_list`, `color_message_mentions`, `request_who_for_missing_users`, pop-out windows, `update_users_label` | No |
| `user_modes` | `{channel: {nickname: set[mode letter]}}` | `sort_users`, `prtcl_MODE`, `prtcl_PART`, `prtcl_QUIT`, `leave_channel` | `get_user_mode`, `sort_users` | No |

### History

| Attribute | Shape | Written by | Read by | Saved |
| --- | --- | --- | --- | --- |
| `channel_messages` | `{server: {channel or nickname or bang channel: list[str]}}`. Each string is one finished display line ending in `\n`, with IRC control codes and 24-bit ANSI colour for nicknames already embedded. | `save_message`, `_log_channel_message`, `append_to_channel_history`, `user_input_*`, `query_msg_handler`, every `prtcl_*` join/part/quit/kick/nick/topic handler, `display_help`, `whois_display`, `cmd_mentions`, `load_channel_messages`; emptied for one channel by `RudeGui.clear_chat_window` | `RudeGui.display_last_messages` (last 800 lines), `RudePopout.load_channel_messages` (last 150), `save_channel_messages`, `trim_messages` | `channel_messages_<server_name>.json`. See below. |

`save_channel_messages` reads the existing file, replaces the top-level key for this client's `server` with the in-memory copy, and writes the result with `indent=2`. It guards the file with `channel_messages_<server_name>.lock`, which it polls every 0.1 s if the lock exists. Every new `RudeChatClient` deletes all `*.lock` files in the config folder when it starts.

Saves happen:

- every 30 s in `auto_save` while `loop_running` is true,
- in `tray_quit` and the `/quit` command, for the current client only,
- in `Window.on_app_exit` for every client, but only as a scheduled task. Whether that task runs before the process ends was not verified. See [known-issues.md](known-issues.md).

`disconnect` does not save.

Bang channels (`!HELP!`, `!WHOIS!`, `!MENTIONS!`) live in `channel_messages` like any other channel. `remove_bang_channels` deletes every key that starts with `!` on `spec_quit`, `tray_quit` and `/quit`, but not on the `on_app_exit` path, so those tabs can be saved to disk and loaded again on the next start.

### Away, WHO and WHOIS

| Attribute | Shape | Written by | Read by | Saved |
| --- | --- | --- | --- | --- |
| `away_users_dict` | `{nickname: away message}`. An empty string means "away, message unknown yet". | `prtcl_AWAY`, `_who_reply_data_handler` (WHO flag `G`), `bprtcl_whois_replies` (301), `send_away_notification`, `away_watcher`, `remove_away_status`, `prtcl_401`, `prtcl_QUIT`, `load_away_users_from_file` | `RudeGui.highlight_away_users`, `whois_worker`, `update_away_status`, `_away_user_helper` | `<server_name>_away_users.json`, by `away_watcher` every 120 s (250 s when `use_auto_away` is off). Loaded in `read_config`. Your own nickname is removed on load. |
| `away_servers` | `list[str]` of `server_name` values where you are away | `send_away_notification`, `away_watcher`, `remove_away_status` | `RudeGui.update_users_label` | No |
| `away_notified` | `set[str]` of nicknames already announced as away | `_away_user_helper` | The same function | No. `the_cleaner` empties it every 1200 s. |
| `who_user_data` | `{nickname: dict}` with keys `nickname`, `username`, `host`, `server`, `channel`, `status`, `mode`, `who_message`, `shared-channels`, and `account` when the reply carried it | The nested `update_user_data` in `bprtcl_who_replies`, `prtcl_AWAY`, `update_away_status` | `ignore_user_from_gui`, `unignore_user_from_gui`, `RudeGui.open_user_info`, the user list menu | No. `reset_state` does not clear it. |
| `who_details` | `list[dict]`. Not in `__init__`; created on the first WHO reply with `hasattr`. | `bprtcl_who_replies` | The `315` branch of the same function, which empties it | No |
| `whois_data` | `{nickname: dict}` using keys such as `Username`, `Hostname`, `Realname`, `Server`, `Channels`, `Away`, `Logged In As` | `bprtcl_whois_replies` | `whois_display`, `save_whois_to_file` | The text goes to `whois/whois_<nickname>.txt`. The dict is cleared once by `the_worker` and by `reset_state`. |
| `whois_executed` | `set[str]` of nicknames already sent a WHOIS from the DM path | `get_direct_message_target`, `get_away_user_whois` | The same two functions | No. `reset_state` clears it. |
| `account_cache` | `{nickname: account}` | `prtcl_ACCOUNT`, `prtcl_JOIN` (with `extended-join`), `bprtcl_who_replies` (WHOX) | Only the membership checks in `prtcl_ACCOUNT`. No other reader found. | No |
| `motd_dict` | `{server_name: str}`, the text of the "server" view | `add_server_message` (every server notice appends), `prtcl_376` | `display_server_motd` | No. `reset_state` clears it. Nothing trims it while connected. |
| `motd_lines` | `list[str]` while an MOTD arrives | `prtcl_372`, `prtcl_375` | `prtcl_376` | No |

### Highlights and mentions

| Attribute | Shape | Written by | Read by | Saved |
| --- | --- | --- | --- | --- |
| `highlighted_channels` | `{server_name: {channel: {'index': int, 'bg': colour string}}}` | `save_highlight`, `restore_channel_bg_colors`. Entries are removed by `detach_channel`, `leave_channel`, `close_dm`, `remove_kicked_channel` and `RudeGui.on_channel_click`. | `restore_channel_bg_colors`, which runs after every `update_gui_channel_list` | No |
| `mentions` | `{target: list[str]}`. Each string is `[time] <sender> text`. | `notify_user_if_mentioned` | `cmd_mentions`, the `/mentions` command | No. `/mentions clear` empties it. |

### Ignore list, friends, macros

| Attribute | Shape | Written by | Read by | Saved |
| --- | --- | --- | --- | --- |
| `ignore_list` | `list[str]`. Entries are `*!user@host` masks from the GUI menu, or whatever text you typed after `/ignore`. | `ignore_user`, `unignore_user`, `ignore_user_from_gui`, `unignore_user_from_gui`, `load_ignore_list` | `should_ignore_sender`, which matches with `fnmatch` against `nick!user@host` | `ignore_list.txt`. One file for all servers, rewritten in full on every change. |
| `friends` | `RudeFriends` with `friend_list` (`list[str]`) and `online_friends` (`list[str]`) | `/watch`, `prtcl_JOIN`, `prtcl_QUIT` | `prtcl_JOIN`, `prtcl_ACCOUNT` | `friend_list.txt`, shared by all servers, rewritten in full on every change. `online_friends` is memory only. |
| `ASCII_ART_MACROS` | `{file name without .txt: text}` | `load_ascii_art_macros`, `update_available_macros` | `cmd_mac`, `handle_pop_out_mac_command` | No. Reloaded from `Resources/Macros`. |
| `config` | Path of the `.rudeserver` file (`''` until `read_config` finishes) | `read_config` | `AutoAway` | No |

Each client holds its own copy of `ignore_list` and its own `RudeFriends`, loaded once at startup. Two servers editing the shared files overwrite each other's later changes. See [known-issues.md](known-issues.md).

### Attributes created outside `__init__`

`chanmodes`, `who_details`, `watcher`, `current_server` (set by `RudeGui.on_server_change`, never read), and every config value from `read_config`. Code that touches them before the first `005` line or before `read_config` can raise `AttributeError`. Most callers catch that and log it.

## RudeGui state

`RudeGui` ([`rude_gui.py`](../src/rudechat4/rude_gui.py)) builds its state in this order: `__init__`, `read_config`, `init_layout`, `set_misc_variables`, `set_gui_theme`, `init_client`.

### Settings from `gui_config.ini`

`read_config` fills about 30 plain attributes (`window_bg`, `chat_font_size`, `list_user_away_fg`, `url_color` and so on). It runs at startup and again after the GUI config window closes (`open_gui_config_window`). Nothing in `RudeGui` writes the file; `RudeConfigGui` does. Missing keys fall back to defaults in the code. The flags are:

| Attribute | Config key | Effect |
| --- | --- | --- |
| `minimize_to_tray` | `[Utility] minimize_to_tray` | Closing the window hides it instead of quitting |
| `log_on` | `[Utility] turn_logging_on` | GUI-side debug logging. The client has its own `log_on` from `[IRC] log_on`. |
| `generate_nickname_colors` | `[Utility] generate_nickname_colors` | Random colour per new nickname, or plain foreground |
| `main_nickname_color`, `tab_complete_terminator`, `scrollbar_bg`, `url_color` | `[Utility]` | Colour and tab-completion settings |

### Attributes from `set_misc_variables`

| Attribute | Shape | Written by | Read by | Saved |
| --- | --- | --- | --- | --- |
| `channel_lists` | `{server_name: list}`, the same list object as the client's `joined_channels` at assignment time | `add_client` and many client methods | Nothing. Write only. | No |
| `nickname_colors` | `{nickname: '#rrggbb'}` | `load_nickname_colors`, `reset_nick_colors`, `update_nickname_colors`, `prtcl_353` | `ansi_color_nickname`, `RudeColours` window | `nickname_colours.json` and `nickname_colours_bak.json`. See below. |
| `clients` | `{server_name: RudeChatClient}` | `add_client` | `on_server_change`, `client_connect`, quit and away fan-out, `Window.on_app_exit` | No |
| `channel_topics` | `{server_name: {channel: topic}}` | `bprtcl_topic`, `display_help` | `switch_channel`, `RudePopout.set_topic` | No |
| `url_cache` | `{}` | Nothing | Nothing | No |
| `tag_cache` | `{"url_<url>": QTextCharFormat}` | `tag_urls` | Nothing in `RudeGui`. The pop-out keeps its own and reads it. | No. Grows by one entry per distinct URL. |
| `entry_history` | `list[str]`, last 10 inputs | `on_enter_key` | `show_previous_entry`, `show_next_entry` | No |
| `history_index` | `int` position in `entry_history` | `on_enter_key`, arrow keys | Same | No |
| `popped_out_channels` | `{server_name: list[str]}` of channels shown in a pop-out window and hidden from the main list | `inform_gui`, `append_to_pop_out_dict`, `remove_from_pop_out_dict` | 40 or so checks in the client and GUI, mostly "display here or in the pop-out" | No |
| `pop_out_windows` | `{channel or nickname: [QWidget, RudePopout]}`. Not keyed by server. | `open_pop_out_window`, `remove_from_pop_out_dict` | `pip_to_pop_out`, `pipe_mode_to_pop_out`, `update_user_selector_list`, `handle_action_ctcp` | No |
| `server_colors` | `{combo box index: {'fg': colour, 'bg': colour}}` | `on_server_change`, `highlight_server` | `on_server_change` | No |
| `download_channel_list` | `{channel: {'user_count', 'topic'}}`, shared by all servers | `prtcl_322`, cleared in `reset_state` | `ChannelListWindow`, `prtcl_323` | `channel_list.txt`, rewritten at the end of each `/list` |
| `last_selected_index`, `target_user_info`, `emoji_width_cache` | `None` or `{}` | Nothing | Nothing | No |
| `previous_server_index` | `int` or `None` | `on_server_change` | `on_server_change` | No |
| `iconed` | `bool`, window is hidden in the tray | `send_to_tray`, `restore_from_tray` | Nothing outside those two | No |
| `url_pattern` | Compiled regex | `set_misc_variables` | `find_urls` | No |
| `rude_shutdown` | `RudeShutdown` window | `set_misc_variables`, replaced in `client_shutdown` | `destroy_client` | No |

`irc_colors` (a fixed table of IRC colour numbers `00` to `98`) is set in `__init__` and duplicated in `RudePopout`.

### Attributes created elsewhere

| Attribute | What it is |
| --- | --- |
| `irc_client` | The current client. `init_client` first creates a stray client with no server config. `on_server_change` replaces it with `clients[selected server]`. Code compares `self.gui.irc_client == self` to ask "is this the server on screen?". |
| `server_var` | Last added server name. Written by `add_client` and `initialize_clients`, never read. |
| `channel_window` | `ChannelListWindow`, created by `show_channel_list_window` for `/list`. The `322` handler uses it inside a `try`. |
| `tray_icon`, `tab_filter`, `arrow_key_filter` | Qt helpers created in `init_layout`. |
| `main_window`, `color_selector`, `user_info_window`, `user_info_ui` | The most recent config, colour or user-info window. Overwritten on each open. |

### Nickname colours on disk

`load_nickname_colors` runs at startup and on `reset_nick_colors`. `save_nickname_colors` writes the whole JSON file. It is called for each new nickname the client sees (`update_nickname_colors` on JOIN and NICK, and once per unknown user inside `prtcl_353`), so a join to a busy channel with many new names writes the file many times on the GUI thread. `save_nickname_colors_bak` and `update_bak_file` maintain the backup copy the same way. When `generate_nickname_colors` is off, the loader returns every nickname with `window_fg` and the file is not rewritten from that path.

### Pop-out window state

`RudePopout` ([`GUI/rude_popout.py`](../src/rudechat4/GUI/rude_popout.py)) keeps `parentGui`, `channel`, `form`, its own `tag_cache`, `entry_history` (10 lines) and `history_index`. It reads `channel_messages` (last 150 lines) when it opens and then receives new lines from client calls such as `pip_to_pop_out`. It saves nothing on its own.

## Background tasks

`RudeGui.create_tasks` ([`rude_gui.py`](../src/rudechat4/rude_gui.py#L781)) starts these for a client. It runs once at startup when `auto_connect_to_networks` is on, and again from `client_connect` for `/connect` and the server list menu. It first awaits `connect()`, so the tasks start only after the welcome sequence ends. If `auto_connect_to_networks` is off, the client is created and configured but no tasks run.

All loops share `loop_running`. Each loop's `CancelledError` handler sets `loop_running = False`, so cancelling one task makes its siblings stop at their next check.

| `tasks` key | Coroutine | What it does | Interval | Stops when |
| --- | --- | --- | --- | --- |
| `keep_alive` | `keep_alive` | Sets `ping_start_time`, sleeps, then sends `PING <server>` | 60 s | `loop_running` is false, or cancelled |
| `auto_save` | `auto_save` | `save_channel_messages` | 30 s | Same |
| `auto_trim` | `auto_trim` | `trim_messages` | 125 s | Same |
| `handle_incoming_message` | `handle_incoming_message` | Reads the socket, splits lines, dispatches by IRC command. Calls `reconnect` on EOF, `OSError` or a 256 s read timeout. | Continuous | `loop_running` is false after a read returns, or cancelled |
| `auto_who` | `request_who_for_all_channels` | After 4 s, sends WHO for each channel not in `cap_who_for_chan`, 14 s apart, then sets `who_for_chan_complete` | One pass | Finishes on its own. `join_new_channels` starts more copies without keeping a reference. |
| `auto_away` | `away_watcher` | Marks you away after `auto_away_minutes` idle, and saves `away_users_dict` | 120 s (250 s when `use_auto_away` is off) | `loop_running` is false |
| `auto_clean` | `the_cleaner` | Clears `away_notified` | 1200 s | Same |
| `away_update` | `away_updater` | Copies away text into `who_user_data` through `update_away_status` once `whois_gathering_complete` is true | 300 s, or polls every 60 s before that | Same |
| `el_worker` (task name `la_worker`) | `the_worker` | Waits for `who_for_chan_complete`, runs `whois_worker` once, clears `whois_data`, sets `whois_gathering_complete`, ends | Polls every 60 s | Finishes on its own. It does not run again after a reconnect. |
| `who_missing_users` | `request_who_for_missing_users` | Sends WHO for users missing from `who_user_data`, 10 s apart | 600 s | `loop_running` is false |
| `thread_killer` | `thread_killer` | Calls `wait_for_threads` to join finished sound threads | 90 s | `loop_running` is false |
| `load_ascii_art_macros` | `load_ascii_art_macros` | Reads `Resources/Macros/*.txt` into `ASCII_ART_MACROS` | Once, at client creation | Finishes on its own |

`whois_worker` is not a task of its own. It sends `WHOIS` for each away user with an empty message, 5 s apart, and only when `auto_whois` is on.

### Tasks nobody tracks

Several `create_task` calls keep no reference, so they appear in no dictionary: the Enter key handler (`on_enter_key`, one per keypress), `handle_upload`, `away_client_task`, `quit_client_task`, `tray_quit`, `save_dm_list`, `update_available_macros`, `connect_to_specific_server`, `leave_channel` from the channel menu, and the context-menu actions in the user list and server list. asyncio keeps only weak references to tasks, so a task with no other reference can be collected before it finishes. None of these were observed failing. `stop_async_loop` spares tasks named `on_enter_key` and `quit_client_task` and cancels the rest.

### Timers and threads outside asyncio

| Item | Where | What it does |
| --- | --- | --- |
| `qt_update` | [`__main__.py`](../src/rudechat4/__main__.py#L123) | Every 100 ms: `loop.stop()`, `loop.run_forever()`, reschedule. This is the only thing that runs asyncio. |
| `BatchDecoderWorker` | `QThreadPool` in [`rude_gui.py`](../src/rudechat4/rude_gui.py#L31) | One per `insert_text_widget` call and per channel switch. Decodes text off the main thread and emits a signal back. |
| Sound threads | `trigger_beep_notification` | One `threading.Thread` per mention with sound on. Tracked in `ping_threads`. |
| `QTimer.singleShot` | `bind_return_key`, config window close, `destroy_client`, `on_channel_click` | Short delays only |

## History limits and trimming

| What | Limit | Where |
| --- | --- | --- |
| In-memory lines per channel, DM or bang channel | 800, enforced by `trim_messages` every 125 s. The comment in the code says 500. | `trim_messages` |
| Lines drawn when you switch to a channel | Last 800 | `RudeGui.display_last_messages` (`num=800`) |
| Lines drawn in a pop-out window | Last 150 | `RudePopout.load_channel_messages` |
| Input history | Last 10 lines, in `RudeGui` and in each pop-out | `on_enter_key`, `save_entry_history` |
| Outgoing line length | 420 characters per chunk, 0.7 s between chunks | `handle_user_input`, `send_message_chunks` |
| Saved history file | Whatever is in memory at the next save. Trimming shrinks the file only after the next `auto_save`. | `save_channel_messages` |
| Text logs in `Logs/` | None. Files grow without a limit. | `log_message` |
| `RudeChat4.log` | None. A plain `FileHandler` at DEBUG level, no rotation. | `configure_logging` |
| `motd_dict`, `who_user_data`, `account_cache`, `mentions`, `tag_cache`, `nickname_colors` | None. They grow until restart (or until `/mentions clear`, or `reset_state` for `motd_dict`). | Various |

A freshly loaded history file is not trimmed until the first `auto_trim` tick, 125 s after startup, so a large file is held in full until then.

## Disconnect, reconnect and exit

### `reset_state`

`reset_state` ([line 853](../src/rudechat4/rude_client.py#L853)) clears `motd_dict`, `joined_channels`, `motd_lines`, `channel_users`, `user_modes`, `mode_to_symbol`, `whois_data`, `whois_executed` and the GUI's shared `download_channel_list`. It leaves everything else, including `channel_messages`, `dm_list`, `detached_channels`, `cap_who_for_chan`, `who_user_data`, `away_users_dict`, `highlighted_channels`, `mentions`, `account_cache`, the capability flags and the `*_complete` flags.

### Connection drops

1. `handle_incoming_message` sees EOF, an `OSError` or a 256 s read timeout. It sends `QUIT` and awaits `reconnect(config_file)`.
2. `reconnect` returns at once if `disconnect_requested` is set. Otherwise it writes notices to the server view, calls `reset_state`, and tries up to 5 times. Each attempt waits 15 s first (5 s for ZNC), then runs `connect`, which opens the socket, registers and waits for the welcome sequence.
3. On success it calls `replace_dms_in_gui`, sets `loop_running = True` and reselects the first server in the list.
4. Channels return through `automatic_join`, which uses `auto_join_channels` only. A channel you joined by hand is not rejoined, except that ZNC replays its own.
5. The background tasks are not recreated. They kept running through the drop. The WHO sweep and `the_worker` already finished, so they do not run again. This path was traced, not run.
6. After 5 failures `reconnect` returns. The read loop then reads from the old reader, gets no data, and starts another reconnect round.

The old `writer` is replaced, never closed.

### You disconnect

`/disconnect <server>` or the server list menu calls `disconnect(server_name)` on the current client. For the target client it sends `QUIT`, sets `loop_running = False`, `is_connected = False` and `disconnect_requested = True`, and clears the ping label. It then calls `reset_state()` on the client that received the command, which may be a different client. It does not cancel tasks, close the socket or save history. Each loop exits the next time it wakes.

`/connect <server>` goes through `client_connect`. It calls `create_tasks` again, which overwrites the `tasks` entries, then clears `disconnect_requested` and sets `loop_running = True`. The old tasks may still be asleep from before. If one wakes after the flag is true again, it keeps looping, so a quick disconnect and connect can leave two copies of a loop running. This was traced, not run.

### Exit

| Path | What it does |
| --- | --- |
| Close the window, `minimize_to_tray` on (the default) | `Window.closeEvent` ignores the close and calls `send_to_tray`. Nothing is saved or stopped. |
| Tray menu Quit | `quit_from_tray` restores the window and runs `tray_quit`: sets `minimize_to_tray = False`, removes bang channels, saves history for the current client only, sends `QUIT :Client Quit` for every client, sets `loop_running = False`, then calls `client_shutdown`. |
| `/quit [message]` | Same as the tray path, plus `stop_async_loop`, which cancels every task in the loop except `on_enter_key` and `quit_client_task`. |
| `client_shutdown` | Shows the goodbye window, runs `quit_clients` (each client's `spec_quit`: remove bang channels, send `QUIT :RudeChat4`, set `loop_running = False`, `stop_async_loop`), then 2 s later `destroy_client` closes the main window. Each client therefore sends two `QUIT` lines on the tray and `/quit` paths. |
| Close the window, `minimize_to_tray` off | `closeEvent` calls `on_app_exit`, which schedules `save_channel_messages` for every client with `create_task` and accepts the close. It sends no `QUIT`, does not remove bang channels and does not stop tasks. |
| Signal or kill | No handler exists in the code. |

On the `/quit` and tray paths `on_app_exit` also runs, from `destroy_client`, so each client gets a second scheduled save after the loops have been cancelled.

`stop_async_loop` cancels every task in the shared loop, not only this client's tasks. With several servers connected, the first client to quit cancels the others' tasks too.

## Sensitive data

The state above holds IRC nicknames, hostmasks (`user@host`, which can carry an IP address or hostname), account names, message text, away messages and WHOIS results. `.rudeserver` files hold NickServ, SASL and ZNC passwords in plain text. Rules that likely apply if the data is shared or collected: GDPR and general PII handling for hostmasks and message content, and SOC 2 expectations for credentials at rest. FERPA and COPPA would apply only if the client is used for student or child chat, which the code does not indicate. Before sharing logs, history files or screenshots, redact them or use synthetic data. Security and Privacy review is worth considering for the plain-text credentials and for the upload command described in [known-issues.md](known-issues.md). See also the "Sensitive data" section of [data-files.md](data-files.md).

Files the client writes that [data-files.md](data-files.md) does not list: `<server_name>_open_dms.txt`, `filtered_channels.txt` (read by the pronoun filter; the client never creates it), and `channel_messages_<server_name>.lock`.
