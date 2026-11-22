# Development

How to run RudeChat from source, where it keeps its files, and how to check a change by hand. For packaging, see [build-and-release.md](build-and-release.md). For how the code fits together, see [architecture.md](architecture.md).

## Python version

- The code needs Python 3.12 or newer. It uses `match` statements (3.10), and `rude_client.py` has f-strings that reuse the same quote character and put a backslash inside the braces, for example `{formatted_message.strip("\n")}` in `cmd_mac`. Only 3.12 and later accept that syntax. The CI jobs on GitHub's runners use 3.12.
- `qt_update()` in `__main__()` drives asyncio from a 100 ms Qt timer. [architecture.md](architecture.md) explains why a blocking call in a coroutine freezes the window.

## Set up from source

Clone the repo and work from its root. The commands below make a virtual environment inside the checkout. Use any name you like, but don't commit it.

### macOS

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src python -m rudechat4
```

On macOS, `shared_imports.py` runs `from objc import lookUpClass` at import time. `requirements.txt` doesn't list a package that provides `objc`. If the import fails, `pip install pyobjc-core` should provide it.

### Linux

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src python -m rudechat4
```

The CI installs these Debian and Ubuntu packages before it builds: `libegl1`, `libxkbcommon-x11-0`, `libxcb-cursor0`, `libdbus-1-3` and `libasound2-dev`. The repo doesn't say which of them a source run needs. If Qt fails to load its `xcb` plugin, start with that list. Some features call external programs: `xdg-open` for `/logs`, `/macros` and similar, and `paplay` for custom notification sounds.

### Windows

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:PYTHONPATH = "src"
python -m rudechat4
```

### Installing into the environment instead

`pip install -r requirements.txt .` is the README's Linux install command, and it works for development if you reinstall after each change.

## Run the app

Any of these start the same code:

- `PYTHONPATH=src python -m rudechat4`
- `PYTHONPATH=src python src/rudechat4` (the folder has a `__main__.py`, so Python runs it)
- `rudechat`, after a `pip install .`

### VS Code

[`.vscode/launch.json`](../.vscode/launch.json) has one configuration, named "Python Debugger: Current File". It uses `debugpy` to launch `${workspaceFolder}/src/rudechat4` with `PYTHONPATH` set to `${workspaceFolder}/src` and the integrated terminal as the console. The name says "Current File", but the program path is fixed, so it always launches the app. `.vscode/settings.json` sets four-space indentation and hides `build/` from search.

## Where files live

RudeChat keeps everything in `~/.config/rudechat`. `G_CONFIG_DIR` in [`global_variables.py`](../src/rudechat4/global_variables.py) builds that path from `os.path.expanduser("~")`, and the module creates the folder on import. On Windows the same code produces `C:\Users\<you>\.config\rudechat`. [data-files.md](data-files.md) lists every file.

The ones you need while developing:

| File or folder | Use |
| --- | --- |
| `RudeChat4.log` | Application log. `configure_logging()` in `Util/rude_logger.py` sends DEBUG-level output to this file and to the console. |
| `*.rudeserver` | One INI file per server. `CopyConfigs` seeds `libera.rudeserver` on first run. |
| `gui_config.ini` | Fonts and colours. |
| `first_run.txt` | Holds `1` after the first-run window is done. |
| `Logs/` | Plain text chat logs, when `use_logging` is on. |

Things that trip people up:

- `CopyConfigs` copies the defaults only when `~/.config/rudechat` is empty. A new key in `DefaultConfig/` never reaches an existing folder. Add it by hand to your copy.
- Delete the folder, or move it aside, to see the first-run flow again. Deleting only `first_run.txt` should also reopen the first-run window, since `FirstRun.load_first_run` treats a missing file as a first run. The window needs at least one `.rudeserver` file in the folder or it shows a warning.
- The `log_on` option in a `.rudeserver` file and `turn_logging_on` in `gui_config.ini` turn on extra debug logging inside the client and the GUI. Both default to off.
- Resources (macros, fortunes, splashes, sounds, icons) are read from the package folder (`G_SOURCE_DIR`), not from the config folder. In a source run that's `src/rudechat4/Resources`.

### Sensitive data

`.rudeserver` files hold NickServ, SASL and ZNC passwords in plain text. Logs, saved history, WHOIS files and `RudeChat4.log` contain nicknames, hostmasks and message text from other people, which counts as personal data. Don't commit the config folder, and don't paste its contents into issues. For the smoke test below, use a throwaway nickname and a test channel you control, and redact anything you share.

## Manual smoke test

Run it after a change that touches the area. Each item names the code that handles it so you know where to look when it fails. Check `RudeChat4.log` after every run.

**Startup and config**

- [ ] With an empty `~/.config/rudechat` (move the real one aside), the app copies `libera.rudeserver` and `gui_config.ini` and shows the first-run server window. Applying it starts the client. (`CopyConfigs`, `FirstRun`)
- [ ] On the next launch the first-run window doesn't reappear. (`first_run.txt`)
- [ ] The main window shows splash art from `Resources/Splashes`, then the server's MOTD after connecting. (`show_startup_art`)
- [ ] With two `.rudeserver` files, both connect, and the server combo box switches between them. (`initialize_clients`, `on_server_change`)
- [ ] A server with a bad address reports an error in the console or log and doesn't block the next server.

**Channels and messages**

- [ ] `/join #channel` adds the channel to the list and fills the user list. Channel and user counts in the labels update.
- [ ] Type a message. It appears with your nickname (and timestamp when `use_time_stamp` is on) and shows on a second client.
- [ ] A message over about 420 characters splits into chunks. (`handle_user_input`)
- [ ] Switching channels loads the saved history in order. (`load_channel_messages`)
- [ ] A line that contains your nickname marks the channel as mentioned, and plays a beep if `use_beep_noise` is on. `/mentions` lists it, and `/mentions clear` empties it.
- [ ] URLs in chat are clickable and open in the browser.
- [ ] `/part #channel` removes the channel.
- [ ] `/query nick` opens a DM, and `/cq nick` closes it.
- [ ] `/me waves` sends an action.

