#!/usr/bin/env python3
"""Text transform behind the ``/mock`` command."""
from rudechat4.shared_imports import *
from rudechat4.global_variables import *

from rudechat4.Util.rude_logger import configure_logging

class RudeMock:
    """Turns a line of text into alternating-case "mocking" text.

        Args:
            line: The text to transform.
    """
    def __init__(self, line):
        """Store the line and make sure logging is configured."""
        self.line = line
        configure_logging()

    def generate_mock(self):
        """Upper-case every character at an odd index.

            Returns:
                The transformed text, or None if an error occurred (the error is
                logged).
        """
        try:
            result = ""
            for i in range(len(self.line)):
                if i % 2 == 1:  # Every other character (odd indices)
                    result += self.line[i].upper()
                else:  # Leave the rest unchanged
                    result += self.line[i]
            return result
        except Exception as e:
            logging.error(f"Exception in generating mock: {e}")
            return None  # Return None in case of an error

