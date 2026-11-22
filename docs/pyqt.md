# PyQt6 in RudeChat

This page covers only the Qt side of the code: widgets, layouts, signals, threads, styling and platform quirks. For the IRC side, see [architecture.md](architecture.md).

RudeChat uses PyQt6. All Qt names come in through `from rudechat4.shared_imports import *`, which imports from `PyQt6.QtWidgets`, `PyQt6.QtCore` and `PyQt6.QtGui`. If a Qt class looks undefined in a module, check [`shared_imports.py`](../src/rudechat4/shared_imports.py) first, and add the import there if it's missing.

## Window structure

```
QApplication                      __main__.py
└─ Window (QMainWindow)           __main__.py: menu bar, close handling
   └─ RudeGui (QWidget)           rude_gui.py: central widget, QGridLayout
      ├─ topic_label              QLabel
      ├─ chat_box                 RudeTextBrowser
      ├─ id_label                 QLabel ("Nickname | #Channel")
      ├─ text_field               RudeMessageEntry
      ├─ user_selector_label      QLabel
      ├─ user_selector_list       RudeUserListWidget
      ├─ channel_selector_label   QLabel
      ├─ channel_selector_list    RudeChannelListWidget
      └─ server_selector_box      QComboBox
```

`RudeGui.init_layout` places these in one `QGridLayout`. Rows and columns are `(row, column, row span, column span)`:

| Widget | Position |
| --- | --- |
| `topic_label` | 0, 0, 1 x 2 |
| `chat_box` | 1, 0, 3 x 2 |
| `id_label` | 4, 0 |
| `text_field` | 4, 1 |
| `user_selector_label` | 0, 2 |
| `user_selector_list` | 1, 2 |
| `channel_selector_label` | 2, 2 |
| `channel_selector_list` | 3, 2 |
| `server_selector_box` | 4, 2 |

Rows 1 and 3 have stretch 1, so the chat area and the two lists share the spare height. A `RudeServerListWidget` exists but its use in `init_layout` is commented out. A combo box replaced it.

`Window` owns the menu bar (Chat, Colors, Config, plus an App menu on macOS). `RudeGui.__init__` connects those actions to its own methods, for example `chat_clear_chat_action.triggered` to `clear_chat_window`.

## Custom widgets

| Class | Base | File | Notes |
| --- | --- | --- | --- |
| `RudeTextBrowser` | `QTextBrowser` | `Components/rude_text_browser.py` | Turns off `setOpenLinks` and opens links with `webbrowser.open` on left click |
| `RudeMessageEntry` | `QLineEdit` | `Components/rude_message_entry.py` | Formatting shortcuts and a Colors and Formatting context menu |
| `RudeUserListWidget` | `QListWidget` | `Components/rude_user_list_widget.py` | Context menu: DM, whois, ignore, unignore, kick, user data |
| `RudeChannelListWidget` | `QListWidget` | `Components/rude_channel_list_widget.py` | Context menu: leave or close, pop out |
| `RudeServerListWidget` | `QListWidget` | `Components/rude_server_list_widget.py` | Context menu: connect, disconnect |
| `RudeColorOption` | `QWidget` | `Components/rude_color_option.py` | Line edit plus a button that opens `QColorDialog` |

The list widgets all take the `RudeGui` as `parent`, store it as `self.gui`, and reach the IRC client through `self.gui.irc_client`. They use `Qt.ContextMenuPolicy.CustomContextMenu` and connect `customContextMenuRequested` to their own `show_context_menu`.

`RudePopout` in `GUI/rude_popout.py` is a `QObject`, not a widget. It builds a Designer-style UI into a plain `QWidget` through `setupUi(Form)`. `RudeGui.open_pop_out_window` creates the `QWidget`, creates the `RudePopout`, calls `setupUi`, and stores `[window, ui]` in `self.pop_out_windows` so Python keeps them alive. If you drop that reference, the window is garbage collected.

## Signals and slots

Where the code uses Qt signals:

- **Widget signals:** `itemClicked` on the channel list calls `on_channel_click`. `currentIndexChanged` on the server combo box calls `on_server_change`. `returnPressed` on the input box starts the async handler (see below). `triggered` on menu and tray `QAction`s calls GUI methods.
- **Custom signals:** `BatchDecoderWorkerSignals` in `rude_gui.py` defines `message_decoded = pyqtSignal(list, list)` and `finished = pyqtSignal()`. They are on a separate `QObject` because a `QRunnable` can't carry signals itself.
- **Auto-connect:** `RudePopout.setupUi` calls `QMetaObject.connectSlotsByName(Form)`, the standard Designer call that connects slots named `on_<objectName>_<signal>`. I didn't check whether any slot in the pop-out relies on it.

## Threads

The GUI runs on the main thread. There are two ways work leaves it.

**Asyncio on the main thread.** Network code is `async` and runs on the asyncio loop that `__main__` pumps from a `QTimer` every 100 ms. See [architecture.md](architecture.md). GUI code starts coroutines with `loop.create_task(...)`. For example, `RudeGui.bind_return_key` connects `text_field.returnPressed` to a lambda that creates a task for `on_enter_key`. Because both run on one thread, Qt calls and `await`ed code can touch widgets directly.

**Text decoding in a thread pool.** Turning IRC control codes into formatted Qt text is slow for long histories, so `BatchDecoderWorker` (a `QRunnable`) does it off the main thread:

