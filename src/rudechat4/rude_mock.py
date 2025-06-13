#!/usr/bin/env python3

from rudechat4.shared_imports import *
from rudechat4.rude_logger import configure_logging

class RudeMock:
    def __init__(self, line):
        self.line = line
        configure_logging()

    def generate_mock(self):
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

