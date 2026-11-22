# Extending RudeChat

Step lists for the common additions. Names were checked against the source on the `RudeChat4.2` branch. Test each change with the checklist in [development.md](development.md), and add new modules to the tables in [modules.md](modules.md).

Resources (macros, fortunes, splashes, sounds) live in `src/rudechat4/Resources` and are read from `G_SOURCE_DIR`, the package folder. For a pip install that's inside `site-packages`. For a PyInstaller build it's inside the bundle. Files you drop into an installed copy disappear on the next upgrade.

## A slash command

The example below adds `/yell`.

1. Open `command_parser` in [`rude_client.py`](../src/rudechat4/rude_client.py). It lowercases the first word into `primary_command` and matches on it. `args[0]` is the command, and `args[1:]` are the words after it, split on whitespace. Add a case above `case None`:

   ```python
   case "yell": await self.cmd_yell(args)
   ```

   There is no `case _`, so a command nobody wrote is dropped without a message.
2. Write the handler as a `cmd_yell` method near the other `cmd_*` methods. Make it `async def` when it sends to the server or sleeps, and `await` it in the case. A plain `def` is called without `await`, as `cmd_cq` and `cmd_watch` are. Useful pieces, all used by existing commands:
   - `self.current_channel` is the target channel.
   - `await self.send_message(f'PRIVMSG {channel} :{text}')` sends a raw line.
   - `self.gui.insert_text_widget(f"...\n")` prints a local line in the chat view.
   - `await self.append_to_channel_history(channel, text, mode_symbol)` stores a line you sent, as `cmd_mac` does.
3. Add a line for it in `display_help`, in the list for the right category in the `categories` dictionary. End every string with a comma. The `/sounds` line in the "Fun" list has none today, so Python joins it to the `/mock` line and the two show as one entry.
4. Add the name to `TabEventFilter.command_list` in [`rude_gui.py`](../src/rudechat4/rude_gui.py). That list drives Tab completion after a `/`. `sounds` is missing from it today.
5. Add a row to the right table in [commands.md](commands.md).

Check these:

- The command should work in the main input box. That path is `RudeGui.on_enter_key`, which calls `command_parser` directly.
- Pop-out windows are different. In `GUI/rude_popout.py` the send handler only special-cases `mac` and `me`. The `case None` branch next to them can't match, because `args[0]` is always a string. From reading that code, other slash commands typed in a pop-out seem to go out as ordinary message text instead of reaching `command_parser`. I haven't run it to confirm. If your command needs to work in pop-outs, add a case there too.
- A command that only opens a folder can reuse `show_file_folder` and the existing `case "logs" | "fortunes" | ...` line. Add a branch for your folder inside `show_file_folder`.

## An ASCII art macro

1. Create `src/rudechat4/Resources/Macros/<name>.txt`. The file name without `.txt` is the macro name, and it's case-sensitive. Use a single word, because `/mac` reads its argument from a whitespace split.
2. Put the art in the file as plain UTF-8 text. `load_ascii_art_macros` in `rude_client.py` reads each `*.txt` in that folder with `aiofiles` and stores the whole text in `self.ASCII_ART_MACROS[name]`. Other extensions are ignored.
3. Colour and format with literal text. `\x03` followed by a colour number, `\x02` for bold, `\x0F` to end formatting. They're written as four visible characters in the file, for example `\x0304`. `escape_color_codes` turns each `\xNN` into the real control character just before sending. The regex decodes one byte as UTF-8, so a value above `\x7F` would raise an error. The shipped `Resources/Splashes` files show the style. Macros such as `fedora.txt` and `Windows.txt` use it too.
4. Know how it sends. `cmd_mac` splits the text with `splitlines()` and sends one `PRIVMSG` per line, with a 0.4 second pause between lines. Long art takes time to send, and the code doesn't check line length against the IRC limit.
5. Load it. The macros are read when a client starts (the `load_ascii_art_macros` task that `RudeGui` creates for each client). To pick up a new file without a restart, use Chat > Reload Macros. That menu action calls `RudeGui.reload_macros`, which runs `update_available_macros` on the currently selected client only. With several servers, reload on each one.
6. Run `/mac` with no argument to list the names, then `/mac <name>` to send.

Packaging: `pyproject.toml` ships `Resources/Macros/*`, and `RudeChat.spec` and the CI both copy the folder, so a new file in this folder needs no build changes.

## A fortune file