1. `display_last_messages` and similar methods build a `BatchDecoderWorker` with the messages, `self.decoder` and `self.find_urls`.
2. `worker.signals.message_decoded` is connected to `self.handle_decoded_text`.
3. `QThreadPool.globalInstance().start(worker)` runs it.
4. For each message the worker emits `message_decoded(formatted_text, urls)`. Because the receiver lives on the main thread, Qt queues the call, and `handle_decoded_text` runs there.
5. `handle_decoded_text` calls `tag_text` and `tag_urls`, which insert the text into the chat view.

Rule: only the main thread touches widgets. The worker only builds data (`QTextCharFormat` lists and URL strings) and emits it.

## Event filters

Event filters are `QObject`s installed on the input box with `installEventFilter`. Returning `True` from `eventFilter` swallows the event.

| Filter | Purpose |
| --- | --- |
| `TabEventFilter` | Tab completes `/commands` (if the cursor is in the first word) and nicknames from the user list. Uses `gui.tab_complete_terminator` after a nickname at the start of a line. |
| `ArrowKeyEventFilter` | Up and Down walk through `entry_history` |
| `EnterFilter` (pop-out only) | Handles Enter in a pop-out input box |

The main window and the pop-out each have their own `TabEventFilter` and `ArrowKeyEventFilter` classes. They're separate classes with the same names, one in `rude_gui.py` and one in `GUI/rude_popout.py`.

The tab-complete command list in `TabEventFilter.command_list` is a hard-coded copy. Add new slash commands there as well as in `command_parser`. See [commands.md](commands.md).

## Shortcuts

Registered with `QShortcut` in `RudeGui.set_shortcuts` and `RudeMessageEntry.add_shortcuts`:

| Keys | Action | Where |
| --- | --- | --- |
| Ctrl+] / PgDown | Next channel | `RudeGui` |
| Ctrl+[ / PgUp | Previous channel | `RudeGui` |
| Ctrl+Shift+\ | Next server | `RudeGui` |
| Ctrl+W | Open GUI config window | `RudeGui` |
| Ctrl+E | Open server config window | `RudeGui` |
| Ctrl+B / Ctrl+I | Bold, italic | `RudeMessageEntry` |
| Ctrl+U (macOS, Windows) or Ctrl+N (Linux) | Underline | `RudeMessageEntry` |
| Ctrl+S | Strike-through | `RudeMessageEntry` |
| Ctrl+/ | Inverse | `RudeMessageEntry` |

Formatting shortcuts only act on selected text. They wrap it in the IRC control code and add a reset (`\x0F`) after it.

## Styling and theming

Theme values come from `gui_config.ini`, which `RudeGui.read_config` reads. `RudeGui.set_gui_theme` then builds Qt style sheets from f-strings and applies them with `setStyleSheet` on the main window, `chat_box`, `text_field`, `user_selector_list`, `channel_selector_list` and the labels.

- Font family and sizes come from the `[GUI]` section. Widget colours come from `[WIDGETS]`.
- `ChannelListWindow` and `RudePopout` build their own style sheets from values on the parent `RudeGui`, such as `gui.scrollbar_bg`.
- The selected-channel colour is appended to the channel list style sheet as `selection-background-color`.

The `irc_colors` dict on `RudeGui` (and on `RudePopout`) maps IRC colour codes `00` to `98` to hex values. The decoder uses it when it builds `QTextCharFormat` objects.

## System tray

`create_tray_icon` builds a `QSystemTrayIcon` with a Show and Quit menu.

- `send_to_tray` hides the main window and shows a balloon message. It does nothing when `minimize_to_tray` is false.
- `restore_from_tray` shows, raises and activates the window.
- `trigger_desktop_notification` uses `tray_icon.showMessage` for mentions and DMs. It skips the notification when `QApplication.activeWindow()` is not None, meaning the app is in focus.
- `Window.closeEvent` calls `event.ignore()` and `send_to_tray()` when `minimize_to_tray` is on, so the close button hides the window instead of quitting.

## Config and secondary windows

- **`RudeConfigGui`** is a `QScrollArea` that builds a form from `label_map`. Each entry maps a config key to a label and a type (`color`, `string`, `int` and so on). `RudeConfigServer` extends it for `.rudeserver` files.
- **Opening a config window:** `open_client_config_window` and `open_gui_config_window` in `RudeGui`. When the window closes, a `QTimer.singleShot(100, ...)` reloads config and `QTimer.singleShot(200, ...)` closes the window.
- **`FirstRun`** shows the server config window before the main window is created. It calls `self.app.exec()` itself, so it runs a nested Qt event loop at startup.
- **`ChannelListWindow`** is a `QDialog` with a `QTreeWidget` of `/list` results. A `QTimer` fires every 100 ms to refill the tree while results arrive.

## Platform notes

- **macOS:** `shared_imports.py` imports `lookUpClass` from `objc` only when `platform.system() == "Darwin"`. `Window.show_mac_about_panel` uses it to show the native About panel. The menu bar uses `setNativeMenuBar(True)`. The app builds as a `.app` with py2app. Clicking the app in the Dock doesn't reopen a hidden window yet (listed in the README to-do).
- **Windows and Linux:** the underline shortcut differs (Ctrl+U or Ctrl+N), and `ICON_FILE` in `global_variables.py` picks an `.ico` or `.png` by platform.
- **Window size:** `RudeGui.set_screen_size` starts the window at half the primary screen's width and height, falling back to 800 x 600.

## Pitfalls

- Keep references to top-level widgets you create (pop-outs, config windows, dialogs). Qt doesn't keep Python objects alive for you.
- Don't block inside a coroutine. The Qt event loop and the asyncio loop share one thread, so a blocking call freezes the whole UI.
- Don't touch widgets from `BatchDecoderWorker.run`. Emit a signal instead.
- `shared_imports` is a star import. Adding a Qt class to a module without adding it there causes a `NameError` at runtime, not at import.
