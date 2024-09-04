from datetime import datetime, timedelta
import configparser
import os

class AutoAway:
    def __init__(self, config_file):
        # Initialize the last_message_time with the current time
        self.last_message_time = datetime.now()
        self.config = config_file
        self.minutes = 0
        self.load_configuration()

    def load_configuration(self):
    	# Reads config and loads it
        config = configparser.ConfigParser()
        config.read(self.config)

        config_minutes = config.get('IRC', 'auto_away_minutes', fallback='30')
        self.minutes = int(config_minutes)

    def reload_config(self):
    	# Reloads configuration
        self.load_configuration()

    def update_last_message_time(self):
        # Update the last message time to the current time
        self.last_message_time = datetime.now()

    def time_since_last_message(self):
        # Calculate the time passed since the last message
        return datetime.now() - self.last_message_time

    def check_auto_away(self):
        # Check if the user should be marked as away based on the threshold
        time_passed = self.time_since_last_message()
        if time_passed > timedelta(minutes=self.minutes):
            return True  # User is away
        return False  # User is still active