# Known issues

Problems and oddities found by reading `src/rudechat4` at commit `174a20e` on the `RudeChat4.2` branch. Each item names the place in the code, what is wrong, and the likely effect. For how the pieces fit together, see [architecture.md](architecture.md) and [state-and-persistence.md](state-and-persistence.md). Terms are in [glossary.md](glossary.md).

## How to read this page

- **confirmed**: the code path was traced, and where a tool could check it (a parse, a `grep`, a `configparser` or `fnmatch` call) it was checked. Nothing here was run inside the live app, so "confirmed" describes the code, not an observed crash.
- **suspected**: the code points that way, but the trigger or the effect was not traced end to end.

Links use `file:line` and open the line in the file. Line numbers match commit `174a20e` and drift as the code changes.

## Security and data handling

| Status | Where | What is wrong | Likely impact |
| --- | --- | --- | --- |
| confirmed | [rude_client.py:3423](../src/rudechat4/rude_client.py#L3423) | `handle_upload` sends the chosen file's text to `https://bpa.st` and then posts the returned link into the current channel. The only prompt is the file picker. The file contents leave the machine. | Easy to leak private files by accident. Worth a Privacy review and a confirmation dialog. |
| confirmed | [Util/rude_logger.py:20](../src/rudechat4/Util/rude_logger.py#L20) | `RudeChat4.log` always logs at DEBUG with no rotation. Error lines include message text and nicknames. | The file grows without limit and holds personal data. See the "Sensitive data" section of [data-files.md](data-files.md). |

## Missing methods and attributes

These are real name errors: the code refers to something that is not defined. Most surface as an exception that is caught and logged, so the symptom is a feature that quietly does nothing.

| Status | Where | What is wrong | Likely impact |
| --- | --- | --- | --- |
| confirmed | [rude_client.py:2817](../src/rudechat4/rude_client.py#L2817) | `user_input_dm_message` tests `self.current_channel` against `channel_messages[server_name]` but then creates the list for `channel`. | If the two ever differ, the next line raises `KeyError`. It is normally masked because they match. |
| confirmed | [rude_client.py:467](../src/rudechat4/rude_client.py#L467), [681](../src/rudechat4/rude_client.py#L681) | In the ZNC sync fallback, line 467 sends every `NAMESTOKENS` entry to `prtcl_366`, including `353` replies. Line 681 loops over `token` but reads `tokens`, the last line parsed, for every entry. Line 669 does it correctly. | With ZNC and `use_auto_join` off, the user lists after sync can be empty or wrong. The effect was not reproduced. |

## Connection lifecycle

| Status | Where | What is wrong | Likely impact |
| --- | --- | --- | --- |
| confirmed | [rude_client.py:2410](../src/rudechat4/rude_client.py#L2410), [rude_gui.py:849](../src/rudechat4/rude_gui.py#L849) | `disconnect` sets `loop_running = False` but cancels nothing and does not close the socket. `client_connect` later overwrites `tasks` with new tasks and sets `loop_running = True`. Old loops that are still asleep (30 s to 20 min) see the flag true again and keep running. | Duplicate `keep_alive`, `auto_save` and similar loops after a quick disconnect and connect. Traced, not run. |
| confirmed | [rude_client.py:131](../src/rudechat4/rude_client.py#L131) | `reload_config` falls back to `'red'` and `'green'` and does not call `.lower()` on the two note colours. `read_config` ([98](../src/rudechat4/rude_client.py#L98)) uses `'#ff0000'` and `'#008000'` and lower-cases them. The list highlight code compares these strings with `QColor.name()`, which is lower-case hex. | After the server config window closes, a colour typed in capitals, or the named fallback, may stop matching, so highlights get overwritten. The match was not tested in the UI. |
| confirmed | [rude_client.py:70](../src/rudechat4/rude_client.py#L70), [226](../src/rudechat4/rude_client.py#L226) | Every `RudeChatClient` deletes all `*.lock` files at construction. `RudeGui.init_client` builds one extra client with no server config ([rude_gui.py:616](../src/rudechat4/rude_gui.py#L616)), and servers are built one after another. | A client created while another is mid-save can remove its lock. The window is small. |

## State and display

| Status | Where | What is wrong | Likely impact |
| --- | --- | --- | --- |
| confirmed | [rude_client.py:756](../src/rudechat4/rude_client.py#L756), [1534](../src/rudechat4/rude_client.py#L1534) | Nothing removes a channel from `detached_channels`. With ZNC, `notify_user_if_mentioned` re-attaches any channel in that list on each mention. `auto_attach` appends to `joined_channels` without a duplicate check ([1542](../src/rudechat4/rude_client.py#L1542)). | A channel detached once is added to the list again on every later mention, even when it is already listed. |
| suspected | [GUI/rude_popout.py:802](../src/rudechat4/GUI/rude_popout.py#L802) | The pop-out passes the already ANSI-coloured nickname to `save_message` as `sender`. `save_message` colours the sender again and looks the coloured string up in `nickname_colors`. | Saved pop-out lines may show the nickname in the fallback colour, with escape codes nested. |
| suspected | [rude_gui.py:1544](../src/rudechat4/rude_gui.py#L1544), [1445](../src/rudechat4/rude_gui.py#L1445) | Decoding runs in `QThreadPool` workers that all emit back to the main thread. Workers may finish in a different order from the one they started in. | A line could appear before an earlier one, for example a new message right after a channel switch redraws history. README lists "messages loading in the wrong order" as fixed. Not reproduced. |
| confirmed | [rude_client.py:1394](../src/rudechat4/rude_client.py#L1394), [1402](../src/rudechat4/rude_client.py#L1402) | The custom sound path is placed into `os.system(f"afplay {sound_path}")` without quotes. | An install path with a space breaks the sound. The path is not user-controlled, so this is not an injection route. |

## Blocking calls inside coroutines

All asyncio work shares the GUI thread (see [architecture.md](architecture.md#qt-and-asyncio-on-one-thread)), so anything below that waits freezes the window for the wait. There is no `time.sleep` anywhere in `src`.

| Status | Where | What is wrong | Likely impact |
| --- | --- | --- | --- |
| confirmed | [rude_client.py:3444](../src/rudechat4/rude_client.py#L3444) | `requests.post(...)` runs in a coroutine with no `timeout`. | The whole UI waits on the network, indefinitely if the host never answers. |
| confirmed | [rude_client.py:3424](../src/rudechat4/rude_client.py#L3424), [3436](../src/rudechat4/rude_client.py#L3436), [3460](../src/rudechat4/rude_client.py#L3460) | `handle_upload` opens `QFileDialog` and `QMessageBox` windows from inside a coroutine. Both run their own nested Qt loop. | Asyncio stops while a dialog is open. |
| suspected | [__main__.py:123](../src/rudechat4/__main__.py#L123) | While that nested Qt loop runs, the 100 ms `qt_update` timer can fire. It calls `loop.run_forever()` on a loop that is already running, which raises `RuntimeError`. The function has no `except`, so the error leaves a Qt slot. PyQt6 may abort the process on an unhandled slot exception. | A possible crash on Chat > Upload File. Not run. |
| confirmed | [rude_client.py:265](../src/rudechat4/rude_client.py#L265), [275](../src/rudechat4/rude_client.py#L275) | `save_channel_messages` uses `aiofiles` for the file I/O, but `json.loads` and `json.dumps(..., indent=2)` of the whole history still run on the loop thread, every 30 s per client. | A pause that grows with history size. Not measured. |
| confirmed | [rude_client.py:2325](../src/rudechat4/rude_client.py#L2325) | `log_message` opens, appends to and closes a file for every message sent or received. | A small stall per message, worse on slow disks. |
| confirmed | [rude_client.py:4680](../src/rudechat4/rude_client.py#L4680), [4692](../src/rudechat4/rude_client.py#L4692), [rude_gui.py:2057](../src/rudechat4/rude_gui.py#L2057) | `prtcl_353` calls `save_nickname_colors_bak()` and `save_nickname_colors()` for every new nickname in a NAMES list, and each call rewrites the whole JSON file. `update_nickname_colors` ([1733](../src/rudechat4/rude_client.py#L1733)) also reads and rewrites the backup on each JOIN. | Joining a busy channel with many unseen nicknames writes the file hundreds of times on the GUI thread. |
| confirmed | [rude_client.py:200](../src/rudechat4/rude_client.py#L200), [2098](../src/rudechat4/rude_client.py#L2098), [4634](../src/rudechat4/rude_client.py#L4634), [3173](../src/rudechat4/rude_client.py#L3173), [4891](../src/rudechat4/rude_client.py#L4891), [Client/rude_friends.py:32](../src/rudechat4/Client/rude_friends.py#L32) | Plain `open()` calls in `save_away_users_to_file`, `save_whois_to_file` (an `async def`), `prtcl_323`, `fortune_cowsay`, `cmd_fortune` and `RudeFriends`. `load_ignore_list` and `load_dm_list` ([3039](../src/rudechat4/rude_client.py#L3039), [3051](../src/rudechat4/rude_client.py#L3051)) do the same during `read_config`. | Small files, so short stalls. Listed for completeness. |

Sound playback uses `os.system` inside `threading.Thread`, and the file manager launch uses `subprocess.Popen`. Neither blocks the loop.

## Stale and duplicate code

| Status | Where | What is wrong | Likely impact |
| --- | --- | --- | --- |
| confirmed | [rude_gui.py:63](../src/rudechat4/rude_gui.py#L63), [GUI/rude_popout.py:79](../src/rudechat4/GUI/rude_popout.py#L79) | Two different classes named `TabEventFilter`. The pop-out copy has its own `command_list` and takes `(parent, gui)`. | A bug fixed in one copy stays in the other. Check the import path. |
| confirmed | [rude_gui.py:167](../src/rudechat4/rude_gui.py#L167), [GUI/rude_popout.py:140](../src/rudechat4/GUI/rude_popout.py#L140) | Two classes named `ArrowKeyEventFilter`. | Same. |
| confirmed | [Components/rude_user_list_widget.py:6](../src/rudechat4/Components/rude_user_list_widget.py#L6), [GUI/rude_popout.py:7](../src/rudechat4/GUI/rude_popout.py#L7) | Two classes named `RudeUserListWidget`. `rude_gui.py` star-imports the `Components` one ([line 11](../src/rudechat4/rude_gui.py#L11)). The pop-out copy is the one calling the missing `whois` and `handle_kick_command`. | The copies have already drifted apart. |
| confirmed | [rude_gui.py:1570](../src/rudechat4/rude_gui.py#L1570), [GUI/rude_popout.py:426](../src/rudechat4/GUI/rude_popout.py#L426) | `decoder`, `tag_text`, `configure_tag_based_on_attributes`, `tag_urls`, `find_urls` and the `irc_colors` table are duplicated between `RudeGui` and `RudePopout`. `escape_color_codes` is also in the client ([2916](../src/rudechat4/rude_client.py#L2916)) and the GUI ([1306](../src/rudechat4/rude_gui.py#L1306)). | Formatting fixes need to be made twice. |
| confirmed | `build/lib/rudechat4` | A copy of the package from an earlier build. `.gitignore` line 7 ignores it and `git ls-files build` lists nothing, so it exists only on this machine. It matches `src` except for 14 module files (the same 14 that fail to parse) and `rude_client.py`, which still has the `/ch` help line and an older log message. `rude_gui.py` and `__main__.py` are identical. | Reading or running the wrong tree gives different behaviour. It is also the last copy that imports. Delete or rebuild it once the docstring fix lands. |
| confirmed | [Components/rude_server_list_widget.py:6](../src/rudechat4/Components/rude_server_list_widget.py#L6), [rude_gui.py:374-385](../src/rudechat4/rude_gui.py#L374) | `RudeServerListWidget` is never created. The call sites are commented out, and the server picker is a `QComboBox` (`server_selector_box`). More commented-out styling for it is at [541](../src/rudechat4/rude_gui.py#L541), [580](../src/rudechat4/rude_gui.py#L580) and [590](../src/rudechat4/rude_gui.py#L590). | Dead widget and dead comments. |
| confirmed | [rude_gui.py:599](../src/rudechat4/rude_gui.py#L599), [605](../src/rudechat4/rude_gui.py#L605), [608](../src/rudechat4/rude_gui.py#L608), [611](../src/rudechat4/rude_gui.py#L611), [rude_client.py:29](../src/rudechat4/rude_client.py#L29), [46](../src/rudechat4/rude_client.py#L46), [47](../src/rudechat4/rude_client.py#L47), [51](../src/rudechat4/rude_client.py#L51) | Attributes that are set and never read: `url_cache`, `emoji_width_cache`, `last_selected_index`, `target_user_info`, `channel_lists` and `server_var` on the GUI. `mode_keys`, `client_event_loops`, `tasks`, `decoder` and `encoder` on the client. `tag_cache` on the GUI is written and never read. | Noise. `tag_cache` and `motd_dict` also grow without limit. |

## Swallowed errors

About 150 `except Exception` blocks cover the code. Most log through `logging.error`, so a failure shows up only in `RudeChat4.log` and never in the chat window. The ones that hide the most:

| Status | Where | What is wrong | Likely impact |
| --- | --- | --- | --- |
| confirmed | [GUI/rude_config_gui.py:180](../src/rudechat4/GUI/rude_config_gui.py#L180) | `except Exception as e: pass` around the rename of a config file path. | A bad server name can leave the editor writing to the old file with no message. |
| confirmed | [GUI/rude_config_server.py:67](../src/rudechat4/GUI/rude_config_server.py#L67) | The only bare `except:` in the source. It catches `KeyboardInterrupt` and `SystemExit` too. | Low. It only wraps a widget removal. |
| confirmed | [rude_gui.py:1788](../src/rudechat4/rude_gui.py#L1788), [GUI/rude_popout.py:621](../src/rudechat4/GUI/rude_popout.py#L621), [GUI/rude_colours.py:182](../src/rudechat4/GUI/rude_colours.py#L182) | `except ValueError: pass`. | A bad colour value is skipped silently. |
| confirmed | [rude_client.py:1262](../src/rudechat4/rude_client.py#L1262), [1270](../src/rudechat4/rude_client.py#L1270) | `except (AttributeError, Exception)`. `AttributeError` is already an `Exception`. | Redundant, and a sign the real error was never found. |
| confirmed | [rude_client.py:2274](../src/rudechat4/rude_client.py#L2274) | The main dispatch wraps every handler in one `except Exception` that logs and moves on. | One bad handler never stops the loop, but errors in a handler are easy to miss. |
| confirmed | [rude_gui.py:628](../src/rudechat4/rude_gui.py#L628), [rude_client.py:2338](../src/rudechat4/rude_client.py#L2338) and others | Fire-and-forget `loop.create_task(...)` calls keep no reference and no done-callback (see the task list in [state-and-persistence.md](state-and-persistence.md#tasks-nobody-tracks)). Exceptions inside them print "Task exception was never retrieved" at best. | Failures in `leave_channel`, `save_dm_list` and the context-menu actions are not logged by the app. |
