# Text formatting

This page follows a chat line from IRC text to coloured, linked text in the chat view. It also covers the helpers that change text on the way in and out: nickname colours, green text, emoji, the pronoun filter, `/mock`, cowsay, fortunes and ASCII art macros. For the Qt widgets themselves see [pyqt.md](pyqt.md). For the settings that switch these features on and off see [configuration.md](configuration.md). For the slash commands see [commands.md](commands.md).

Line numbers refer to the files under `src/rudechat4`. They drift as the code changes, so search for the function name if a number is off.

## The pipeline in one pass

1. **Receive.** `handle_incoming_message` in `rude_client.py` reads bytes, decodes them as UTF-8 (bad bytes dropped) and removes four things: the sequences `ESC[?25h` and `ESC[?7h`, `\x06` and the bell character (line 2186). If `use_irc_colors` is `False` (the code's default), it also strips every `\x03` colour code with a regex (line 2190). Bold, italic and the other control codes stay.
2. **Handle.** `prtcl_PRIVMSG` runs `replace_emojis` and then `green_texter` on the message text (lines 4481 and 4484). Nicknames in the text get wrapped in ANSI colour sequences by `color_message_mentions`, and the sender's name by `ansi_color_nickname`.
3. **Display.** `RudeGui.insert_text_widget` hands the finished string to a `BatchDecoderWorker`. The worker calls `RudeGui.decoder` (turns control codes and ANSI into Qt formats) and `find_urls` on a thread-pool thread. The GUI thread then inserts the text with `tag_text` and links URLs with `tag_urls`. The threading model is in [pyqt.md](pyqt.md#threads).

On the way out, `handle_user_input` runs `escape_color_codes` and the pronoun filter. `send_message_chunks` then runs `replace_emojis` and `green_texter` before the line goes to the server.

Chat content is personal data. When you share screenshots, logs or saved history from RudeChat, remove nicknames and hostmasks, or use made-up ones. See [data-files.md](data-files.md#sensitive-data).

## IRC control codes

The control characters are defined by value in the decoder (`rude_gui.py:1570`). `global_variables.py` also lists them for the input box menu.

| Code | Name | What the decoder does |
| --- | --- | --- |
| `\x02` | Bold | Toggles bold |
| `\x1D` | Italic | Toggles italic |
| `\x1F` | Underline | Toggles underline |
| `\x1E` | Strike through | Toggles strike-out |
| `\x16` | Inverse | Swaps the current foreground and background |
| `\x03` | Colour | Sets colours. Format: `\x03` then up to two digits, then optionally `,` and up to two more digits |
| `\x0F` | Reset | Clears all attributes and colours |

Details worth knowing:

- **Toggles.** Each bold, italic, underline and strike code flips the state. Two bold codes in a row cancel each other.
- **State is per call.** The decoder keeps its state in local variables, so formatting never carries over from one message to the next.
- **A colour code with no digits.** A bare `\x03` sets the foreground to colour 0 (white) instead of clearing colour (`rude_gui.py:1743`). Most clients treat a bare `\x03` as "reset colours". RudeChat's own colour menu ends a coloured selection with a bare `\x03` (`Components/rude_message_entry.py`, `apply_irc_color`), so any text typed after the selection shows white in RudeChat's own display until a reset code.
- **Background resets.** A `\x03` code that names a foreground but no background resets the background to the default. Some other clients keep the old background.
- **Inverse on default colours.** Inverse swaps the two stored colours. If both are still the default, the swap changes nothing, so inverse text with no explicit colours looks normal.
- **Colour index 99.** The table has no entry for 99, so it falls back to the default text colour.
- **Defaults.** When the foreground or background is "default", the decoder doesn't set a colour at all. The chat view's own style sheet colours (`chat_fg`, `chat_bg`) show through.

### Colour tables

There are three places that define colours. They don't line up by name.

| Table | File | Contents | Used by |
| --- | --- | --- | --- |
| `irc_colors` | `rude_gui.py:195`, copy at `GUI/rude_popout.py:180` | Two-digit string `'00'` to `'98'` mapped to a hex colour | The decoder, for IRC colour codes |
| `IRC_COLORS` | `global_variables.py:108` | Name mapped to a two-digit code, for example `"Red": "04"` | The Colors submenu in the input box (`Components/rude_message_entry.py:47`) |
| `IRC_FORMAT` | `global_variables.py:9` | Label and control character for bold, italic, underline, strike through and inverse | The Formatting submenu |

`irc_colors` holds 99 entries. Codes 0 to 15 are the classic 16 colours:

| Code | Hex | Code | Hex | Code | Hex | Code | Hex |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 00 | `#ffffff` | 04 | `#AA0000` | 08 | `#FFFF00` | 12 | `#2576ff` |
| 01 | `#000000` | 05 | `#AA5500` | 09 | `#00ff00` | 13 | `#ff00ff` |
| 02 | `#0000AA` | 06 | `#AA00AA` | 10 | `#00AAAA` | 14 | `#AAAAAA` |
| 03 | `#00AA00` | 07 | `#FFAA00` | 11 | `#00FFAA` | 15 | `#D3D3D3` |

Codes 16 to 87 are the extended palette, a set of 72 colours that runs from dark shades (16 to 51) through saturated ones (52 to 63) to pale tints (64 to 87). Codes 88 to 98 are a greyscale ramp from `#000000` to `#ffffff`. The complete list is in `rude_gui.py` lines 195 to 226.

**The names in the Colors menu don't describe the colours for codes 16 and up.** `IRC_COLORS` gives code 16 the name "Navy Blue", but `irc_colors['16']` is `#470000`, a dark red. Codes 0 to 15 look consistent, though some names are approximate ("Brown" is `#AA5500`). Trust the hex table, not the menu labels, when you want a specific colour.

The input box menu groups the names in tens (`00-09`, `10-19` and so on) and inserts `\x03<code><selected text>\x03`. Formatting shortcuts insert `<code><selected text>\x0F` and only act on selected text.

## ANSI escape sequences

RudeChat uses ANSI internally for one job: colouring nicknames in 24-bit colour. The decoder also understands ANSI sent by other people, so ANSI art and coloured bot output display.

The decoder only handles SGR sequences, which look like `ESC[...m`. When it sees `ESC[` it reads numbers separated by `;` or `:` up to the next `m`. If it reaches the end of the text without an `m`, it drops the `ESC` and shows the rest as plain text (`rude_gui.py:1599`). Other sequences, such as cursor moves, aren't interpreted. Because the parser looks for the next `m` anywhere in the text, a non-SGR sequence can swallow text up to a later letter m. The two sequences the receive loop strips (see step 1 above) are the ones RudeChat's author seems to have hit in practice.

| SGR code | Effect |
| --- | --- |
| `0` | Reset everything |
| `1`, `3`, `4`, `9` | Bold, italic, underline, strike-out on |
| `22`, `23`, `24`, `29` | Bold, italic, underline, strike-out off |
| `7` | Swap foreground and background |
| `27` | Ignored (the code comments say undoing inverse is hard) |
| `30` to `37`, `90` to `97` | Foreground from `ANSI_TO_IRC_MAP` |
| `40` to `47`, `100` to `107` | Background from `ANSI_TO_IRC_MAP` |
| `39`, `49` | Default foreground, default background |
| `38;5;N`, `48;5;N` | 256-colour foreground, background (N is 0 to 255) |
| `38;2;R;G;B`, `48;2;R;G;B` | 24-bit foreground, background |

Everything else (dim, blink and so on) is ignored.

### `ANSI_TO_IRC_MAP`

`ANSI_TO_IRC_MAP` in `global_variables.py:17` maps the 16 basic ANSI colours to IRC colour indexes. The same numbers serve foreground (30 to 37, 90 to 97) and background (40 to 47, 100 to 107). The result is looked up in `irc_colors`.

| ANSI colour | Dark (30 to 37) | Bright (90 to 97) |
| --- | --- | --- |
| Black | 01 | 08 |
| Red | 04 | 05 |
| Green | 03 | 09 |
| Yellow | 07 | 11 |
| Blue | 02 | 12 |
| Magenta | 06 | 13 |
| Cyan | 10 | 11 |
| White | 14 | 00 |

The comments above the table in `global_variables.py` list different numbers for yellow (`08`) than the values below them (`07` for dark yellow). The values are what the code uses. The mapping also sends bright black to `08` (yellow in `irc_colors`) and bright cyan to `11`, the same as bright yellow, which looks unintentional.

### `ANSI_256_COLOR_MAP`

`ANSI_256_COLOR_MAP` in `global_variables.py:36` maps colour numbers 0 to 255 straight to hex. It follows the standard xterm layout: 0 to 15 are the system colours, 16 to 231 are a 6 by 6 by 6 colour cube, and 232 to 255 are a 24-step grey ramp. The decoder uses it for `38;5;N` and `48;5;N` (`rude_gui.py:1822`). An index missing from the map becomes `gray`. Key 253 is written `#dadaDA`, which Qt reads fine.

### 24-bit colour

`38;2;R;G;B` builds a `QColor` straight from the three numbers. The check for a complete sequence uses `j + 4 <= len(codes)` where it likely needs `<` (`rude_gui.py:1680`, `GUI/rude_popout.py:523`). A truncated sequence such as `38;2;10;20` can raise an `IndexError`. `BatchDecoderWorker.run` catches the error and logs it, and the whole message is dropped. I didn't run this to confirm.

## Pop-out decoders

`GUI/rude_popout.py` has its own copy of the decoder (line 426) and `irc_colors` table. The copy differs slightly from the main one: it uses `isdigit()` instead of an ASCII-only check, so other Unicode digits count, and it doesn't have the unterminated-sequence guard. Fix a bug in both places, or expect the two to disagree.

## Nickname colouring

Each nickname gets one hex colour, stored in `nickname_colours.json` in the config folder. It maps nickname to `#rrggbb`.

### Choosing a colour

- `generate_random_color` (`rude_gui.py:1900`) picks random red, green and blue values between 50 and 255 and retries until the spread between the highest and lowest channel is over 50. This keeps colours bright and not grey.
- Your own nickname uses `main_nickname_color` from `[Utility]`.
- When `generate_nickname_colors` is `False`, every nickname gets `window_fg`.

`update_nickname_colors` (`rude_client.py:1733`) assigns a colour when someone joins and moves the colour to the new name on a nick change. `prtcl_353` (line 4670) does the same for every name in a NAMES list, and it also writes the backup file.

### Saving and the backup file

- `save_nickname_colors` writes `nickname_colours.json` after passing the dictionary through `clean_nicknames`.
- `nickname_colours_bak.json` keeps the real colours. `save_nickname_colors_bak` writes it, and `update_bak_file` adds any nickname the backup is missing.
- `load_nickname_colors` (`rude_gui.py:1983`) handles the switch between modes. With generation off, it returns the saved names all set to `window_fg` and leaves the backup alone. With generation on, it reads the main file. If the first nickname's colour equals `window_fg`, it assumes the file was overwritten while generation was off and loads the backup instead. If there's no backup, it generates new random colours. This "first entry" check is a heuristic. A genuine first entry that happens to equal `window_fg` triggers it.

### `nick_cleaner`

`Util/nick_cleaner.py` keeps junk out of `nickname_colours.json`. `is_valid_nickname` rejects names that:

- contain a space, comma, `*`, `?` or `!`,
- start with `$`, `:`, `#` or `&`,
- contain a `.`.

An empty string raises `IndexError`. `clean_nicknames` returns a new dictionary that keeps only valid names. The rule means a nickname with a dot (rare, but legal on some networks) keeps a colour in memory for the session but never reaches the file.

### Editing colours by hand

The Colors menu opens `RudeColours` (`GUI/rude_colours.py`), a table of nicknames and colours with Add, Edit and Delete buttons. It writes `nickname_colours.json` directly and then reloads the colours into the GUI. `NickEditor` has a free text colour field and a colour picker.

Only `#rrggbb` values work for display. `ansi_color_nickname` strips a leading `#` and requires exactly six hex digits. A colour name such as `red` fails that check and the nickname shows with no colour. The editor doesn't validate the text you type.

### Applying the colour: `ansi_color_nickname`

`ansi_color_nickname` (`rude_client.py:1762`) looks up the nickname case-insensitively, converts the hex colour to red, green and blue, and returns `ESC[38;2;R;G;Bm<nickname>ESC[0m`. If there's no stored colour it uses `window_fg`. The decoder then draws that as 24-bit colour. The trailing `ESC[0m` resets everything, so a message that was bold before the nickname loses its bold afterwards.

The sent text isn't coloured. `color_message_mentions` (line 4427) runs after the line goes out, for local display and history only. It wraps every nickname in the current channel's user list that appears in the message. It matches whole words, ignores case, and skips matches next to a `.` or `/` (so it doesn't colour parts of file names or URLs).

## Green text

`green_texter` (`rude_client.py:1415`) wraps a line in `\x0303` and `\x0F` when it starts with one of these: `>`, `»`, `→`, `⇒`, `↣`, `➜`, `➤`, `➡`, `➝`, `➞`, `➟`, `➠`, `->` or `=>`. IRC colour 03 renders as `#00AA00`.

It's controlled by `green_text` (code default `True`). It runs on incoming messages, and also on lines you send, so other users see the green code on the wire. Since it runs after the colour-stripping in the receive loop, the added green code survives even when `use_irc_colors` is `False`. A server's own `\x03` codes don't.

## Emoji replacement

`replace_emojis` (`rude_client.py:1425`) does two things:

1. **Smileys.** When `use_emojis` is `True`, it replaces about 70 text emoticons such as `:)`, `:D`, `<3`, `:P` and `xD` with Unicode emoji. A match needs whitespace or the start of the text before it, and whitespace, the end of the text or `.`, `,`, `?`, `!` after it. The patterns run one at a time in dictionary order, so earlier entries win on overlaps.
2. **Aliases.** It then runs `emoji.emojize(message, language="alias")`, which turns names like `:smile:` into emoji. This step runs even when `use_emojis` is `False`. In that branch, an exception returns `None` (the other branch returns the text unchanged). A `None` would break later string handling.

It runs on incoming channel and direct messages and on lines you type. It doesn't run on `/me`, `/mock`, notices or macros.

## URL detection and tagging

`self.url_pattern` (`rude_gui.py:612`, copied in the pop-out at `GUI/rude_popout.py:208`) matches:

- anything of the form `scheme://...`, and
- anything starting with `www.`.

A match runs until whitespace, `(`, `)`, `<` or `>`, with two refinements: balanced round brackets inside a URL are allowed (so Wikipedia links work), and a trailing `.`, `,`, `;`, `!` or `?` isn't part of the match.

`find_urls` runs in the worker thread on the raw message. `tag_urls` (`rude_gui.py:1854`) then runs on the GUI thread. For each URL it builds a `QTextCharFormat` with the anchor set, `url_color` as the colour and underline on. It searches the whole chat document for that URL string and merges the format into every match, so older copies of the same link get linked too. Each URL needs a full document search, so a very long chat history with many links is slower to tag.

`RudeTextBrowser` (`Components/rude_text_browser.py`) turns off Qt's own link handling. A left click on an anchor calls `webbrowser.open`. A `www.` link has no scheme, so it's passed to `webbrowser.open` as written. I didn't check how that behaves on each platform.

## Pronoun filter

`Client/rude_pronouns.py` rewrites gendered pronouns to neutral ones in text you send. It is off unless `replace_pronouns = True` in the server file, and it only applies to channels you list.

**Setup.** Create `filtered_channels.txt` in `~/.config/rudechat`. It isn't in `DefaultConfig`. Put one channel name per line. Matching ignores case. The file is cached and re-read when its modification time changes, so edits apply without a restart. A missing file means no channel is filtered.

**What it changes.** `handle_user_input` calls `replace_pronouns(text, current_channel)` once per line you send (`rude_client.py:2853`). It leaves incoming text alone. Parts of the text that look like `http://` or `https://` links are left untouched. The rules run in this order, and each one keeps the original capitalisation (all caps, first letter capital, or lower case):

1. `his` or `her` followed by a relation word (`husband`, `wife`, `son`, `daughter`, `brother`, `sister`, `boyfriend`, `girlfriend`) becomes `their` plus a neutral word (`spouse`, `child`, `sibling`, `partner`).
2. `he's` or `she's` before `been`, `got`, `had`, `gone`, `done`, `made`, `seen` or `never` becomes `they've`.
3. `he` or `she` followed by a verb becomes `they` plus the plural verb. It handles irregular verbs (`is` to `are`, `has` to `have`, `does` to `do`, `goes` to `go` and the contracted negatives) and common `-s`, `-es` and `-ies` endings. A list of words that only look like verbs (`always`, `unless` and similar) is left alone, and it skips one adverb in between.
4. `her` is treated as an object (becomes `them`) when it's followed by punctuation, the end of the text, or a short list of linking words such as `to`, `for` and `with`. Otherwise it's a possessive and becomes `their`.
5. Simple swaps: `he's`/`she's` to `they're`, `he'll`/`she'll` to `they'll`, `he'd`/`she'd` to `they'd`, `himself`/`herself` to `themself`, `hers` to `theirs`, `him` to `them`, `his` to `their`, `he`/`she` to `they`, and `guys`/`gals`/`lads`/`lasses` to `folks`.

The rules are regular expressions, not grammar. A sentence the patterns didn't expect can come out wrong, and the filter doesn't tell you when it changes something. The module's docstring describes the same behaviour.

## `/mock`

`/mock <text>` runs `RudeMock.generate_mock` (`Client/rude_mock.py`). It upper-cases every character at an odd index (second, fourth and so on) and leaves the rest as typed, so `this is a test` becomes `tHiS Is a tEsT`. Spaces count as characters. The command then sends the result as a normal channel message and shows it locally (`cmd_mock`, `rude_client.py:5008`). It skips colour-code escaping, emoji and pronoun handling. Because `command_parser` splits the line on whitespace, repeated spaces in your text collapse to one.

## Cowsay and fortunes

**Fortune files** live in `Resources/Fortunes` inside the installed package (`G_SOURCE_DIR`), not in the config folder. Each file is plain UTF-8 text with the extension `.txt`. Entries are separated by `%`, as in the Unix `fortune` format:

```
%
First entry, one or more lines
-- optional attribution
%
Second entry
%
```

The shipped lists are `dadjoke`, `insults`, `therules` and `yomama`. The loader reads the whole file and splits on every `%` character, not only on a `%` that sits on its own line. A percent sign inside a fortune therefore splits that fortune in two. The loader also strips the file and splits it, so a file that starts with `%` produces an empty first entry. Picking that empty entry prints nothing useful.

**Commands.**

- `/fortune` picks a random file, then a random entry, and sends it one line at a time with a 0.4 second pause between lines (`cmd_fortune`, line 4882).
- `/fortune <name>` uses `Resources/Fortunes/<name>.txt`. The code doesn't check the file exists (`get_fortune_file`, line 3157), so an unknown name raises `FileNotFoundError`. I didn't check whether anything catches it.
- `/cowsay` with no argument picks a random fortune and puts it in a speech bubble.
- `/cowsay <name>` does the same for the named fortune file, if `Resources/Fortunes/<name>.txt` exists. Otherwise the whole argument is treated as the text to say (`cmd_cowsay`, line 4850).
- `/fortunes` opens the fortunes folder in your file manager.

**The bubble.** `cowsay` (line 3100) wraps the text at 100 characters (`wrap_text`), draws a box with `_` and `-` borders and `/ | \` sides, and appends a fixed cow drawing. Each line of the bubble gets a random IRC colour from 02 to 15 followed by a reset (`\x03NN ... \x0F`). The cow itself isn't coloured. Each output line goes out as its own `PRIVMSG`.

Because the files sit inside the package, a reinstall or upgrade can overwrite files you add. The `/help` text says to use a "Fortune List folder" (line 3377), but the folder is `Resources/Fortunes`.

## ASCII art macros

Macros are `.txt` files in `Resources/Macros` inside the package. The macro name is the file name without `.txt`, and names are case-sensitive. Shipped names include `shrug`, `tableflip`, `cow1`, `fedora` and `kitty`.

**Format.** Plain UTF-8 text. Each line of the file becomes one message. The file can contain two kinds of colour data:

- raw characters, including raw control bytes (`gmchat.txt` and `transrights.txt` contain some), which pass through as typed, and
- the four-character text `\xNN` (a backslash, `x` and two hex digits), which is replaced by that character. `\x03` becomes the colour character, `\x02` becomes bold, and so on. The shipped `Windows.txt` and `fedora.txt` use this form. `escape_color_codes` (`rude_client.py:2916`) does the replacement with one regular expression. It decodes each byte as UTF-8, so a value above `\x7f` raises `UnicodeDecodeError`. Stick to `\x00` to `\x7f`.

Because a colour code and a digit run together, write the colour as two digits (for example `\x0304text`) so the first digit of your text isn't read as part of the colour number.

**Loading.** `load_ascii_art_macros` (line 2922) reads every `.txt` in the folder into a dictionary when a client starts. Add a file, then use the Chat menu's reload macros action (or `update_available_macros`) to pick it up without restarting. `/mac` lists the names. `/mac <name>` sends the macro line by line, 0.4 seconds apart, and shows each line locally. `/macros` opens the folder.

**Splash art** at startup uses the same `\xNN` rule. `show_startup_art` (`rude_gui.py:1282`) picks a random `.txt` from `Resources/Splashes` and runs it through `escape_color_codes` before displaying it. Splashes are shown only on your own screen.

The `/help` text says macros go in an "Art folder" (line 3375). The code reads `Resources/Macros`.

## Code oddities noticed while writing this page

- **Fourteen source files don't compile.** The latest commit (`174a20e`) moved docstrings and comments to column 0, directly after `def` and `class` lines. The parent commit parses cleanly; the current tree raises `IndentationError`. The files are `Util/nick_cleaner.py`, `Util/rude_logger.py`, `Util/copy_configs.py`, `Components/rude_user_list_widget.py`, `Components/rude_channel_list_widget.py`, `Components/rude_message_entry.py`, `Components/rude_text_browser.py`, `Components/rude_server_list_widget.py`, `Components/rude_color_option.py`, `Client/init_clients.py`, `Client/rude_pronouns.py`, `Client/rude_auto_away.py`, `Client/rude_friends.py` and `Client/rude_mock.py`. I found the error with `ast.parse` and didn't run the app. `rude_gui.py` and `rude_client.py` import several of them, so the app probably can't start from this tree. Re-indent those docstrings before building.
- `rude_gui.py:1743`: a bare `\x03` sets white instead of resetting colour.
- `rude_gui.py:1680` and `GUI/rude_popout.py:523`: `j + 4 <= len(codes)` is off by one for truncated 24-bit sequences.
- `global_variables.py:17`: comments and values in `ANSI_TO_IRC_MAP` disagree for yellow.
- `global_variables.py:108`: names for codes 16 to 98 don't match the hex colours in `irc_colors`.
- `rude_client.py:1425`: `replace_emojis` returns `None` on an alias error when `use_emojis` is `False`.
- `rude_client.py:3157`: `get_fortune_file` has a `print` after a `return` that never runs, and doesn't check that the file exists.
- Fortune files shipped with a leading `%` produce an empty first entry when loaded (`rude_client.py:4891`, `:3174`).
