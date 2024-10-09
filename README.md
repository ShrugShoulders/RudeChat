# RudeChat IRC Client: For Fun & Reasons.
## Installation    
To install on Linux:

        Download the Stand Alone and extract.(recommended for Debain/Ubuntu users.)
        In your Terminal cd to the folder where you extracted the package.
        Using ./rudechat3 will open rudechat. 
        or
        Clone the repo, cd into its cloned directory, and use pip to install. 
        Command: 'pip install -r requirements.txt .'
        Once pip has completed you can then run rudechat in your terminal. 
        Command: 'rudechat'

Main Stand Alone files found in: \_internal\/rudechat3\/
Pip Install Directory: \/home\/username\/.local\/lib\/python3.12\/site-packages\/rudechat3\/

To install on Windows Download the installer.

It will install to %LOCALAPPDATA%\Programs\RudeChat3

It is suggested that you use: https://github.com/source-foundry/Hack as your font.

Right click anywhere to open and edit the config.

RudeChat assumes conf.server_name.rude is available and configed properly:

For assistance find me on irc.libera.chat/##rudechat

### Server Config Example:

file name: conf.libera.rude(config files should follow conf.server_name.rude naming)

        [IRC]
        server_name = Libera # This is the server name. 
        nickname = Rude # This is your nickname.
        server = irc.libera.chat # This is the server url. 
        auto_join_channels = ##rudechat # This is the list of autojoin channels Example: #chan1,#chan2,#chan3
        use_nickserv_auth = False # Want to use nickserv? False for no True for yes.
        nickserv_password = password # This would be your nickserv password, using nickserv? Set this.
        port = 6697 # This is the port you use to connect to the IRC network. 
        ssl_enabled = True # Do you like SSL? Awesome, so do I. 
        sasl_enabled = False # Are you skilled enough to use SASL? Sweet, set that up. 
        sasl_username = splithead # SASL user name. 
        sasl_password = password # SASL Paassword, if you know you know. 
        use_time_stamp = True # Want time stamps to be shown next to nicks? True for yes, False for no. 
        show_hostmask = True # Want joins, parts, and quits to have full host masks? True for yes, False for no. 
        show_join_part_quit_nick = True # This enabled or disables showing joins parts and nick messages. 
        use_beep_noise = True # Enables beep notifications. 
        auto_whois = True # Enables or Disables auto whois capabilities. 
        custom_sounds = False # Custom Sounds - Linux Only.
        use_logging = True # Disables or Enables Logging. 
        znc_connection = False # Tells the client you're using a ZNC. 
        znc_password = password # Password for ZNC Server. 
        ignore_cert = False # You can ignore ssl certs that are not signed. 
        znc_user = Rude # User name for ZNC. 
        replace_pronouns = False # Might Remove This - Replaces gender pronouns with gender neutral statements.
        display_user_modes = True # This will display the user mode beside the nickname. 
        send_ctcp_response = True # Turns CTCP responses on or off
        green_text = False # Automatic green text styling
        auto_away_minutes = 30 # Auto Away timer - sets user auto away after a certain time.
        use_auto_away = True # Turn this to True for auto away, see time above.
        auto_join_invite = True # This will auto-join on invite to a channel. 
        log_on = False # Logs everything in the client including incoming data, etc. 

### GUI Config Example:

file name: gui_config.ini

        [GUI]
        master_color = black # The Master Window Color - Change if you know what you're doing. 
        family = Hack # This is the font family, Hack is recommended. 
        size = 10 # Font Size. Obviously. 
        main_fg_color = #C0FFEE # This is the main chat display window foreground (text color)
        main_bg_color = black # This is the main chat display window background color.
        server_fg = #7882ff # This is the main console window or server window foreground (text color)
        server_bg = black # This is the main console window or server window background color.
        selected_list_server = blue # The background for the selected server.
        user_font_size = 9 # Users listbox font size.
        channel_font_size = 9 # Channel listbox font size
        server_font_size = 9 # Server listbox font size
        list_boxs_font_family = Hack # Font for all list boxes.
        topic_label_font_size = 10 # Topic Display Font size
        topic_label_font_family = Hack # Topic Display Font
        minimize_to_tray = True # This will allow RudeChat to be minimized to the tray - Set to False and client will simply shutdown.
        turn_logging_on = False # This enables GUI logging for ayncio task creation & more
        
        [WIDGETS]
        users_fg = #39ff14 # This is the user list foreground (text color)
        users_bg = black # This is the user list background color. 
        channels_fg = white # This is the channels list foreground (text color)
        channels_bg = black # This is the channels list background color. 
        entry_fg = #C0FFEE # This is the input Widgets foreground (text color)
        entry_insertbackground = #C0FFEE # This is the insertbackground color - set as the same as entry_fg for best results, but have fun!
        entry_bg = black # This is the entry Widgets background color. 
        entry_label_bg = black # This is the background color of the label directly to the left of the Entry Widget. 
        entry_label_fg = #C0FFEE # This is the foreground color of the label directly to the left of the Entry Widget.
        server_listbox_bg = black # This is the server list background color. 
        server_listbox_fg = white # This is the server list foreground color (text)
        tab_complete_terminator = : # Don't like to end your nickname tab complets with a colon? Change it!
        channel_label_bg = black # Label for Channel list background
        channel_label_fg = white # Label color for Channel List foreground
        servers_label_bg = black # Servers label background
        servers_label_fg = white # Servers label foreground 
        topic_label_bg = black # Topic Label background. 
        topic_label_fg = white # Topic Label Text Color
        channel_select_color = blue # Channel selected color
        show_server_window = False # Server Window Toggle. 

![alt text](https://i.imgur.com/eWkOK9p.png)
