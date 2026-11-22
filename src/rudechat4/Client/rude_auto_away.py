#!/usr/bin/env python3
"""Idle timer used to mark a user as away after a period of inactivity."""
from rudechat4.shared_imports import *
from rudechat4.global_variables import *

class AutoAway:
    """Tracks how long it has been since the user last sent a message.

        Attributes:
            last_message_time: Time of the last recorded activity.
            config: Path to the ``.rudeserver`` file the threshold is read from.
            minutes: Idle minutes allowed before the user counts as away.
    """
    def __init__(self, config_file):
        # Initialize the last_message_time with the current time
        """Start the idle timer and read the threshold.

            Args:
                config_file: Path to the ``.rudeserver`` file to read
                    ``auto_away_minutes`` from.
        """
        self.last_message_time = datetime.now()
        self.config = config_file
        self.minutes = 0
        self.load_configuration()

    def load_configuration(self):
    	# Reads config and loads it
        """Read ``auto_away_minutes`` from the config file, defaulting to 30."""
        config = configparser.ConfigParser()
        config.read(self.config)

        config_minutes = config.get('IRC', 'auto_away_minutes', fallback='30')
        self.minutes = int(config_minutes)

    def reload_config(self):
    	# Reloads configuration
        """Re-read the threshold from the config file."""
        self.load_configuration()

    def update_last_message_time(self):
        # Update the last message time to the current time
        """Reset the idle timer to now."""
        self.last_message_time = datetime.now()

    def time_since_last_message(self):
        # Calculate the time passed since the last message
        """Return the idle time as a ``timedelta``."""
        return datetime.now() - self.last_message_time

    def check_auto_away(self):
        # Check if the user should be marked as away based on the threshold
        """Report whether the idle time has passed the threshold.

            Returns:
                True if the user has been idle longer than ``minutes``.
        """
        time_passed = self.time_since_last_message()
        if time_passed > timedelta(minutes=self.minutes):
            return True  # User is away
        return False  # User is still active