#!/usr/bin/env python3
from rudechat4.shared_imports import *
from rudechat4.global_variables import *

from rudechat4.GUI.rude_config_gui import RudeConfigGui

from rudechat4.Util.rude_logger import configure_logging

class RudeConfigServer(RudeConfigGui):
    def __init__(self, parent, config_file, close_callback):
        super().__init__(parent, config_file, close_callback)

        self.start()

        print(self.widget.layout.count())

    def start(self):
        self.channels = self.config.get('IRC', 'auto_join_channels')

        self.label_map = {
            'server_name': ['Server Name', 'string'],
            'nickname': ['Nickname', 'string'],
            'server': ['Server Address', 'string'],
            'auto_join_channels': ['Auto-Join Channels', 'channels'],
            'use_nickserv_auth': ['Use NickServ Authentication', 'bool'],
            'nickserv_password': ['NickServ Password', 'string'],
            'port': ['Port', 'string'],
            'ssl_enabled': ['SSL Enabled', 'bool'],
            'sasl_enabled': ['SASL Enabled', 'bool'],
            'sasl_username': ['SASL Username', 'string'],
            'sasl_password': ['SASL Password', 'string'],
            'use_time_stamp': ['Use Time Stamps?', 'bool'],
            'show_hostmask': ['Show Hostmasks?', 'bool'],
            'show_join_part_quit_nick': ['Show Join/Part/Quit Messages?', 'bool'],
            'use_beep_noise': ['Use Beep Noises?', 'bool'],
            'auto_whois': ['Auto WHOIS Users?', 'bool'],
            'custom_sounds': ['Custom Sounds', 'bool'],
            'mention_note_color': ['Mention Channel Highlight', 'color'],
            'activity_note_color': ['Activity Channel Highlight', 'color'],
            'use_logging': ['Turn Logging On/Off', 'bool'],
            'znc_connection': ['Use ZNC Connection', 'bool'],
            'znc_password': ['ZNC Password', 'string'],
            'ignore_cert': ['Ignore SSL Certs?', 'bool'],
            'znc_user': ['ZNC Username', 'string'],
            'replace_pronouns': ['Replace Pronouns?', 'bool'],
            'display_user_modes': ['Display User Modes?', 'bool'],
            'use_auto_join': ['Use Auto Join?', 'bool'],
            'auto_rejoin': ['Auto Rejoin on Kick?', 'bool'],
            'use_irc_colors': ['Enable/Disable IRC Colors', 'bool'],
            'send_ctcp_response': ['Respond to CTCP Requests?', 'bool'],
            'green_text': ['Green Text Styling', 'bool'],
            'auto_away_minutes': ['Time Until Auto Away', 'string'],
            'use_auto_away': ['Use Auto Away?', 'bool'],
            'auto_join_invite': ['Auto Join On Invite?', 'bool'],
            'log_on': ['Turn Client Debug Logging On', 'bool'],
            'use_emojis': ['Turn Emoji filters on/off', 'bool'],
            'auto_connect_to_networks': ['Turn Server auto-connect on/off', 'bool'],
        }

        configure_logging()
        self.entries = {}
        self.reload_channels()

    def reload_channels(self):
        self.channels = self.config.get('IRC', 'auto_join_channels')

        try:
            self.widget.layout.itemAt(0).widget().setParent(None)
        except:
            logging.info("No widget to remove")

        self.create_widgets()