**Input box**

- [ ] Tab completes a nickname from the user list, with the `tab_complete_terminator` after it at the start of a line.
- [ ] Tab on `/jo` should complete to `/join `. (`TabEventFilter.command_list`)
- [ ] Up and Down arrows walk the last ten entries. (`ArrowKeyEventFilter`)
- [ ] The formatting shortcuts (Ctrl+B, Ctrl+I, Ctrl+S, Ctrl+/ and Ctrl+N or Ctrl+U) wrap selected text, and a coloured message renders in the chat view.

**Commands**

- [ ] `/help` opens the `!HELP!` pseudo-channel with the full command list.
- [ ] `/mac` lists macros. `/mac shrug` sends one. Chat > Reload Macros picks up a new file.
- [ ] `/fortune`, `/fortune dadjoke`, `/cowsay hello` and `/mock hello world` each send output to the channel.
- [ ] `/away reason`, then `/back`. The away state shows in the user list.
- [ ] `/ignore nick` and `/unignore nick`.
- [ ] `/whois nick`, `/who mask`, `/names`, `/topic`, `/banlist`.
- [ ] `/list` opens the channel list window.
- [ ] `/logs`, `/macros`, `/fortunes`, `/swhois` and `/sounds` open the matching folder in the file manager.
- [ ] `/disconnect`, then `/connect <server_name>`.
- [ ] `/quote PING test` shows a raw reply.

**Windows and menus**

- [ ] Pop out a channel from the channel list's context menu. Send a message from the pop-out. `/sw #channel` brings it back. Slash commands in pop-outs behave differently. See [extending.md](extending.md).
- [ ] Config > Edit GUI (Ctrl+W) changes a colour. Apply updates the main window without a restart.
- [ ] Config > Edit Servers (Ctrl+E) changes a setting. Apply reloads it. A new server file connects automatically.
- [ ] Colors > Color Selector opens, and Save Colors and Reset Colors work.
- [ ] Chat > Clear Chat clears the view and the saved messages for the channel.
- [ ] Ctrl+] and Ctrl+[ (and PgUp and PgDown) cycle channels. Ctrl+Shift+\ cycles servers.

**Tray and exit**

- [ ] With `minimize_to_tray` on, closing the window hides it. The tray icon's Show restores it, and Quit exits.
- [ ] With `minimize_to_tray` off, closing the window exits and the channel history file (`channel_messages_<server>.json`) updates.
- [ ] The app exits without a traceback in the console.

**Platform extras**

- [ ] macOS: the App > About menu opens the native About panel.
- [ ] Linux with `custom_sounds` on: `paplay` plays `Notification4.wav`.
- [ ] Windows: a mention produces a short beep.

## Branches and history

The output below comes from `git branch -a` and `git log --oneline -15`, run at `174a20e`.

Branches:

| Branch | Where | Notes |
| --- | --- | --- |
| `RudeChat4.2` | local and `origin` | Current branch. Where this work happens. |
| `RudeChat4` | local and `origin` | `origin/HEAD` points here, so it's the remote's default. Local and remote are both at `5eb1535` ("ver change"), which is also what tag `v4.2.0` points to. |
| `RudeChat3` | `origin` only | The previous major version. |
| `old-main` | `origin` only | An early upload. |
| `feat_revampedconfigs` | `origin` only | Its last commit message is "trade ini for json, make config load into the gui." |
| `copilot/fix-build-fedora-rpm` | `origin` only | Merged into `RudeChat4.2` as pull request #13. |
| `copilot/fix-build-musl-alpine-job` | `origin` only | Merged into `RudeChat4.2` as pull request #14. |

The other tags are `v4.0.0`, `v4.1.0`, `v4.1.1`, and four older ones for version 3 (`RudeChat3.0.4-Linux`, `RudeChat3Win304`, `RudeChat3Win314`, `RudeChat_MacOS-rev34`).
