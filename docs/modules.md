# Module reference

Paths are relative to `src/rudechat4`. "Docstrings" shows how many classes and functions had a docstring on 2026-11-21, before any inline documentation work. Update the column as modules are documented.

## Top level

| Module | Purpose | Docstrings |
| --- | --- | --- |
| `__main__.py` | Entry point. Defines `Window` (menu bar, close handling) and `__main__()` (startup, Qt and asyncio bridge). Installed as the `rudechat` command. | 3 / 9 |
| `rude_gui.py` | `RudeGui`, the main widget, plus `BatchDecoderWorker`, `TabEventFilter` and `ArrowKeyEventFilter`. Builds the layout, loads GUI config, owns the clients dict, handles input, tray icon and nickname colours. | 11 / 104 |
| `rude_client.py` | `RudeChatClient`, one IRC connection. Connection handling, protocol parsing, slash commands, history, logging, notifications. See [commands.md](commands.md). | 52 / 209 |
| `global_variables.py` | `G_SOURCE_DIR`, `G_CONFIG_DIR`, IRC format and colour tables, ANSI to IRC colour maps. | none (constants) |
| `shared_imports.py` | Star-import hub for standard library and PyQt6 names, plus the GPL notice. | none (imports) |

## Client/

Logic that belongs to an IRC connection but isn't protocol handling.

| Module | Purpose | Docstrings |
| --- | --- | --- |
| `init_clients.py` | `initialize_clients(app)` finds `*.rudeserver` files and starts one client per file. | 0 / 1 |
| `rude_auto_away.py` | `AutoAway` tracks the last message time and reports when the `auto_away_minutes` threshold passes. | 0 / 7 |
| `rude_friends.py` | `RudeFriends` loads and saves `friend_list.txt` and tracks which friends are online. | 6 / 8 |
| `rude_pronouns.py` | `replace_pronouns(text, channel=None)` rewrites gendered pronouns to neutral wording. Used when `replace_pronouns` is on. | 0 / 7 |
| `rude_mock.py` | `RudeMock.generate_mock()` returns text in alternating case. Backs `/mock`. | 0 / 3 |

## Components/

Small Qt widget subclasses used by `RudeGui`.

| Module | Class | Docstrings |
| --- | --- | --- |
| `rude_channel_list_widget.py` | `RudeChannelListWidget` | 3 / 5 |
| `rude_user_list_widget.py` | `RudeUserListWidget` | 3 / 9 |
| `rude_server_list_widget.py` | `RudeServerListWidget` | 0 / 5 |
| `rude_text_browser.py` | `RudeTextBrowser`, the chat view | 1 / 11 |
| `rude_message_entry.py` | `RudeMessageEntry`, the input box | 0 / 6 |
| `rude_color_option.py` | `RudeColorOption`, a label with a colour picker (`pickColor`) | 0 / 5 |

## GUI/

Dialogs and secondary windows.

| Module | Purpose | Docstrings |
| --- | --- | --- |
| `rude_popout.py` | `RudePopout` and helpers for channel and DM pop-out windows | 4 / 49 |
| `rude_config_gui.py` | `RudeConfigGui`, base class for the config editors | 0 / 7 |
| `rude_config_server.py` | `RudeConfigServer`, the `.rudeserver` editor. Extends `RudeConfigGui`. | 0 / 4 |
| `rude_first_run.py` | `FirstRun`, first-launch detection and the setup window | 0 / 10 |
| `rude_colours.py` | `RudeColours`, the window for viewing, saving and resetting nickname colours | 0 / 12 |
| `rude_shutdown.py` | `RudeShutdown`, a small window that shows a random goodbye message while the app closes | 0 / 5 |
| `channel_expand.py` | `ChannelExp`, a window with a channel name input | 0 / 7 |
| `list_window.py` | `ChannelListWindow`, results of `/list` | 0 / 10 |
| `nick_editor.py` | `NickEditor`, add or edit one nickname and colour entry. Takes a callback for the result. | 0 / 5 |
| `user_data_display.py` | `RudeUserData`, the user info form (Qt Designer style `setupUi`) | 2 / 6 |

## Util/

| Module | Purpose | Docstrings |
| --- | --- | --- |
| `copy_configs.py` | `CopyConfigs()` copies `DefaultConfig/` into the config folder when it's empty. | 0 / 1 |
| `rude_logger.py` | `configure_logging()` sets up console and file logging at DEBUG level, once. Log file is `RudeChat4.log` in the config folder. | 0 / 1 |
| `nick_cleaner.py` | `is_valid_nickname` and `clean_nicknames` filter out nicknames IRC wouldn't accept. | 0 / 2 |

## Non-code resources

- `DefaultConfig/` holds the starter `gui_config.ini` and `libera.rudeserver`.
- `Resources/Macros` has ASCII art for `/mac`. `Fortunes` feeds `/fortune` and `/cowsay`. `Splashes` has the startup art. `Icons` and `Sounds` hold app icons and the notification sound.

## Outside the package

| File | Purpose |
| --- | --- |
| `RudeUpdate.py` | Update helper in the repo root. It merges an updated INI config with a backed-up one so your settings survive an upgrade. |
| `setup.py`, `pyproject.toml`, `RudeChat.spec`, `macBuild.sh` | Packaging and build scripts (setuptools, PyInstaller, py2app) |
| `.github/workflows/build-installers.yml` | CI that builds the installers |

## Documentation priority

Suggested order for adding inline docs: `Util/`, `Client/`, `Components/`, `GUI/`, then `rude_gui.py`, `rude_popout.py` and `rude_client.py`. The last three are large, so work through them in sections (connection, receive loop, commands, display).