1. Create `src/rudechat4/Resources/Fortunes/<name>.txt`.
2. Separate entries with a line that holds only `%`. The code does `f.read().strip().split('%')` and picks one entry at random with `random.choice`. A `%` inside an entry splits it, so avoid that character in the text. Look at `dadjoke.txt` for the layout: each entry starts after a `%` line.
3. Use it. `/fortune <name>` sends one entry, one `PRIVMSG` per line. `/cowsay <name>` sends it inside a cow bubble. `/fortune` and `/cowsay` with no name pick a random file from the folder. `get_fortune_file` in `rude_client.py` does the file choice.
4. Beware of name clashes. In `cmd_cowsay`, an argument that matches a fortune file name is treated as a fortune list. Anything else becomes the text for the cow. A list named `hello` would make `/cowsay hello` print a fortune.
5. `cmd_fortune` doesn't appear to check that the file exists, so a mistyped name looks like it would raise `FileNotFoundError` there. I didn't confirm what the user sees.
6. Add the list to the "Fun" help text in `display_help` if you want users to find it. The help text names the shipped lists by hand.

## A splash

Splashes are the art shown when you start the app and when you switch servers.

1. Create `src/rudechat4/Resources/Splashes/<anything>.txt`. The shipped ones are named `rude_splash_N.txt`, but the code only looks for `.txt`.
2. Use the same `\xNN` escape style as macros. `show_startup_art` in `rude_gui.py` calls `escape_color_codes` on the file text and passes it to `insert_text_widget`.
3. `show_startup_art` lists the folder every time it runs, picks one file at random and logs an error if the folder is empty. It doesn't need a restart. Switch servers to see a new file.

The art appears at the top of the chat view, so check it at your usual window width.

## A custom sound

The code doesn't offer a sound-picker. It plays a fixed file.

1. The notification sound is `Resources/Sounds/Notification4.wav` (a 24-bit mono WAV, 48 kHz). `mac_trigger_sound` and `linux_trigger_sound` in `rude_client.py` build the path from that name. To change the sound, replace that file and keep the name and the WAV format, or edit the two functions.
2. Turn on `custom_sounds = True` in the `.rudeserver` file. With it off, macOS plays the system `Ping.aiff` and Linux writes a terminal bell.
3. `use_beep_noise` must be on as well. `trigger_beep_notification` only runs for a mention when it is.
4. Playback uses `afplay` on macOS and `paplay` on Linux. Both are checked with `shutil.which` first. The Windows path (`win_trigger_sound`) ignores `custom_sounds` and plays a `winsound.Beep` tone. A custom file has no effect there.
5. `/sounds` opens the folder in your file manager.

To add a new platform or a second sound, add a trigger method in `RudeChatClient` and a branch in `trigger_beep_notification`. The sound plays in a `threading.Thread`, so it doesn't block the GUI.

## A GUI config key

GUI settings live in `gui_config.ini` in the config folder. The sections are `Chat`, `Entry`, `Lists` and `Utility`. A key touches four places.

