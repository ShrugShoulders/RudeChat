import os
import logging

def configure_logging():
    # Get the script directory
    script_directory = os.path.dirname(os.path.abspath(__file__))
        
    # Log file path within the script directory
    log_file = os.path.join(script_directory, 'RudeChat3.log')
        
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