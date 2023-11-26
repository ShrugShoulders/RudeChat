RudeIRC assumes conf.rude is available and configed properly:

Config Example:

        [IRC]
        nickname = Rudie
        server = irc.libera.chat
        auto_join_channels = #irish
        nickserv_password = password
        port = 6697
        ssl_enabled = True
        font_family = Hack
        font_size = 10
        sasl_enabled = False
        sasl_username = Rudie
        sasl_password = password

                password can be replaced with your nick's password to auto-auth with nickserv.
                to use ssl or not you can designate by port: no ssl: 6667 yes ssl: 6697
                ssl_enabled = False needs port 6667
                ssl_enabled = True needs port 6697(usually)
                sasl_enabled will use SASL to authenticate if SASL is available. Default is False - must be enabled.

![alt text](https://i.imgur.com/3ZrVDk4.png)
