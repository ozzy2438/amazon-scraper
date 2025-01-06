"""Utility functions for the Amazon scraper."""

import logging
import os
from typing import Optional
from urllib.parse import urljoin

def setup_logging(log_file: str, log_level: str) -> None:
    """
    Set up logging configuration.
    
    Args:
        log_file: Path to the log file
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def clean_url(base_url: str, path: str) -> str:
    """
    Clean and join URL components.
    
    Args:
        base_url: Base URL of the website
        path: Path component of the URL
        
    Returns:
        Cleaned and joined URL
    """
    return urljoin(base_url, path)

def clean_text(text: Optional[str]) -> str:
    """
    Clean text by removing extra whitespace and newlines.
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    if text is None:
        return ""
    return " ".join(text.split())

def ensure_dir(directory: str) -> None:
    """
    Ensure a directory exists, create it if it doesn't.
    
    Args:
        directory: Path to the directory
    """
    os.makedirs(directory, exist_ok=True) 