"""
Logging functionality for the Kenya news scraping project.
"""
import os
import logging
from datetime import datetime


def setup_logger(name, log_file=None, level=logging.INFO):
    """
    Set up a logger with file and console handlers.
    
    Args:
        name (str): Logger name
        log_file (str): Path to log file (optional)
        level (int): Logging level
        
    Returns:
        logging.Logger: Configured logger
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers if any
    if logger.handlers:
        logger.handlers = []
    
    # Create formatters
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Create file handler if log_file is provided
    if log_file:
        # Ensure logs directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_scraper_logger(source_name):
    """
    Get a logger for a specific scraper.
    
    Args:
        source_name (str): Name of the news source
        
    Returns:
        logging.Logger: Configured logger for the scraper
    """
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    # Create log filename with date
    log_file = f"logs/{source_name}_{datetime.now().strftime('%Y%m%d')}.log"
    
    return setup_logger(f"{source_name}_scraper", log_file)