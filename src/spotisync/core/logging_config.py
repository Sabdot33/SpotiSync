import logging
import os
from .config import read_create_config

def setup_logging():
    """Configure logging based on the debug setting in config.ini"""
    config = read_create_config()
    debug_mode = config.getboolean('settings', 'debug', fallback=False)
    
    # Create logs directory if it doesn't exist
    logs_dir = 'logs'
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # Set up logging format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Configure root logger for SpotiSync
    logger = logging.getLogger('spotisync')
    logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)
    
    # Clear any existing handlers
    logger.handlers = []
    
    # File handler for SpotiSync logs
    log_file = 'debug.log' if debug_mode else 'spotisync.log'
    file_handler = logging.FileHandler(
        os.path.join(logs_dir, log_file),
        mode='a',
        encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(console_handler)
    
    # Prevent propagation to avoid duplicate logs
    logger.propagate = False
    
    if debug_mode:
        logger.debug('Debug logging enabled')
    else:
        logger.info('Normal logging mode')
    
    return logger