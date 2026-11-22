# Slash commands

Type these in the input box. `command_parser` in [`rude_client.py`](../src/rudechat4/rude_client.py) handles them. The names below come from its `match` statement; the in-app `/help` output is the authority on arguments.

Anything that doesn't start with `/` is sent as a message to the current channel or DM.

## Channels

| Command | Purpose |
| --- | --- |
| `/join <channel>` | Join a channel and request its user list |
| `/part <channel>` | Leave a channel |
| `/detach <channel>` | Detach from a channel |
| `/list` | Send `LIST` and open the channel list window |
| `/sw <channel>` | Return a popped-out channel to the main window. It reports an error if you aren't in the channel or it isn't popped out |
| `/names` | Refresh the user list for the current channel |
| `/topic` | Request the topic for the current channel |
| `/mode <mode> [channel]` | Set a mode for yourself, optionally in a specific channel |
| `/banlist` | Show the ban list for the channel |
| `/kick <user> <channel> [message]` | Kick a user |
| `/invite <user> <channel>` | Invite a user to a channel |
| `/clear` | Clear the chat window and remove the saved messages for the current channel |

## Messaging

| Command | Purpose |
| --- | --- |
| `/msg <nickname> [message]` | Send a private message |
| `/query <nickname>` | Open a DM with a user |
| `/cq <nickname>` | Close a DM with a user |
| `/me <action text>` | Send an action to the current channel |
| `/notice <target> [message]` | Send a notice to a user or channel |
| `/ctcp <nickname> <command>` | Send a CTCP request |
| `/broadcast #a,#b <message>` | Send a message to every listed channel |
| `/mentions` | List mentions of your nickname. `/mentions clear` empties the list |
| `/ignore`, `/unignore` | Add or remove a user from the ignore list |

## Users and status

| Command | Purpose |
| --- | --- |
| `/whois <nickname>` | Show information about a user |
| `/who <mask>` | List users matching a mask |
| `/nick <new nickname>` | Change your nickname |
| `/away [message]`, `/back` | Set or clear away status |
| `/watch +nick`, `/watch -nick` | Add or remove a nickname from the watch list |
| `/time` | Send `TIME` to the server |
| `/ping [user]` | Ping the selected server, or a user if you give one |

## Servers

| Command | Purpose |
| --- | --- |
| `/connect <server_name>` | Connect to a configured server |
| `/disconnect` | Disconnect from the currently connected servers |
| `/quit` | Close the connection and the client |
| `/quote <IRC command>` | Send a raw IRC line, for example `/quote MODE #chan +m` |

## Fun and utilities

| Command | Purpose |
| --- | --- |
| `/mac` | Send an ASCII art macro from `Resources/Macros` |
| `/cowsay` | Send text in a cow speech bubble |
| `/fortune` | Send a fortune, optionally through cowsay |
| `/mock` | Send text in alternating case |
| `/logs`, `/macros`, `/fortunes`, `/swhois`, `/sounds` | Open the matching folder in your file manager |
| `/help` | Print the command list |

## Adding a command

1. Add a `case "yourcommand":` to `command_parser`.
2. Put longer logic in a `cmd_yourcommand` method so the match block stays short.
3. Add a line to `display_help`.
4. Add the command to this page.
