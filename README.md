# RudeChat IRC Client: For Fun & Reasons.
## Installation        
To install cd to RudeChat3 folder where the .toml is && run the installer for your OS. 

It will pip install all needed libraries and then RudeChat3. 
You can then run rudechat in your terminal/cmd/powershell to open RudeChat.
It is suggested that you use: https://github.com/source-foundry/Hack as your font.
        
Right click anywhere to open and edit the config.
        
RudeIRC assumes conf.server.rude is available and configed properly:

For assistance find me on irc.libera.chat/##rudechat

Config Example:

file name: conf.libera.rude

        [IRC]
        server_name = Libera
        nickname = Rude
        server = irc.libera.chat
        auto_join_channels = ##rudechat
        use_nickserv_auth = False
        nickserv_password = password
        port = 6697
        ssl_enabled = True
        sasl_enabled = False
        sasl_username = splithead
        sasl_password = password
        use_time_stamp = True
        show_hostmask = True

                password can be replaced with your nick's password to auto-auth with nickserv.
                to use ssl or not you can designate by port: no ssl: 6667 yes ssl: 6697
                ssl_enabled = False needs port 6667
                ssl_enabled = True needs port 6697(usually)
                sasl_enabled will use SASL to authenticate if SASL is available. Default is False - must be enabled.

![alt text](https://i.imgur.com/2DmsET8.png)
