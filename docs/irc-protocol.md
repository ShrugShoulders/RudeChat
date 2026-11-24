# IRC protocol handling

This page covers how `RudeChatClient` speaks IRC: connecting, registering, negotiating capabilities, parsing server limits, and reacting to each command and numeric. For the Qt side see [pyqt.md](pyqt.md). For how a chat line travels through the app, see [message-flow.md](message-flow.md). For slash commands the user types, see [commands.md](commands.md).

All code lives in [`rude_client.py`](../src/rudechat4/rude_client.py) unless noted. Line numbers are from the tree at the time of writing and will drift.

## Parsing and framing

The client reads bytes, splits them into lines, and hands each line to `irctokens.tokenise` (imported in [`shared_imports.py`](../src/rudechat4/shared_imports.py)). A token object gives `.command`, `.params`, `.source` and `.hostmask` (with `.nickname`). Message tags are parsed by `irctokens` but the client never reads them.

Two details are easy to miss:

- Lines are split only on `\r\n`. A server that sends a bare `\n` would never produce a complete line.
- Each `read(4096)` chunk is decoded on its own with `data.decode('UTF-8', errors='ignore')`. A multi-byte character that straddles two reads is silently dropped. See [`handle_incoming_message`](../src/rudechat4/rude_client.py#L2143) and [`_await_welcome_message`](../src/rudechat4/rude_client.py#L398).

`self.decoder` and `self.encoder` (`irctokens.StatefulDecoder` and `StatefulEncoder`, lines 51 and 52) are created in `__init__` but I found no code that uses them. Outgoing lines are built as f-strings in [`send_message`](../src/rudechat4/rude_client.py#L688).

Before tokenising, the receive loop strips `\x1b[?25h`, `\x1b[?7h`, `\x06` and `\a` from the text. If the server's `use_irc_colors` setting is off, it also removes IRC colour codes (`\x03` plus digits) with a regex.

## Server config keys

`read_config` ([line 74](../src/rudechat4/rude_client.py#L74)) reads the `[IRC]` section of a `.rudeserver` file. These keys decide the connection behaviour described below. For the full list and defaults, see [data-files.md](data-files.md).

| Key | Effect on the protocol |
| --- | --- |
| `server`, `port`, `ssl_enabled`, `ignore_cert` | Where and how the socket opens |
| `nickname` | Sent in `NICK` and `USER` (unless ZNC is on) |
| `sasl_enabled`, `sasl_username`, `sasl_password` | SASL PLAIN login |
| `use_nickserv_auth`, `nickserv_password` | `PRIVMSG NickServ :IDENTIFY ...` after the MOTD |
| `znc_connection`, `znc_user`, `znc_password` | `PASS` line, ZNC login name, and ZNC playback handling |
| `use_auto_join`, `auto_join_channels` | Whether `JOIN` runs after registration |
| `auto_rejoin`, `auto_join_invite` | Rejoin after `KICK`, join on `INVITE` |
| `auto_whois` | `WHOIS` on first DM from a nick, and background `WHOIS` of away users |
| `send_ctcp_response` | Master switch for CTCP handling (see below) |

## Connection and registration

[`RudeGui.create_tasks`](../src/rudechat4/rude_gui.py#L781) starts a connection. It sets `is_connected`, awaits `connect()`, then starts the long-running tasks (keep-alive, receive loop and others). Because `connect()` is awaited first, registration finishes inside `_await_welcome_message` before the normal receive loop exists.

```
connect()
 ├─ connect_to_server()      open socket (TLS if ssl_enabled); send PASS if ZNC
 ├─ send_initial_commands()  CAP LS 302, NICK, USER
 └─ wait_for_welcome()       -> _await_welcome_message()  (registration loop)
        reads lines, runs CAP / SASL / NickServ / ZNC logic,
        stops when it decides the session is ready
then create_tasks starts handle_incoming_message (steady-state loop) and the rest
```

### Opening the socket

`connect_to_server` ([line 292](../src/rudechat4/rude_client.py#L292)) uses `asyncio.open_connection` inside `wait_for` with a 256 second timeout.

- TLS off: plain TCP.
- TLS on and `ignore_cert` falsy: default SSL context with hostname checking and `CERT_REQUIRED`.
- TLS on and `ignore_cert` truthy: `check_hostname = False`, `CERT_NONE`.

Check the `ignore_cert` read. `read_config` uses `config.get(...)` (line 92), which returns a string. The string `"False"` is truthy in Python, so the `if not self.ignore_cert` branch is skipped and the `elif self.ignore_cert` branch runs. With the shipped `libera.rudeserver`, which contains `ignore_cert = False`, I expect certificate checks to be off. I read this from the code and did not run it against a server. `getboolean` would fix it.

Only `asyncio.TimeoutError` is caught here. Other connection errors (refused, DNS failure) propagate to the caller.

If `znc_connection` is on, the client sends `PASS <znc_password>` straight after the socket opens, before any `CAP` line. The client does not build a `user/network:password` string. Whatever you store in `znc_password` is sent as is.

### First lines

`send_initial_commands` ([line 327](../src/rudechat4/rude_client.py#L327)) sends, in order:

1. `CAP LS 302`
2. `NICK <nickname>` and `USER <nickname> 0 * :<nickname>`, or the same with `znc_user` when ZNC is on.

The client does not send `CAP END` itself at this point. `CAP END` comes later from the `CAP` and SASL handlers.

### The registration loop

`_await_welcome_message` is a long `match tokens.command` block with its own state flags: `received_001`, `motd_received`, `sasl_authenticated`, `logged_in` (set by numeric 900), `nickserv_sent`, `znc_connected`, plus counters for 366 and topic replies. It reuses the `prtcl_*` handlers from the steady-state loop for most commands. Three things set it apart:

- It reads with `await self.reader.read(4096)` and no timeout. The 60 second `MAX_WAIT_TIME` and the 0.30 second ZNC quiet period are only checked after a read returns, so a silent server can leave it waiting.
- On `001` it enables the Upload File menu action and sets the input placeholder to "Type here...".
- Its exit conditions depend on the login mode (next sections).

When the loop decides registration is done it usually sends a bare `AWAY` (to clear any away state left by a previous session or by ZNC), clears the chat view and shows the startup art. Exceptions are noted per mode.

### Plain registration (no SASL, NickServ or ZNC)

On `376` (end of MOTD), if `use_auto_join` is on, the client calls `automatic_join` (a `JOIN` per channel, 0.1 s apart), sends `AWAY` and returns. If `use_auto_join` is off it returns with no `AWAY`.

Numeric `433` (nick in use) during registration calls `handle_nickname_conflict` ([line 348](../src/rudechat4/rude_client.py#L348)). It appends a random number from 1 to 99 to the configured nickname, sends `NICK`, and updates `self.nickname`.

### SASL

Set `sasl_enabled` to turn it on. The sequence:

1. On `CAP LS`, the client sends `CAP REQ :sasl` along with the other capability requests.
2. On `CAP ACK` containing `sasl`, it sends `AUTHENTICATE PLAIN`.
3. On `AUTHENTICATE +`, `prtcl_AUTHENTICATE` ([line 3828](../src/rudechat4/rude_client.py#L3828)) sends the base64 of `username\0username\0password`. It uses the SASL username for both the authorization and authentication identities. It does not split long payloads into 400 byte pieces.
4. On `903`, `prtcl_903` shows "SASL authentication successful." and sends `CAP END`.
5. `900` sets `logged_in`. Joining happens when `903`, `900`, `005` and the MOTD have all been seen, or at `376` if `903` already arrived.

If the server answers `CAP NAK` for `sasl`, the client sets `sasl_enabled` to false and sends `CAP END`.

Only the PLAIN mechanism is implemented. The client ignores any `sasl=` value in the `CAP LS` list.

### NickServ

With `use_nickserv_auth` on and SASL and ZNC off, the client waits for `376`, then sends `PRIVMSG NickServ :IDENTIFY <nickname> <password>` and sets `nickserv_sent`. The string ends with its own `\r\n` and `send_message` adds another, so the server receives an extra empty line, which it ignores.

It joins channels when numeric `900` arrives. Two other paths also complete registration:

- A `NOTICE` from NickServ whose text contains "invalid password" makes `prtcl_NOTICE` return `True`. The loop then joins anyway (if `use_auto_join` is on), sends `AWAY` and returns.
- Numeric `042` sends a second form of the identify command (`IDENTIFY <password>` without the nickname) and joins. I couldn't tell from the code which networks send `042`.

If the network never sends `900`, the loop waits until the 60 second cap, and only checks that after more data arrives.

### ZNC

ZNC mode changes three things: the login lines (above), how the client treats joins during registration, and how it handles replayed history.

- `JOIN` lines for your own nick go to `join_znc_channel` ([line 377](../src/rudechat4/rude_client.py#L377)). It adds the channel to `joined_channels` and `channel_messages` without sending a `JOIN`. The bouncer already joined for you. `JOIN` lines from other nicks go to `prtcl_JOIN`.
- When `use_auto_join` is off, the client buffers `PRIVMSG` tokens (`PRIVMSGTOKENS`), topics (`332`, `333`, `TOPIC`) and names (`353`, `366`) instead of handling them at once. `reset_timer` stamps the time of the last such line. Once more than 0.30 seconds pass with no new stamp (checked at the next line), the client replays the buffered topics and names, then runs `process_PRIVMSG_tokens`, and returns.
- `process_PRIVMSG_tokens` calls `prtcl_PRIVMSG(..., znc_privmsg=True)` for each buffered message, which saves and highlights without displaying (see [message-flow.md](message-flow.md)). It then sends `CAP REQ` for `away-notify`, `account-notify` and `extended-join`, sends `AWAY`, waits 0.8 s, and clears the chat view.
- The "Syncing with ZNC" banner prints once, after the MOTD arrives, only when `use_auto_join` is off.
- When `use_auto_join` is on, `check_timeout` always returns `None` and `reset_timer` does nothing, so the quiet period never ends the loop. Buffered `PRIVMSG` tokens are appended but I found no path that replays them except the 60 second cap. The loop instead ends on a `366` once `count_366` and `got_topic` reach `len(joined_channels)` and `znc_connected` is true. In that path I don't see the buffered messages processed.
- ZNC together with SASL or NickServ: the `376` branches only handle ZNC when both are off. For the combined case I found no completion path other than the 60 second cap.

During registration in ZNC mode, a `NICK` line whose source differs from `self.nickname` goes to `change_nickname(..., is_from_token=True)` with the new nick. The check doesn't test that the line is about you, and I couldn't confirm from the code what ZNC sends here. The `zncnick` counter that looks meant to limit this to one time is a local variable reset on every line, so it doesn't limit anything.

After registration, `handle_znc_status_message` ([line 1585](../src/rudechat4/rude_client.py#L1585)) handles `*status` messages. A message containing "disconnected" resets the `away_notify`, `extended_join` and `account_notify` flags to false. This lets the CAP `NEW` handler request them again when the bouncer reconnects upstream.

## Capabilities

`prtcl_CAP` ([line 3869](../src/rudechat4/rude_client.py#L3869)) handles `CAP`. The client requests four capabilities and tracks three of them in flags.

| Capability | Requested | Flag | Behaviour change |
| --- | --- | --- | --- |
| `away-notify` | Always | `self.away_notify` | The server sends `AWAY` lines for users who share a channel. `prtcl_AWAY` updates `away_users_dict`, sets `who_user_data[nick]['status']` and highlights away users. The handler runs whether or not the flag is set. The flag only gates the CAP `NEW` re-request. |
| `account-notify` | Always | `self.account_notify` | The server sends `ACCOUNT` lines. `prtcl_ACCOUNT` updates `account_cache`. The flag also makes `send_who` use WHOX (below). |
| `extended-join` | Always | `self.extended_join` | `JOIN` carries the account name as a second parameter. `prtcl_JOIN` caches it. |
| `sasl` | Only if `sasl_enabled` | none (uses `sasl_enabled`) | Starts the SASL exchange above. |

Notes from the code:

- On any `CAP LS` line the client sends one `CAP REQ` for each capability, without checking the list the server offered. A server that splits `LS` over several lines (the `*` continuation form of `CAP LS 302`) would trigger the requests once per line. The code does not look at the `*` marker.
- Each `ACK` is handled on its own. After each `ACK`, if SASL is off, the client sends `CAP END`. Three separate `ACK` lines mean up to three `CAP END` lines. I expect servers to ignore the extras, but I haven't tested that.
- On `NAK`, the matching flag is set to false and a notice is printed. A `NAK` for `sasl` also turns `sasl_enabled` off.
- On `CAP NEW`, only when `znc_connection` is on, the client re-requests missing capabilities (1 s apart) and sends `CAP END`. `CAP DEL` is not handled.
- The client doesn't request `server-time`, `message-tags`, `multi-prefix`, `userhost-in-names`, `echo-message`, `chghost`, `setname`, `batch` or `cap-notify`. Timestamps shown in the UI are the local receive time (`datetime.now()`), and own messages are drawn locally rather than from an echo.
- `account_cache` is filled in three places (`ACCOUNT`, `JOIN` with extended-join, and WHOX `354`) but I found nothing that reads it besides the friend notices in `prtcl_ACCOUNT`. Under `extended-join` an account of `*` (not logged in) is cached as the string `*`.
- The `CAP ACK` handler runs with `tokens.params[2]` as the capability list. That matches the usual `CAP <nick> ACK :<caps>` layout. A server that sends `ACK` with a different parameter count would hit the `except` branch and log "Error1".

## ISUPPORT (005)

`prtcl_005` ([line 4555](../src/rudechat4/rude_client.py#L4555)) runs only during registration. In the steady-state loop, `005` is `pass`, so a later `005` (some servers send one after a feature change) is ignored.

Each call first writes defaults, then overwrites them from the tokens it recognises:

| Token | Stored in | Default | Parsing |
| --- | --- | --- | --- |
| `PREFIX=(ov)@+` | `mode_to_symbol` (dict mode to symbol) | `{'o': '@', 'v': '+'}` | Splits on `)` and zips modes with symbols |
| `CHANTYPES=#&` | `chantypes` (list of characters) | `['#', '&']` | `list(value)` |
| `NICKLEN=` | `nicknamelen` | 16 | `int` |
| `CHANLIMIT=#&:10` | `chan_limit` | 250 | Splits on `:` and keeps the number only if there are exactly two parts |
| `CHANNELLEN=` | `channellen` | 50 | `int` |
| `TOPICLEN=` | `topiclen` | 390 | `int` |
| `CHANMODES=A,B,C,D` | `chanmodes` | see below | Needs exactly four comma-separated groups |

`chanmodes` maps type names to lists of mode letters. The code's names don't follow the ISUPPORT A/B/C/D labels, so here is the mapping:

| Key in `chanmodes` | ISUPPORT group | Meaning |
| --- | --- | --- |
| `list` | A | List modes such as bans |
| `parameter` | B | Always take a parameter |
| `setting` | C | Take a parameter only when set |
| `no_parameter` | D | Never take a parameter |

After parsing, `get_mode_lists` fills `mode_keys` and `mode_values` from `mode_to_symbol`. `mode_values` (the prefix symbols, such as `@+`) is used all over the file to strip prefixes from nicknames.

Things to know:

- Any other token is ignored. That includes `NETWORK`, `MODES`, `TARGMAX`, `STATUSMSG`, `CASEMAPPING` and `WHOX`. The client doesn't check for `WHOX`. It picks WHOX syntax based on `account_notify` alone.
- The last parameter (the "are supported by this server" text) is dropped with `params[:-1]`. The first parameter, your nick, is passed through the token checks and matches nothing.
- Because the defaults are rewritten at the top of every call, a server that splits ISUPPORT over several `005` lines (common, since each line holds about 13 tokens) resets earlier values whenever a later line lacks that token. For example, a `PREFIX` seen on line one would be replaced with the default on line two.
- `chanmodes` is not set in `__init__`. Until the first `005`, `set_mode` would raise `AttributeError` on it, and `prtcl_MODE` would log an error.
- `reset_state` (used on reconnect) calls `mode_to_symbol.clear()`. The next `005` refills it.

## Commands and numerics

The steady-state dispatcher is `handle_incoming_message` ([line 2143](../src/rudechat4/rude_client.py#L2143)). Each line goes through one `match tokens.command`. Every branch runs inside a `try` that logs and continues, so one bad line doesn't stop the loop. The tables below follow the order of the `match`.

Display targets: the **chat view** is the current channel's text area (`gui.insert_text_widget`). The **server tab** is the server's own buffer (`add_server_message`, stored in `motd_dict[server_name]`, which also highlights the server in the server list).

### Handled by a small "to client" helper

`bprtcl_to_client` ([line 3521](../src/rudechat4/rude_client.py#L3521)) writes straight to the chat view.

| Command or numeric | Meaning | Client action |
| --- | --- | --- |
| `ERROR` | Server closing the link | Shows `ERROR: <text>` |
| `250` | Highest connection count | Shows "Server Info: ..." |
| `266` | Global user count | Shows "Server Users Info: ..." |
| `305`, `306` | No longer away, now away | Shows a status line. These only print. They don't change `away_users_dict`. |
| `367`, `368` | Ban list entry, end of list | Shows mask, setter and time, then "End of ban list" |
| `391` | Server time | Shows the time string |
| `431`, `461` | No nickname given, not enough parameters | Shows source plus params |
| `477` | Channel needs registered nick (or similar) | Shows "Cannot join channel ..." |

### Handled by a small "to server" helper

`bprtcl_to_server` ([line 3547](../src/rudechat4/rude_client.py#L3547)) writes to the server tab.

| Command or numeric | Meaning | Client action |
| --- | --- | --- |
| `KILL` | You were killed | Source, target and reason |
| `WALLOPS` | Operator broadcast | Source and text |
| `263` | Rate limited, try again | Command and message |
| `307` | Nick is registered | Source and params |
| `324` | Channel modes | "Modes for #chan: ..." |
| `328` | Channel URL | Shows the URL |
| `329` | Channel creation time | Converts the epoch with `datetime.fromtimestamp(..., tz=timezone.utc)` and prints it as UTC |
| `341` | Invite sent | Params joined |
| `378`, `379` | Host and mode info from WHOIS-style replies | Params joined |
| `396` | Host now hidden | "Your host is now hidden as ..." |
| `403`, `404`, `442`, `443`, `482` | No such channel, cannot send, not on channel, already on channel, not operator | Reason text |
| `432` | Erroneous nickname | Params |
| `464` | Password incorrect | Params |
| `472` | Unknown mode | "Unknown mode for ..." |
| `487` | Server error text (meaning varies by server software) | Params |
| `716` | Target is in caller-ID mode | Params |
| `900` | Logged in | "Successfully authenticated as: <account>" (`params[3]`) |

### WHOIS and WHO replies

See [WHO and WHOIS](#who-and-whois) for the flow.

| Command or numeric | Meaning | Client action |
| --- | --- | --- |
| `301`, `311`, `312`, `313`, `317`, `318`, `319`, `330`, `338`, `671` | WHOIS replies: away text, user info, server, operator, idle time, end, channels, account, actual IP, secure connection | `bprtcl_whois_replies` fills `whois_data[nick]` |
| `315`, `352`, `354` | WHO end, WHO reply, WHOX reply | `bprtcl_who_replies` fills `who_user_data[nick]` |

### State changes

| Command or numeric | Meaning | Client action |
| --- | --- | --- |
| `ACCOUNT` | User logged in or out (account-notify) | `prtcl_ACCOUNT`: updates `account_cache`, tells you when a friend logs in or out |
| `AWAY` | User set or cleared away (away-notify) | `prtcl_AWAY`: updates `away_users_dict` and `who_user_data` status, then calls `gui.highlight_away_users` |
| `CAP` | Capability negotiation | `prtcl_CAP` (above) |
| `INVITE` | You were invited | `prtcl_INVITE`: runs `/join` through `command_parser` if `auto_join_invite` is on, otherwise prints a notice |
| `JOIN` | User joined | `prtcl_JOIN`: caches the account if `extended_join` is on, checks the friends list, records the join message, adds the nick to `channel_users`, refreshes the user list. For your own nick it only handles ZNC and returns. |
| `KICK` | User kicked | `prtcl_KICK`: records the kick, removes the user, and if it was you, rejoins after 1 s (`auto_rejoin`) or removes the channel from the list |
| `MODE` | Mode change | `prtcl_MODE`: uses `chanmodes` to decide which letters consume a parameter. Prefix modes update `user_modes` and the user list. |
| `NICK` | Nick change | `prtcl_NICK`: updates every channel list the nick is in, DM tabs (`prtcl_NICK_dm_helper`) and colours. Updates `self.nickname` if it was you. |
| `PART` | User left | `prtcl_PART`: records the part message and removes the user |
| `QUIT` | User quit | `prtcl_QUIT`: removes the user from every channel list, drops them from `away_users_dict` and the online friends list |
| `TOPIC`, `332`, `333` | Topic changed, topic text, topic setter | `bprtcl_topic`: stores the topic in `gui.channel_topics` and updates the label if it's the current channel |
| `353`, `366` | Names list, end of names | `prtcl_353` adds users (with prefixes) and assigns nick colours. `prtcl_366` sorts and redraws the user list. |
| `433` | Nick in use | `prtcl_433`: shows the message, then sets `self.nickname` to `params[0]` (the nick the server reports, which is `*` during registration) without sending `NICK`. |
| `471`, `473`, `474`, `475` | Cannot join: full, invite only, banned, bad key | `m_prtcl_ChannelJoinUnable`: shows the reason and removes the channel from `joined_channels` |
| `476`, `479` | Bad channel mask, illegal channel name | `m_prtcl_BadChannelName`: shows the reason and sends `PART` if the channel was in the list |
| `401` | No such nick | `prtcl_401`: drops the nick from `away_users_dict` and prints a notice |

### Chat, notices and keep-alive

| Command or numeric | Meaning | Client action |
| --- | --- | --- |
| `PRIVMSG` | Chat message, DM or CTCP | `prtcl_PRIVMSG` (see [message-flow.md](message-flow.md) and [CTCP](#ctcp)) |
| `NOTICE` | Notice | `prtcl_NOTICE`: formats as `NOTICE <sender> <target>: <text>`. For channel targets it appends the notice to the history of every channel on this server (`add_notice_to_history` loops over all of them). It shows the notice in the chat view and adds it to the server tab. |
| `PING` | Server keep-alive | Replies `PONG <params[0]>` |
| `PONG` | Reply to your ping | `prtcl_PONG`: updates the ping label (see [keep-alive](#keep-alive-and-timeouts)) |

### Registration, MOTD and lists

| Command or numeric | Meaning | Client action |
| --- | --- | --- |
| `001` | Welcome | `pass` in this loop. Handled during registration. |
| `002`, `003`, `004`, `251`, `252`, `253`, `254`, `255`, `265` | Server info and counts | `server_message_handler` writes to the server tab |
| `005` | ISUPPORT | `pass` in this loop. Parsed during registration only. |
| `321` | List start | `pass` |
| `322` | One `/list` entry | `prtcl_322` stores it in `gui.download_channel_list` and passes it to the list window |
| `323` | List end | `prtcl_323` writes `channel_list.txt` in the config folder |
| `372`, `375`, `376` | MOTD line, start, end | Collected in `motd_lines`. `376` appends the text to the server tab and prints "Message of the Day". |
| `412` | No text to send | `pass` |

### Anything else

The `case _` branch logs the unhandled line only when `log_on` is true. Then, if the line starts with `:<self.server>` (the hostname from your config), it goes to the server tab through `handle_server_message`. That prefix test needs the server to identify itself with exactly the hostname you configured. A network that connects you through a different host name (round-robin DNS, for example) will drop those lines.

### Registration-only handlers

These appear in `_await_welcome_message` but not in the steady-state loop: `042`, `904`, `396` (sets `got_396`, shows nothing), `328` (shown in the server tab), `305` and `306` (`pass`), and the `NOTICE` return-value check. Numeric `904` is covered above.

## WHO and WHOIS

### Which WHO to send

`send_who` ([line 189](../src/rudechat4/rude_client.py#L189)) picks the form:

- With `account_notify` on: `WHO <target> %nuhsrcdfa` (WHOX with the fields nick, user, host, server, realname, channel, hops, flags and account).
- Otherwise: plain `WHO <target>`.

The code does not test whether the server supports WHOX. It relies on `account-notify` as a stand-in. A server that grants `account-notify` but lacks WHOX would return an error for the `%` form. I haven't seen that case handled.

### When WHO is sent

| Trigger | Where | Notes |
| --- | --- | --- |
| After joining | `request_who_for_all_channels` ([line 1084](../src/rudechat4/rude_client.py#L1084)) | Waits 4 s, then goes through `joined_channels`, skipping those already in `cap_who_for_chan`. Sends one `WHO` per channel with a 14 s gap, then sets `who_for_chan_complete`. Runs once. |
| `/join` | `command_parser` | Sends `WHO <channel>` right after `JOIN` |
| `/who [mask]` | `cmd_who` | Sets `who_user_request` so the result prints to the chat view. No argument sends a bare `WHO`. |
| Every 10 minutes | `request_who_for_missing_users` | For each channel member not in `who_user_data`, waits 10 s and sends `WHO <nick>`. |

`cap_who_for_chan` is the list of channels already queried. DM tabs and the `!WHOIS!` and `!MENTIONS!` pseudo-channels are added to it so they are never queried.

### Reading WHO replies

`bprtcl_who_replies` ([line 3639](../src/rudechat4/rude_client.py#L3639)) handles three numerics.

- `352` (plain WHO): reads channel, user, host, server, nick and flags from `params[1]` to `params[6]`, and `params[7]` as the "hops and realname" text.
- `354` (WHOX): same first fields, then `params[8]` as account and `params[9]` as realname. This fits the fixed field order that WHOX replies use (channel, user, host, server, nick, flags, hops, account, realname) when the request has no `t` field.
- `315` (end of WHO): joins the collected rows into text and prints them only if `who_user_request` is set.

The flags field starts with `H` (here) or `G` (gone). `G` becomes status "Away", anything else "Active". `_who_reply_data_handler` then adds or removes the nick in `away_users_dict`. This means a WHO result can set an away entry with an empty message, which `whois_worker` later fills.

Results are merged into `who_user_data[nick]`. A user seen in several channels gets a comma-separated `shared-channels` string and a `mode` string such as `#chan(@)`. With `354` the account goes into `account_cache` too. Nothing removes entries from `who_user_data` on `QUIT` or `NICK`; I found no deletion for it. The user info dialog (`RudeGui.open_user_info`) and the user list context menu read this dict.

`update_user_data` exists twice: as a nested helper inside `bprtcl_who_replies` and as a method on the class ([line 3476](../src/rudechat4/rude_client.py#L3476)). The method looks unused.

### WHOIS

| Trigger | Where |
| --- | --- |
| `/whois nick` | `command_parser` sets `whois_user_request` and calls `cmd_whois`, which sends `WHOIS <nick>`. |
| First DM from a nick, `auto_whois` on | `get_direct_message_target` sends `WHOIS` once per nick (tracked in `whois_executed`) and also sets `whois_user_request`. |
| Background pass | `the_worker` waits until `who_for_chan_complete`, then `whois_worker` sends `WHOIS` for each entry in `away_users_dict` with an empty message, 5 s apart. It runs once, then clears `whois_data` and sets `whois_gathering_complete`. Needs `auto_whois`. |
| Away DM | `_away_user_helper` calls `get_away_user_whois` when you message someone marked away with no text yet. |

`bprtcl_whois_replies` ([line 3754](../src/rudechat4/rude_client.py#L3754)) builds `whois_data[nick]`:

| Numeric | Stored as |
| --- | --- |
| `301` | `Away` (also updates `away_users_dict` if the nick is there) |
| `311` | Starts a fresh dict: `Username`, `Hostname`, `Realname` |
| `312` | `Server` |
| `313` | `Operator` |
| `317` | `Idle Time` (formatted with `timedelta`) |
| `319` | `Channels` |
| `330` | `Logged In As` |
| `338` | `Actual IP` |
| `671` | `Secure Connection` |
| `318` | End. If `whois_user_request` is set, `whois_display` shows the result. |

`whois_display` puts the text into a `!WHOIS!` pseudo-channel tab and clears `whois_user_request`. `save_whois_to_file` also writes it to `whois/whois_<nick>.txt` in the config folder. Both append a suggested ignore mask, `*!<user>@<host>`.

Gaps and oddities:

- Because `get_direct_message_target` sets `whois_user_request`, the first DM from a new nick (with `auto_whois` on) also opens a `!WHOIS!` tab with the result.
- The `318` branch builds `whois_response` only inside `if nick:`. If the reply arrives for a nick with no earlier data, the loop over `self.whois_data[nickname]` raises `KeyError`. The method's own `except` logs it and nothing is shown.
- `311` replaces the whole dict, so a `301` that arrives before `311` loses its `Away` entry.
- Numerics for unknown servers (`402`) and WHOWAS (`406`, `369`) have no case and fall to the default branch.
- `whois_data` is never saved across a reconnect. `reset_state` clears it.

## CTCP

`prtcl_PRIVMSG` calls `is_ctcp_command` ([line 1555](../src/rudechat4/rude_client.py#L1555)) on the raw message. It is true when the text starts and ends with `\x01`. Those messages go to `handle_ctcp` ([line 1132](../src/rudechat4/rude_client.py#L1132)) and then return. Ignored senders are dropped before this step.

`handle_ctcp` does nothing unless `send_ctcp_response` is on. That switch covers `ACTION` too, so with it off, other people's `/me` lines are dropped as well. I think this is unintended, but I didn't find a comment that says so.

Only the upper and lower case forms of each name are matched (`VERSION` or `version`). Mixed case isn't. Replies go back as `NOTICE <sender> :\x01...\x01`, and each reply writes a "CTCP: sender target: command" line to the server tab.

| CTCP command | Reply |
| --- | --- |
| `VERSION` | `VERSION RudeChat4.2.0` (hard-coded string) |
| `MOO` | `MoooOOO! Hi Cow!! RudeChat4.2.0` |
| `PING` | `PING <their payload> <current unix time>`. This appends an extra timestamp to the payload. The CTCP spec says to echo the payload unchanged. |
| `FINGER` | `FINGER: <nick> <server_name> RudeChat4.2.0` |
| `CLIENTINFO` | `CLIENTINFO VERSION TIME PING FINGER`. It doesn't list `MOO` or `ACTION`. |
| `TIME` | `TIME <local date time>` using `pytz` and the `tzlocal` zone |
| `ACTION` | No reply. `handle_action_ctcp` ([line 1194](../src/rudechat4/rude_client.py#L1194)) formats `* nick text`, stores it in `channel_messages`, and shows or pops it out. |
| anything else | Logged (if `log_on`) and ignored |

Replies are only sent when `tokens.command == "PRIVMSG"`. The handler is never called for `NOTICE`, so CTCP replies you receive (for example from `/ctcp nick VERSION`) show up as plain notices through `prtcl_NOTICE`, control characters and all.

Sending: `/ctcp <nick> <command>` calls `send_ctcp_request`, which sends `PRIVMSG <nick> :\x01<COMMAND>\x01` with the command upper-cased. `/me` sends `PRIVMSG <channel> :\x01ACTION <text>\x01` ([`cmd_me`](../src/rudechat4/rude_client.py#L4956)).

Neither a received `ACTION` nor your own `/me` calls `log_message`, so actions don't reach the plain-text chat logs. They do reach the saved history in `channel_messages`.

## Keep-alive and timeouts

Several things keep the link honest:

| Mechanism | Where | Behaviour |
| --- | --- | --- |
| Client `PING` | `keep_alive` ([line 949](../src/rudechat4/rude_client.py#L949)) | Loop: note the time, sleep 60 s, send `PING <server>`. The server's `PONG` reaches `prtcl_PONG`. |
| Server `PING` | `handle_incoming_message`, `prtcl_PING` | Replies `PONG <params[0]>` right away. |
| Read timeout | `handle_incoming_message` | Each read is wrapped in `wait_for(..., 256)`. A quiet link for 256 s counts as dead. |
| Empty read | same | `read` returns `b''` when the server closes the socket. |
| Send timeout | `send_message` | `drain()` waits at most 10 s. A failure prints "Connection Error" in the chat view. It doesn't trigger a reconnect. |

The ping label: `prtcl_PONG` ([line 4405](../src/rudechat4/rude_client.py#L4405)) computes `now - ping_start_time`, formats the number with three decimals, strips a leading `0`, appends `ms`, and calls `gui.update_server_ping`. Two issues:

- `ping_start_time` is set at the top of the `keep_alive` loop, then the loop sleeps 60 s before it sends `PING`. The measured value includes the sleep, so the keep-alive number would read about 60 plus the round trip.
- The value is in seconds but labelled `ms`. A 45 ms round trip from `/ping` shows as `.045ms`.

`prtcl_PONG` also hides `PONG` lines from servers whose name starts with `irc`, and (in ZNC mode) names with a dot.

### Reconnect

Three read failures call `reconnect` ([line 886](../src/rudechat4/rude_client.py#L886)): a timeout, an `OSError`, and an empty read. Each first tries `send_message('QUIT :<reason>')`. The timeout case builds the reason from `e.strerror`. On Python 3.11 and later, `asyncio.TimeoutError` is the built-in `TimeoutError` and its `strerror` is `None`, so the text reads `QUIT :None`. On older Pythons the attribute doesn't exist. I didn't check which versions the project supports. The old socket is not closed. I found no `writer.close()` call anywhere in the file.

`reconnect` does this:

1. Return at once if `disconnect_requested` is set.
2. `reset_state`: clears `motd_dict`, `joined_channels`, `motd_lines`, `channel_users`, `user_modes`, `mode_to_symbol`, `whois_data`, the GUI's `/list` results and `whois_executed`. It leaves the capability flags, `who_user_data`, `account_cache` and `cap_who_for_chan` as they are.
3. Print "DISCONNECTED ... Auto Reconnecting" with the delay: 15 s, or 5 s in ZNC mode.
4. Up to 5 tries: sleep for the delay, call `connect(config_file)` (full registration again), then `replace_dms_in_gui`, set `loop_running`, and select the first server.
5. After the fifth failure, log (only when `log_on`) and give up. It prints nothing to the chat view and doesn't schedule another attempt.

Because `reconnect` is awaited inside `handle_incoming_message`, the receive loop resumes with the new `reader` once it returns. `keep_alive` and the other tasks keep running through the reconnect. They read `self.writer` each time they send.

Two side effects of re-registering: `joined_channels` is emptied, so the rejoin happens through `automatic_join` (or ZNC replay), not through `auto_rejoin`. Channels you joined by hand are not restored unless they are in `auto_join_channels`.

### Disconnect and quit

`/disconnect <server>` ([`disconnect`](../src/rudechat4/rude_client.py#L2410)) sends `QUIT`, sets `loop_running` false, `is_connected` false and `disconnect_requested` true, and clears the ping label. It calls `reset_state` but doesn't cancel the tasks or close the socket. `/connect` starts everything again through `RudeGui.client_connect`.

Quitting the app (`/quit` or the tray menu) sends `QUIT` through `send_quit` or `spec_quit`, saves history, and cancels all asyncio tasks except `on_enter_key` and `quit_client_task`.