1. **Default file.** Add the key to the right section of [`DefaultConfig/gui_config.ini`](../src/rudechat4/DefaultConfig/gui_config.ini). This only helps new installs, because `CopyConfigs` copies the defaults when `~/.config/rudechat` is empty. Existing users have to add the line by hand.
2. **Read it.** In `RudeGui.read_config` in `rude_gui.py`, add a line in the `if os.path.exists(config_file)` branch, for example `self.my_key = config.getboolean('Utility', 'my_key', fallback=False)`. Add the same attribute with a literal default in the `else` branch, which is used when the file is missing. Both branches exist, so you need both lines.
3. **Show it in the editor.** In `RudeConfigGui.start` in [`GUI/rude_config_gui.py`](../src/rudechat4/GUI/rude_config_gui.py), add an entry to `label_map`: `'my_key': ['Label shown', 'bool']`. The second item picks the widget. The types the code handles are `bool` (a checkbox), `string`, `int` (a line edit with a two-digit mask, so values over 99 can't be typed) and `color` (a `RudeColorOption` with a picker). The editor builds a row for every key that is in the user's file, and `save_config` writes every row back, so the new key round-trips with no more code. `save_config` writes a fresh file, so comments in the user's `.ini` are lost.
4. **Use it.** Read `self.my_key` where it matters. If the key is a colour or font, apply it in `RudeGui.set_gui_theme`. The Apply button runs `read_config` and then `apply_settings`, and `apply_settings` calls `set_gui_theme`, so a style change shows without a restart. A behaviour flag needs no extra wiring, but any code that cached the old value won't see the change.

Do not skip step 3. The editor looks keys up with `self.label_map.get(option, option)`. For a key missing from the map, the lookup returns the key's own name, so `[0]` and `[1]` pick single characters. The `match` then finds no case and the row has no widget. I expect that to raise an error or reuse the previous row's widget, though I haven't tested it. Two keys are in this state today: `list_channel_select_bg` is read by `read_config` but has no map entry, and `highlight_all_nicknames` is in the map but nothing reads it. The README's "GUI Config Example" shows `[GUI]` and `[WIDGETS]` sections and keys such as `master_color`. `read_config` doesn't read those, so the README example is out of date for this file.

Pop-out windows and other windows read attributes from the main `RudeGui`, for example `self.gui.tab_complete_terminator`. If a pop-out needs your value, it must reach it through `parentGui` or `gui`, and the code won't copy it for you.

## A server config key

Server settings live in `<name>.rudeserver`, section `[IRC]`. The README lists the keys.

1. **Default file.** Add the key and a safe default to [`DefaultConfig/libera.rudeserver`](../src/rudechat4/DefaultConfig/libera.rudeserver). Same caveat as above: it only seeds an empty config folder.
2. **Read it at connect time.** In `RudeChatClient.read_config` in `rude_client.py`, add `self.my_key = config.getboolean('IRC', 'my_key', fallback=False)` with the right getter. Use a fallback so old files still load. That method is a coroutine that runs when the client is set up.
3. **Reload it when the user clicks Apply.** `RudeChatClient.reload_config` repeats a subset of those reads. `RudeGui.open_client_config_window` calls it after the server editor closes. Add your line there if the setting should take effect without a reconnect. Connection settings such as `server`, `port`, `ssl_enabled`, `nickname` and the NickServ, SASL and ZNC fields aren't in `reload_config`, so changes to those need a reconnect or restart. I didn't test which one.
4. **Show it in the editor.** Add the key to `label_map` in `RudeConfigServer.start` in [`GUI/rude_config_server.py`](../src/rudechat4/GUI/rude_config_server.py). It uses the same types as the GUI editor, plus `channels` (used only for `auto_join_channels`, which opens a channel list editor). The same missing-key problem applies.
5. **Special case.** `auto_away_minutes` isn't read in `read_config`. The `AutoAway` class in `Client/rude_auto_away.py` opens the file itself. If your key belongs to a helper class, follow that pattern and make the helper reload it from `reload_config`.
6. **Document it.** Add it to the "Server Config Example" in the README.

Existing `.rudeserver` files won't have the new key, so the editor won't show it until the user adds the line. The `fallback` in `read_config` keeps the app working in the meantime. `RudeUpdate.py` merges new keys from the shipped `libera.rudeserver` into old files, but only for the package folder it targets. See [build-and-release.md](build-and-release.md).

## A new widget in Components/

`Components/` holds small Qt subclasses used by `RudeGui`. See [pyqt.md](pyqt.md) for the existing ones.

1. Create `Components/rude_<name>.py`. Start with the shebang, then a module docstring, then the two star imports the other modules use:

   ```python
   #!/usr/bin/env python3
   """One line on what the widget is for."""
   from rudechat4.shared_imports import *
   from rudechat4.global_variables import *
   ```

   If a Qt class you need isn't exported, add it to the matching `from PyQt6...` block in [`shared_imports.py`](../src/rudechat4/shared_imports.py).
2. Subclass the Qt widget. Follow the list widgets: take `parent=None`, call `super().__init__(parent)`, and store the main window as `self.gui` when you need the active client (`self.gui.irc_client`). Use `Qt.ContextMenuPolicy.CustomContextMenu` and `customContextMenuRequested` for a right-click menu, as `RudeChannelListWidget` does.
3. Indent docstrings inside the class or function body, as [contributing-docs.md](contributing-docs.md) shows. The docstring commit on this branch left docstrings at column 0 in the existing `Components/`, `Client/` and `Util/` files, and those files don't parse. See [development.md](development.md). Don't copy that layout.
4. Import the class in `rude_gui.py`, next to the other `from rudechat4.Components...` lines.
5. Create it in `RudeGui.init_layout` and place it in `self.gridLayout` with `addWidget(widget, row, column, rowSpan, columnSpan)`. The current positions are in [pyqt.md](pyqt.md). Adjust stretch with `setRowStretch` if the new widget should share space.
6. Style it in `RudeGui.set_gui_theme` with `setStyleSheet`, using the existing config attributes or a new GUI config key (see above). Anything that needs the theme must be styled there, because `apply_settings` re-runs it after the user applies GUI settings.
7. Update the `Components/` table in [modules.md](modules.md) and the widgets table in [pyqt.md](pyqt.md).

Packaging: `setup.py` lists `rudechat4.Components` in `PKGS`, `pyproject.toml` ships `Components/*`, and `RudeChat.spec` copies `Components/*`. A new file in the existing folder needs no changes. A new subfolder (a new package) would need edits to all three, and a new folder under `Resources` needs an entry in the spec's `datas` and the `pyproject.toml` `package-data` list. CI copies all of `Resources` in one `--add-data`, so it needs no edit.

If the widget is used by pop-out windows too, pop-outs are built in `GUI/rude_popout.py` through `setupUi`, not through `init_layout`. You'd add it there separately.
