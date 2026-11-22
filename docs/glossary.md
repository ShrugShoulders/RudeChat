# Glossary

Terms as the RudeChat code uses them. Paths are relative to `src/rudechat4`. For where each piece sits in the app, see [architecture.md](architecture.md) and [modules.md](modules.md). For what each term does to memory and disk, see [state-and-persistence.md](state-and-persistence.md).

## Channels, windows and conversations

| Term | Meaning | Where it lives |
| --- | --- | --- |
| Detach | A ZNC feature. `/detach #chan` sends a raw `detach #chan` line to the server and moves the channel from `joined_channels` to `detached_channels`. It only works when `znc_connection` is on. Nothing ever removes a channel from `detached_channels`. A plain `/join` is the way back. | `rude_client.py`: `command_parser` (case `detach`), `detach_channel`, `notify_user_if_mentioned` |
| Pop out | Showing a channel or DM in its own window instead of the main chat view. The name goes into `popped_out_channels[server_name]`, which hides it from the channel list. `/sw <channel>` or closing the window brings it back ("pop in"). Windows are keyed by channel name only, not by server. | `rude_gui.py`: `open_pop_out_window`, `append_to_pop_out_dict`, `remove_from_pop_out_dict`, `pop_out_return`. `GUI/rude_popout.py`: `RudePopout`, `pop_in_window`. `rude_client.py`: `update_gui_channel_list` |
| `pip_to_pop_out`, `pipe_mode_to_pop_out` | Client methods that send a finished line to a pop-out window. "pip" and "pipe" are the same idea, spelled both ways. | `rude_client.py` |
| DM vs query | "Query" is the IRC word and the `/query` command. "DM" is the app's word for the open conversation. A DM is a nickname stored in `joined_channels` (so it shows in the channel list) and in `dm_list` (so it survives a restart). Its history sits under that nickname in `channel_messages`. A line counts as a DM when its target is your own nickname. `/msg` opens a DM too. `/cq` closes one. | `rude_client.py`: `cmd_query`, `open_dm`, `close_dm`, `cmd_cq`, `is_direct_message`, `prepare_direct_message`, `load_dm_list`, `save_dm_list`. File `<server_name>_open_dms.txt` |
| Bang channels | Local tabs whose names start with `!`: `!HELP!`, `!WHOIS!`, `!MENTIONS!`. They exist only in the client and have no IRC channel behind them. The channel list menu calls them "info" and offers "Close Info". `remove_bang_channels` deletes every history key that starts with `!` when you quit through the tray, `/quit` or `spec_quit`. | `rude_client.py`: `display_help`, `whois_display`, `cmd_mentions`, `remove_bang_channels`. `Components/rude_channel_list_widget.py` |
| `remove_help_info` | Deletes the `!HELP!` history from every server's `channel_messages`. `display_help` calls it first, then rebuilds the text only if the `!HELP!` tab is not already open. | `rude_client.py` |
| Server view, MOTD text | The text shown when you pick a server and no channel. It comes from `motd_dict[server_name]`, which collects the MOTD plus every server notice for that connection. | `rude_client.py`: `add_server_message`, `display_server_motd`, `prtcl_376` |
| `server` vs `server_name` | `server` is the hostname from the config. `server_name` is the label. Different dictionaries use different ones. See [state-and-persistence.md](state-and-persistence.md#two-names-for-one-server). | `rude_client.py`: `read_config` |

## Users and status

| Term | Meaning | Where it lives |
| --- | --- | --- |
| Mentions | Two checks use the word. `notify_user_if_mentioned` matches your nickname as a whole word, ignoring case, then records the line in `mentions[target]`, highlights the channel and may beep. `is_it_a_mention` is a looser substring test used when choosing a highlight colour. `/mentions` copies the stored lines into the `!MENTIONS!` tab. | `rude_client.py`: `notify_user_if_mentioned`, `notify_user_of_mention`, `is_it_a_mention`, `cmd_mentions`, `highlight_channel`, `save_highlight` |
| Highlight, activity vs mention colour | Channel and server list rows change background when something happens off screen. `activity_note_color` (green by default) means new messages. `mention_note_color` (red) means someone said your name. Both come from the `.rudeserver` file. | `rude_client.py`: `highlight_channel_if_not_current`, `highlight_server`. `rude_gui.py`: `highlight_who_channels`, `on_channel_click` |
| Away users | Users the client knows are away. `away_users_dict` maps nickname to away text (empty means "away, text not fetched yet"). Names in the user list are drawn in `list_user_away_fg`. It fills from the `away-notify` capability, WHO flag `G`, WHOIS reply 301 and your own `/away`. It is saved per server. | `rude_client.py`: `prtcl_AWAY`, `_who_reply_data_handler`, `away_watcher`, `away_updater`, `save_away_users_to_file`. `rude_gui.py`: `highlight_away_users` |
| Auto away | Marks you away after `auto_away_minutes` without typing a plain message or `/me`. `AutoAway` keeps the clock. `away_watcher` checks it. | `Client/rude_auto_away.py`, `rude_client.py`: `away_watcher`, `handle_user_input` |
| `cap_who_for_chan` | List of channels and DMs where a WHO was already sent. Entries not in it are drawn in `list_channel_needwho_fg` (grey). The name is not explained in the code. | `rude_client.py`, `rude_gui.py`: `highlight_who_channels` |
| WHO, WHOIS, auto whois | WHO fills `who_user_data` (host, server, channels, away flag). WHOIS fills `whois_data` and the `!WHOIS!` tab. With `auto_whois` on, the client sends WHOIS for new DM senders and for away users whose message is unknown. | `rude_client.py`: `bprtcl_who_replies`, `bprtcl_whois_replies`, `get_direct_message_target`, `whois_worker`, `save_whois_to_file` |
| Watch, friends | `/watch +nick` adds a nickname to `friend_list.txt`. When a watched nickname joins a channel the client prints "is Online!" and may show a desktop notification. Account login and logout of friends are also announced. `online_friends` tracks who is currently seen. | `Client/rude_friends.py`: `RudeFriends`. `rude_client.py`: `cmd_watch`, `prtcl_JOIN`, `prtcl_ACCOUNT`, `prtcl_QUIT` |
| Ignore list | Patterns for senders to drop. Only PRIVMSG (and so ACTION) lines are checked, with `fnmatch` against `nick!user@host`. The GUI menu stores `*!user@host`. `/ignore bob` stores the bare text `bob`, which does not match a full hostmask unless you add wildcards. One file, `ignore_list.txt`, shared by all servers. | `rude_client.py`: `ignore_user`, `ignore_user_from_gui`, `should_ignore_sender`, `save_ignore_list`, `load_ignore_list` |
| Hostmask | `nick!user@host`. Used for ignore patterns, join and quit messages (when `show_hostmask` is on) and the WHOIS "suggested ignore mask". | `rude_client.py`, irctokens `tokens.hostmask` |
| Account cache | `{nickname: account}` from `account-notify`, `extended-join` and WHOX replies. | `rude_client.py`: `cache_accountname`, `prtcl_ACCOUNT` |
| Capabilities (CAP) | Optional IRC features the client asks for: `away-notify`, `account-notify`, `extended-join`, and `sasl` when enabled. Acknowledged ones set booleans on the client. | `rude_client.py`: `prtcl_CAP` |
| Mode symbols | The prefix characters in front of nicknames, such as `@` and `+`. `prtcl_005` builds `mode_to_symbol` from the server's `PREFIX`, in rank order. `sort_users` puts the highest rank first. `display_user_modes` turns the symbols off. | `rude_client.py`: `prtcl_005`, `get_mode_lists`, `sort_users`, `get_mode_symbol`, `get_user_mode`, `prtcl_MODE` |
| Nickname colours | Each nickname gets a hex colour, stored in `nickname_colours.json`. `ansi_color_nickname` turns it into a 24-bit ANSI escape that is written into the stored line. The chat view decodes the escape back into a colour. | `rude_gui.py`: `load_nickname_colors`, `save_nickname_colors`. `rude_client.py`: `ansi_color_nickname`, `update_nickname_colors`. `GUI/rude_colours.py` |
| Green text | Lines that start with an arrow such as `>` or `=>` are wrapped in IRC colour 03. Controlled by `green_text`. | `rude_client.py`: `green_texter` |
| Pronoun filter | When `replace_pronouns` is on and the channel is listed in `filtered_channels.txt`, outgoing text has gendered pronouns replaced. URLs are skipped. | `Client/rude_pronouns.py`, `rude_client.py`: `handle_user_input` |

## ZNC

| Term | Meaning | Where it lives |
| --- | --- | --- |
| ZNC connection | `znc_connection = True` in the `.rudeserver` file. The client sends `PASS <znc_password>` first and registers with `znc_user`. It changes retry timing, welcome handling, mention handling and `/detach`. | `rude_client.py`: `connect_to_server`, `send_initial_commands`, `_await_welcome_message`, `reconnect` |
| `*status` | The ZNC control user. A DM sender whose name starts with `*status` is stored as a DM and then handled by `handle_znc_status_message`. A message containing "disconnected" clears the three capability flags so they are asked for again. Other `*status` text is shown like a normal DM. Because the check runs after the generic DM code, `*status` also lands in `dm_list`. | `rude_client.py`: `prepare_direct_message`, `handle_znc_status_message` |
| ZNC sync, `znc_privmsg` | During the welcome sequence a ZNC client buffers PRIVMSG replay lines, then replays them through `prtcl_PRIVMSG(..., znc_privmsg=True)` so they are saved and highlighted but not drawn live. The screen shows "Syncing with ZNC". | `rude_client.py`: `_await_welcome_message`, `prtcl_PRIVMSG`, `handle_channel_message` |
| Auto attach | With ZNC on, a mention in a detached or unjoined channel adds it back to the list and requests `NAMES` and `TOPIC`. | `rude_client.py`: `auto_attach`, `notify_user_if_mentioned` |

## Files and content

| Term | Meaning | Where it lives |
| --- | --- | --- |
| `.rudeserver` | One INI file per server in the config folder, with an `[IRC]` section. Read by `read_config`, edited by the server config window. The README lists the keys. | `rude_client.py`: `read_config`, `reload_config`. `GUI/rude_config_server.py`. [data-files.md](data-files.md) |
| First run | `first_run.txt` holds `1` once setup is done. If it is missing or not `1`, `FirstRun` opens the server config window before the main window. `CopyConfigs` seeds the config folder from `DefaultConfig` only when the folder is empty. | `GUI/rude_first_run.py`, `Util/copy_configs.py`, `__main__.py` |
| Macros | ASCII art text files in `Resources/Macros`, loaded into `ASCII_ART_MACROS`. `/mac <name>` sends one line at a time, 0.4 s apart. `/macros` opens the folder and the Chat menu can reload them. They live in the install folder, not the config folder. | `rude_client.py`: `load_ascii_art_macros`, `cmd_mac`, `handle_pop_out_mac_command`, `update_available_macros` |
| Fortunes | Text files in `Resources/Fortunes`, split on `%` lines. `/fortune [list]` sends one. `/cowsay [list or text]` sends it inside a speech bubble. Shipped lists: `dadjoke`, `insults`, `therules`, `yomama`. | `rude_client.py`: `cmd_fortune`, `cmd_cowsay`, `fortune_cowsay`, `cowsay`, `get_fortune_file` |
| Splashes | Random ASCII art from `Resources/Splashes`, drawn in the chat view when you pick a server and after a connection finishes its welcome sequence. | `rude_gui.py`: `show_startup_art` |
| Mock | `/mock <text>` sends text with every odd-numbered character upper-cased. | `Client/rude_mock.py`, `rude_client.py`: `cmd_mock` |
| Broadcast | `/broadcast #a,#b <text>` sends one message to each listed channel. | `rude_client.py`: `cmd_broadcast` |
| Lock file | `channel_messages_<server_name>.lock`, created while history is being saved. Deleted when any client starts. | `rude_client.py`: `save_channel_messages`, `delete_lock_files` |
| Stale build copy | `build/lib/rudechat4`, an old build output ignored by git. Not the running code. | See [known-issues.md](known-issues.md) |

## App shell

| Term | Meaning | Where it lives |
| --- | --- | --- |
| Tray | The system tray icon, with Show and Quit actions. With `minimize_to_tray` on, closing the window hides it there. Desktop notifications go through the tray icon and only fire while the app has no active window. | `rude_gui.py`: `create_tray_icon`, `send_to_tray`, `restore_from_tray`, `quit_from_tray`, `trigger_desktop_notification`. `__main__.py`: `Window.closeEvent` |
| Protocol handler prefixes | `prtcl_<COMMAND>` handles one IRC command or numeric (`prtcl_JOIN`, `prtcl_353`). `bprtcl_*` sit under a "Combined Handlers" comment and cover several commands in one function. `m_prtcl_*` handle join-failure numerics. `cmd_*` implement slash commands. The code does not spell out what the leading `b` and `m` stand for. | `rude_client.py` |
| Worker names | `the_worker`, `the_cleaner`, `thread_killer`, `away_updater` and `away_watcher` are the background loops. Their task table is in [state-and-persistence.md](state-and-persistence.md#background-tasks). | `rude_client.py` |
| `BatchDecoderWorker` | A `QRunnable` that turns raw lines (IRC codes, ANSI colour) into styled text segments off the main thread. | `rude_gui.py` |
| `qt_update` | The 100 ms timer that lets asyncio run inside Qt. See [architecture.md](architecture.md#qt-and-asyncio-on-one-thread). | `__main__.py` |
