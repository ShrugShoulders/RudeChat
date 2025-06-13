#!/usr/bin/env python3

from rudechat4.shared_imports import *
from rudechat4.global_variables import *

def configure_logging():
   # Log file path within the script directory
    log_file = os.path.join(G_CONFIG_DIR, 'RudeChat4.log')
        
    # Configure logging only if not already configured
    if not logging.getLogger().hasHandlers():
        # Create handlers
        console_handler = logging.StreamHandler()
        file_handler = logging.FileHandler(log_file)
            
        # Set levels and formatters
        console_handler.setLevel(logging.DEBUG)
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
            
        # Add handlers to the logger
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)