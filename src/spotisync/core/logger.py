import logging
import os

def setup_logging(module_name):
    """Set up logging configuration for the given module.

    Args:
        module_name (str): The name of the module requesting logging setup.

    Returns:
        logging.Logger: Configured logger instance for the module.
    """
    logger = logging.getLogger(module_name)
    
    # Only configure if the logger hasn't been set up
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        
        # Create formatters
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # Create handlers
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Create logs directory if it doesn't exist
        logs_dir = 'logs'
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
        
        # File handler for general logs
        file_handler = logging.FileHandler(
            os.path.join(logs_dir, 'spotisync.log'),
            mode='a',
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Prevent propagation to avoid duplicate logs
        logger.propagate = False
    
    return logger