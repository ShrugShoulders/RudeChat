# Data files

RudeChat keeps its files in `~/.config/rudechat` (`G_CONFIG_DIR` in [`global_variables.py`](../src/rudechat4/global_variables.py)). On first run, `CopyConfigs` fills that folder from `src/rudechat4/DefaultConfig` if it is empty.

| File or folder | Written by | Contents |
| --- | --- | --- |
| `*.rudeserver` | You, or the server config window | One INI file per server. Keys are listed in the repo README. |
| `gui_config.ini` | You, or the GUI config window | Fonts and colours for the main window and widgets |
| `first_run.txt` | `FirstRun` | `1` once first-run setup is done |
| `nickname_colours.json`, `nickname_colours_bak.json` | `RudeGui` | Colour assigned to each nickname, plus a backup |
| `channel_messages_<server>.json` | `save_channel_messages` | Saved channel history for one server, loaded on startup |
| `<server>_away_users.json` | `save_away_users_to_file` | Users known to be away on one server |
| `<server_name>_open_dms.txt` | `save_dm_list` | DMs open on one server, restored on startup |
| `filtered_channels.txt` | You | Channels where the pronoun filter rewrites outgoing text. Not shipped in `DefaultConfig`; see [text-formatting.md](text-formatting.md) |
| `ignore_list.txt` | `save_ignore_list` | Ignored nicknames or hostmasks, shared across servers |
| `friend_list.txt` | `RudeFriends` | One friend per line, shared across servers |
| `channel_list.txt` | Channel list handler | Cached result of the last `/list` |
| `Logs/irc_log_<server>_<channel>.txt` | `log_message` | Plain text chat logs, when `use_logging` is on |
| `whois/` | `save_whois_to_file` | Saved WHOIS results |
| `RudeChat4.log` | `configure_logging` | Application debug log |
| `*.lock` | Client | Lock files, deleted on client startup by `delete_lock_files` |

## Sensitive data

- `.rudeserver` files can hold NickServ, SASL and ZNC passwords in plain text. Keep the folder private to your user account and don't commit it or attach it to bug reports.
- Chat logs, saved history, WHOIS results and the log file can contain nicknames, hostmasks and message content from other people. Treat them as personal data before sharing them, and redact or use synthetic data in any bug report, screenshot or demo.
