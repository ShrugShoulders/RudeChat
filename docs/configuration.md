# Configuration

This page lists every key RudeChat reads from `.rudeserver` files and `gui_config.ini`, what each one does and where the code reads it. For where the files live, see [data-files.md](data-files.md). For how the config windows are built in Qt, see [pyqt.md](pyqt.md).

Defaults on this page come from the `fallback=` values in the code, not from the README or from the files in `DefaultConfig/`. The three often disagree. See [Mismatches with the README](#mismatches-with-the-readme).

> **Warning: `.rudeserver` files hold passwords in plain text.** `nickserv_password`, `sasl_password` and `znc_password` are stored as written, and the config editor writes them back the same way. Keep `~/.config/rudechat` readable only by your own account, don't commit it, and redact those three keys before you paste a config into a bug report or a chat. These files are credential data. If you handle them for other people, your organisation's security and privacy rules apply.

## How the files are read

- Both files are INI files read with Python's `configparser`. Key names are case-insensitive. Boolean values accept `true/false`, `yes/no`, `on/off` and `1/0`.
- Every `*.rudeserver` file in `~/.config/rudechat` becomes one server. `initialize_clients` in `Client/init_clients.py` loads them in sorted file-name order at startup.
- A key marked "required" has no fallback. If it's missing, `RudeChatClient.read_config` raises, `init_client_with_config` logs the error and the server is added half configured. Treat these keys as mandatory.
- RudeChat uses `configparser` with its default settings, which don't strip inline comments. I checked this: `use_x = False # hi` reads back as the string `False # hi`, and `getboolean` raises `ValueError` on it. The README examples put `# ...` comments after every value, so copying them verbatim breaks any boolean or integer key. Put comments on their own lines or leave them out. The config editor also rewrites the file without any comments.

## `.rudeserver` keys

All keys live in the `[IRC]` section. `RudeChatClient.read_config` (`rude_client.py` lines 74 to 123) reads them at startup. `RudeChatClient.reload_config` (lines 125 to 152) re-reads a subset after you edit the file. The "Reload" column says whether a key takes effect without a restart. See [Reload after editing](#reload-after-editing).

### Connection

| Key | Type | Default | What it does | Read at | Reload |
| --- | --- | --- | --- | --- | --- |
| `server_name` | string | none (falls back to `Server_<n>`) | Display name of the server. It is the key in `RudeGui.clients`. The config editor also uses it, lower-cased, as the file name. Avoid spaces and dots. | `rude_client.py:89`, `rude_gui.py:766` | No |
| `server` | string | required | Host name passed to `asyncio.open_connection`. | `rude_client.py:77` | No |
| `port` | int | required | TCP port. | `rude_client.py:78` | No |
| `ssl_enabled` | bool | required | Wraps the connection in TLS. | `rude_client.py:79`, used at `:297` | No |
| `ignore_cert` | see note | `False` | Skips certificate and host name checks on a TLS connection. | `rude_client.py:92`, used at `:298` and `:306` | No |
| `nickname` | string | required | Nickname for `NICK` and `USER`. If the server answers 433, the client adds a random number from 1 to 99 and carries on. | `rude_client.py:80`, `:337`, `:350` | No |
| `auto_connect_to_networks` | bool | `False` | When `False`, the server is added to the server list but the client doesn't connect on startup. | `rude_client.py:112`, used at `rude_gui.py:771` | No |

`ignore_cert` is read with `config.get`, not `getboolean`. The value is the string `"False"`, which Python treats as true. If the key is present at all (even set to `False`), a TLS connection takes the "ignore certificate" branch. Only a missing key gives the real default. See the code oddities at the end of this page.

### Joining channels

| Key | Type | Default | What it does | Read at | Reload |
| --- | --- | --- | --- | --- | --- |
| `auto_join_channels` | comma-separated list | effectively required | Channels to join after connecting. The value is split on `,` with no trimming, so write `#a,#b` with no spaces. The fallback is `None`, and `None.split` raises, so a missing key breaks `read_config` and `reload_config`. | `rude_client.py:83`, `:130` | Yes. New channels are joined. Removed ones aren't left. |
| `use_auto_join` | bool | `True` | `True`: the client sends `JOIN` for each auto-join channel. `False`: the client waits for the server or bouncer to say which channels you are in. This is the mode for ZNC. See [ZNC setup](#znc-setup). | `rude_client.py:84` | No |
| `auto_rejoin` | bool | `True` | Rejoin a channel after you're kicked. If `False`, the kicked channel is removed from your list. | `rude_client.py:85`, used at `:4090` | No |
| `auto_join_invite` | bool | `True` | Join a channel when someone invites you. If `False`, the invite is only shown. | `rude_client.py:110`, used at `:3970` | Yes |

### Authentication

| Key | Type | Default | What it does | Read at | Reload |
| --- | --- | --- | --- | --- | --- |
| `use_nickserv_auth` | bool | `False` | Send `IDENTIFY` to NickServ after the MOTD. | `rude_client.py:81` | No |
| `nickserv_password` | string | required when `use_nickserv_auth` is true, otherwise ignored | NickServ password. | `rude_client.py:82` | No |
| `sasl_enabled` | bool | `False` | Request the `sasl` capability and authenticate with SASL PLAIN. | `rude_client.py:86` | No |
| `sasl_username` | string | `None` | SASL account name. The client sends it as both the authorisation and authentication identity. | `rude_client.py:87`, used at `:3834` | No |
| `sasl_password` | string | `None` | SASL password. | `rude_client.py:88` | No |
| `znc_connection` | bool | `False` | Treat the server as a ZNC bouncer. | `rude_client.py:90` | No |
| `znc_user` | string | `None` | Sent as the `NICK` and `USER` name when `znc_connection` is true. | `rude_client.py:93`, used at `:334` | No |
| `znc_password` | string | `None` | Sent as `PASS <value>` right after the socket opens when `znc_connection` is true. | `rude_client.py:91`, used at `:321` | No |

Step-by-step setup is in [SASL setup](#sasl-setup), [NickServ setup](#nickserv-setup) and [ZNC setup](#znc-setup).

### Display and behaviour

| Key | Type | Default | What it does | Read at | Reload |
| --- | --- | --- | --- | --- | --- |
| `use_time_stamp` | bool | `True` | Prefix chat lines with `[HH:MM:SS]`. | `rude_client.py:100` | Yes |
| `show_hostmask` | bool | `True` | Join, part and quit lines show the full `nick!user@host` mask. If `False` they show the coloured nickname only. Stored as `show_full_hostmask`. | `rude_client.py:101`, used at `:4010`, `:4362`, `:4506` | Yes |
| `show_join_part_quit_nick` | bool | `True` | Show join, part, quit and nick-change lines at all. | `rude_client.py:102` | Yes |
| `display_user_modes` | bool | `True` | Show the mode symbol (`@`, `+` and so on) next to nicknames in chat. | `rude_client.py:95`, used at `:1845` | Yes |
| `mention_note_color` | colour string | `#ff0000` | Background of a channel or server entry when someone mentions you. Lower-cased on first read. | `rude_client.py:98`, `:131` | Yes, but see note below |
| `activity_note_color` | colour string | `#008000` | Background of a channel or server entry that has new activity. | `rude_client.py:99`, `:132` | Yes, but see note below |
| `use_irc_colors` | bool | `False` | When `False`, the receive loop strips `\x03` colour codes from incoming data before parsing. Bold, italic and the other control codes stay. See [text-formatting.md](text-formatting.md). | `rude_client.py:94`, used at `:2190` | Yes |
| `use_emojis` | bool | `True` | Turn text smileys such as `:)` into emoji, on both sent and received text. When `False`, `:name:` aliases still convert. | `rude_client.py:97`, used at `:1432` | Yes |
| `green_text` | bool | `True` | Wrap lines that start with `>` or another arrow symbol in green. | `rude_client.py:109`, used at `:1417` | Yes |
| `replace_pronouns` | bool | `False` | Rewrite gendered pronouns in your outgoing messages, in channels listed in `filtered_channels.txt`. | `rude_client.py:107`, used at `:2853` | Yes |
| `send_ctcp_response` | bool | `True` | Answer incoming CTCP requests such as VERSION and PING. | `rude_client.py:108`, used at `:1141` | Yes |
| `auto_whois` | bool | `True` | Send `WHOIS` for users who message you, and for tracked away users. | `rude_client.py:104`, used at `:171`, `:1576` | Yes |

The mention and activity colours reload with different fallbacks than they start with: `read_config` falls back to `#ff0000` and `#008000` and lower-cases the value, while `reload_config` falls back to `red` and `green` and doesn't lower-case. If you set both keys in the file, you won't see a difference. If you rely on the defaults, a reload changes the colour names.

### Away, sound and logging

| Key | Type | Default | What it does | Read at | Reload |
| --- | --- | --- | --- | --- | --- |
| `use_auto_away` | bool | `True` | Mark you away after you've been idle for `auto_away_minutes`. Sending a message or `/me` resets the timer and clears away. | `rude_client.py:96`, used at `:924`, `:2845` | Yes |
| `auto_away_minutes` | int | `30` | Idle minutes before auto away. Read by `AutoAway`, not by the client. A non-numeric value makes `int()` raise. The check runs every 120 seconds, so the real delay can be up to two minutes longer. | `Client/rude_auto_away.py:34`, `rude_client.py:119` | Yes |
| `use_beep_noise` | bool | `True` | Play a sound and show a tray notification when you're mentioned. | `rude_client.py:103`, used at `:1284` | Yes |
| `custom_sounds` | bool | `False` | Use `Resources/Sounds/Notification4.wav` instead of the system sound. macOS uses `afplay` and Linux uses `paplay`. The README says "Linux Only", but the macOS branch exists too. Windows always uses `winsound.Beep`. | `rude_client.py:105`, used at `:1391`, `:1399` | Yes |
| `use_logging` | bool | `True` | Write plain text chat logs to `Logs/irc_log_<server>_<channel>.txt`. | `rude_client.py:106`, used at `:2284` | Yes |
| `log_on` | bool | `False` | Turn on verbose client debug logging to `RudeChat4.log`. Don't confuse it with `use_logging`. | `rude_client.py:111` | Yes |

### Auto away in detail

`AutoAway` in `Client/rude_auto_away.py` keeps a timestamp of your last activity. `away_watcher` in `rude_client.py` wakes every 120 seconds. If the idle time is past `auto_away_minutes` and you aren't already away, it sends `AWAY :Auto Away @ <time>`. When `use_auto_away` is `False` the loop only saves the away-users file every 250 seconds. `reload_config` builds a fresh `AutoAway`, which also resets the idle timer.

## `gui_config.ini` keys

`RudeGui.read_config` (`rude_gui.py` lines 259 to 327) reads the file. If the file doesn't exist, it sets the same defaults directly. The sections are `[Chat]`, `[Entry]`, `[Lists]` and `[Utility]`. The README documents `[GUI]` and `[WIDGETS]` instead. See [Mismatches with the README](#mismatches-with-the-readme).

Colour values go to Qt style sheets and `QColor`, so any CSS-style name or `#rrggbb` value works. Font sizes go into style sheets as pixels.

### `[Chat]`

| Key | Type | Default | What it does | Read at |
| --- | --- | --- | --- | --- |
| `window_bg` | colour | `#1b1e20` | Main window, labels and topic bar background. Also the default background in the text decoder. | `rude_gui.py:266`, used at `:505` and others |
| `window_fg` | colour | `#C0FFEE` | Text colour for the same widgets. Also the colour given to nicknames when nickname colours are off. | `rude_gui.py:267` |
| `window_font_family` | string | `Courier` | Font for the topic bar. | `rude_gui.py:268`, used at `:506` |
| `window_font_size` | int | `12` | Font size (px) for the topic bar. | `rude_gui.py:269`, used at `:507` |
| `chat_bg` | colour | `#1b1e20` | Chat view background. | `rude_gui.py:270`, used at `:518` |
| `chat_fg` | colour | `#C0FFEE` | Default chat text colour. | `rude_gui.py:271`, used at `:517` |
| `chat_font_family` | string | `Courier` | Chat view font. Also used by pop-out windows and by the text decoder. | `rude_gui.py:272`, `GUI/rude_popout.py:345` |
| `chat_font_size` | int | `12` | Chat view font size. Used as pixels in the style sheet and as points in the decoder. | `rude_gui.py:273`, `:1787` |

### `[Entry]`

| Key | Type | Default | What it does | Read at |
| --- | --- | --- | --- | --- |
| `entry_bg` | colour | `#1b1e20` | Input box background. | `rude_gui.py:274` |
| `entry_fg` | colour | `#C0FFEE` | Input box text. | `rude_gui.py:275` |
| `entry_selected_bg` | colour | `#C0FFEE` | Selection highlight in the input box. | `rude_gui.py:276` |
| `entry_font_family` | string | `Courier` | Input box font. | `rude_gui.py:277` |
| `entry_font_size` | int | `12` | Input box font size. | `rude_gui.py:278` |

### `[Lists]`

| Key | Type | Default | What it does | Read at |
| --- | --- | --- | --- | --- |
| `list_bg` | colour | `#1b1e20` | Background of the user and channel lists. Also the background for server entries that aren't highlighted. | `rude_gui.py:279` |
| `list_font_family` | string | `Courier` | Font for the lists. | `rude_gui.py:282` |
| `list_font_size` | int | `12` | Font size for the lists. | `rude_gui.py:283` |
| `list_user_fg` | colour | `#C0FFEE` | User list text. | `rude_gui.py:287` |
| `list_user_away_fg` | colour | `#4c6c3b` | Text colour for users who are away. | `rude_gui.py:288` |
| `list_channel_fg` | colour | `#C0FFEE` | Channel list text. | `rude_gui.py:281` |
| `list_channel_needwho_fg` | colour | `#a4a4a4` | Text colour for channels still waiting for their WHO reply. | `rude_gui.py:286` |
| `list_channel_current_bg` | colour | `blue` | Selection colour in the channel list, and the server-box highlight for the selected server. | `rude_gui.py:284`, used at `:591`, `:1357` |
| `list_channel_select_bg` | colour | `blue` | Background set on a channel item when you click it. Not in the shipped `gui_config.ini` and not in the editor's label map, so it only works if you add it by hand. | `rude_gui.py:285`, used at `:2106` |
| `list_server_fg` | colour | `#C0FFEE` | Text colour for server entries when they're highlighted. | `rude_gui.py:280`, `rude_client.py:1325` |

### `[Utility]`

| Key | Type | Default | What it does | Read at |
| --- | --- | --- | --- | --- |
| `main_nickname_color` | colour | `#39ff14` | Colour of your own nickname when nickname colouring is on. | `rude_gui.py:289`, `rude_client.py:1741`, `:4679` |
| `generate_nickname_colors` | bool | `True` | `True`: give each new nickname a random colour. `False`: every nickname uses `window_fg`. See [text-formatting.md](text-formatting.md#nickname-colouring). | `rude_gui.py:290`, `rude_client.py:1736` |
| `minimize_to_tray` | bool | `True` | Close button hides the window to the tray instead of quitting. | `rude_gui.py:291`, `__main__.py:72` |
| `turn_logging_on` | bool | `False` | GUI debug logging. Stored as `RudeGui.log_on`. | `rude_gui.py:292` |
| `tab_complete_terminator` | string | `:` | Text added after a nickname that you tab-complete at the start of a line. | `rude_gui.py:293`, used at `:121` |
| `scrollbar_bg` | colour | `#2a2e32` | Scrollbar background and handle. | `rude_gui.py:294`, `GUI/list_window.py:59` |
| `url_color` | colour | `#3d85c6` | Colour of detected links. | `rude_gui.py:295`, used at `:1864` |

### Other readers of `gui_config.ini`

| Reader | Keys | Notes |
| --- | --- | --- |
| `GUI/rude_shutdown.py:20` | `[Chat] window_bg`, `window_fg` | Same defaults as above.

When the file is missing entirely, `rude_gui.py` lines 298 to 327 set the same values as the fallbacks. The shipped `gui_config.ini` differs from both in one key: `entry_bg` is `#2a2e32` there and `#1b1e20` in the code.

## SASL setup

1. Set `sasl_enabled = True`, `sasl_username` and `sasl_password`. Leave `use_nickserv_auth` off. If both are on, the NickServ branch is skipped when SASL is enabled.
2. The client sends `CAP LS 302` when it connects. On the `LS` reply it requests `away-notify`, `account-notify`, `extended-join` and, if SASL is on, `sasl` (`prtcl_CAP`, `rude_client.py:3869`).
3. When the server acknowledges `sasl`, the client sends `AUTHENTICATE PLAIN`. When the server replies `AUTHENTICATE +`, the client sends the base64 of `username\0username\0password` (`prtcl_AUTHENTICATE`, line 3828).
4. On numeric 903 the client prints "SASL authentication successful" and sends `CAP END`. It then auto-joins after the MOTD (numeric 376) if `use_auto_join` is on.
5. On numeric 904 the handler calls `bprtcl_to_client()` without its required `tokens` argument (`rude_client.py:511`). That looks like a bug, so a failed login probably raises a `TypeError` instead of showing a clean message. I didn't run it to confirm. The code also never sends `CAP END` after a 904.

Only SASL PLAIN is implemented. There's no EXTERNAL or SCRAM support.

## NickServ setup

1. Set `use_nickserv_auth = True` and `nickserv_password`. Keep `sasl_enabled = False` and `znc_connection = False`. The NickServ branch only runs when both are off.
2. After the MOTD ends (numeric 376) the client sends `PRIVMSG NickServ :IDENTIFY <nickname> <nickserv_password>` and notes "Sent NickServ authentication".
3. The client then waits. Numeric 900 (logged in) triggers auto-join. A NickServ notice containing "invalid password" also releases the wait, so the client still joins channels. A separate handler for numeric 042 sends `IDENTIFY <password>` (without the nickname) and joins.
4. If your network never sends 900 or 042, I couldn't find another path that joins channels in this mode. Test it on your network before relying on it.

Use the nickname you registered. The `IDENTIFY` line uses the client's current nickname, which changes if the server forced a 433 suffix.

## ZNC setup

1. Set `znc_connection = True`, `znc_user` and `znc_password`.
2. Set `use_auto_join = False`. The bouncer already knows your channels, and this flag puts the client in "collect and replay" mode. With `use_auto_join = True` the client sends its own `JOIN` lines as well.
3. On connect the client sends `PASS <znc_password>` first, then `NICK` and `USER` with `znc_user`. The code sends `znc_password` exactly as written. ZNC's own convention for several networks is `user/network:password`. That string has to go in `znc_password`, because the client doesn't build it. This convention comes from ZNC, not from RudeChat's code.
4. The client queues topics, name lists and replayed messages until the stream goes quiet for 0.3 seconds, or 60 seconds pass, then processes them in one batch and prints "Syncing with ZNC" and "Processing Tokens". With `use_auto_join = False` the client doesn't send its own `JOIN` lines, so what you see depends on what ZNC replays.
5. Reconnect waits 5 seconds for ZNC and 15 seconds for other servers, up to 5 tries (`reconnect`, line 886).
6. NickServ identification at numeric 376 is skipped when `znc_connection` is true. Let ZNC's own modules identify you.

## The config editor windows

Both editors are `QScrollArea` forms that build themselves from the file's contents.

- **GUI editor** (`GUI/rude_config_gui.py`, class `RudeConfigGui`): opened with Ctrl+W or the Config menu. It reads `gui_config.ini` and shows one group box per section.
- **Server editor** (`GUI/rude_config_server.py`, class `RudeConfigServer`): opened with Ctrl+E or the Config menu. It extends `RudeConfigGui`, replaces `label_map` with the `.rudeserver` keys and adds a file picker and an "Apply" button in `RudeGui.open_client_config_window`. `FirstRun` uses the same class with a "Start Client" button.

How they work:

- **Label map.** Each key maps to a label and a widget type: `bool` (checkbox), `string` (line edit), `int` (line edit with a two-digit mask, so 0 to 99), `color` (`RudeColorOption`, a line edit plus a colour picker) and `channels` (a button that opens `ChannelExp`, the list editor for `auto_join_channels`).
- **Only keys already in the file appear.** The form is built from `config.options(section)`. A key you haven't added to the file has no field. To use a newer key, add it to the file by hand first. The editor can't create it.
- **Unknown keys.** A key that isn't in the label map is labelled with its own name. The widget type is then looked up as `option[1]`, which is the second character of the key name. That matches no widget type, so the loop reuses the previous field. I read this path but didn't test it, so avoid hand-added keys that the editor doesn't know (for example `list_channel_select_bg`) if you plan to save from the editor. Check the file afterwards.
- **`port` and `auto_away_minutes` are plain text fields.** The editor doesn't check that they're numbers.
- **Saving.** `save_config` builds a new `ConfigParser` from the widgets, so comments and key order from your hand-edited file are lost. Booleans are written as `True` or `False`.
- **Renaming.** For server files, the editor lower-cases `server_name`, appends `.rudeserver` and writes to that path. Change the server name to create a new server file. The old file stays on disk. Delete it yourself if you meant to rename.
- **Picking another server file.** The combo box at the top reloads the form from the chosen file. If you edit one file and then switch before pressing Apply, the edits aren't kept.
- **Editing channels.** The "Edit Channels..." button only opens when `auto_join_channels` is non-empty. A file with an empty value can't be edited this way.

## Reload after editing

Both windows call a close callback after saving. The callback waits 100 ms, reloads, waits another 100 ms and closes the window (`QTimer.singleShot(100, ...)` and `(200, ...)`).

**After the GUI editor:** `RudeGui.open_gui_config_window` calls `read_config()` and then `apply_settings()`. That re-reads every key in the tables above, rebuilds the style sheets (`set_gui_theme`), reloads `nickname_colours.json` and re-highlights away users. Text already in the chat view keeps the formatting it was drawn with. Open pop-out windows read their colours and fonts from the main window when they are built (`GUI/rude_popout.py:343` to `:354`).

**After the server editor:** `open_client_config_window` does two things.

1. For each `.rudeserver` file, it finds the client whose server name matches the file name (compared lower-case) and calls `reload_config(path)`. Keys that reload: `auto_join_channels` (and new channels are joined), `mention_note_color`, `activity_note_color`, `use_time_stamp`, `show_hostmask`, `show_join_part_quit_nick`, `use_beep_noise`, `auto_whois`, `custom_sounds`, `use_logging`, `use_irc_colors`, `replace_pronouns`, `display_user_modes`, `send_ctcp_response`, `green_text`, `use_auto_away`, `auto_join_invite`, `use_emojis`, `log_on` and `auto_away_minutes`.
2. `new_server_config_connect` looks for `.rudeserver` files with no matching server in the list and starts a new client for each. That's how a new server connects without a restart. A new client still respects `auto_connect_to_networks`.

**Needs a restart or a reconnect:** `server`, `port`, `ssl_enabled`, `ignore_cert`, `nickname`, `server_name`, `use_nickserv_auth`, `nickserv_password`, `sasl_*`, `znc_*`, `use_auto_join`, `auto_rejoin` and `auto_connect_to_networks`. `reload_config` doesn't touch them. A client whose `server_name` doesn't match its file name (ignoring case) also isn't matched for reload.

If you edit a file by hand in a text editor, nothing watches the file. Open the server editor and press Apply (even without changes) to trigger the reload, or restart the app. Applying rewrites the file, so it also strips your comments.
