# RudeChat IRC Client: For Fun & Reasons.
## Installation    
To install on Linux:

        Download the Stand Alone and extract. 
        or
        Clone the repo, cd into its cloned directory, and pip install -r requirements.txt .

Main Stan Alone files found in: \_internal\/rudechat3\/
Pip Install Directory: \/home\/username\/.local\/lib\/python3.12\/site-packages\/rudechat3\/

To install on Windows Download the installer.

It will install to %LOCALAPPDATA%\Programs\RudeChat3

It is suggested that you use: https://github.com/source-foundry/Hack as your font.
        
Right click anywhere to open and edit the config.
        
RudeIRC assumes conf.server.rude is available and configed properly:

For assistance find me on irc.libera.chat/##rudechat

### Server Config Example:

file name: conf.libera.rude

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

![alt text](https://i.imgur.com/2DmsET8.png)
