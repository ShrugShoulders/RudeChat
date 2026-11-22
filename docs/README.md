# RudeChat documentation

RudeChat is a Python IRC client with a PyQt6 GUI. It can connect to several IRC servers at once, keeps per-channel history, and supports ZNC, SASL, CTCP, ASCII art macros and pop-out windows.

These docs describe the code in `src/rudechat4`. The README in the repo root covers installing the app and the config file examples.

| Page | What it covers |
| --- | --- |
| [architecture.md](architecture.md) | How the app starts, how the GUI and IRC clients fit together, and how the Qt and asyncio loops share one thread |
| [modules.md](modules.md) | A reference for every package and module: what it holds and what it depends on |
| [pyqt.md](pyqt.md) | The Qt side only: window layout, custom widgets, signals, threads, event filters, shortcuts, styling, tray |
| [commands.md](commands.md) | Every slash command the input box accepts |
| [data-files.md](data-files.md) | Where RudeChat reads and writes files on disk |
| [contributing-docs.md](contributing-docs.md) | Docstring style and the checklist for documenting a module |

## Documentation status

Docs are being added module by module. Track progress in [modules.md](modules.md); the "Docstrings" column says which modules have inline documentation.

## Source of truth

The code wins. If a page here disagrees with the source, fix the page and note it in your commit message.
