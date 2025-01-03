"""Configuration settings for the Amazon scraper."""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

@dataclass
class Settings:
    """Settings class for the Amazon scraper."""
    
    AMAZON_BASE_URL: str
    CHROME_DRIVER_PATH: Optional[str]
    HEADLESS_MODE: bool
    OUTPUT_FORMAT: str
    OUTPUT_DIR: str
    MAX_PAGES: int
    SCROLL_PAUSE_TIME: int
    REQUEST_TIMEOUT: int
    LOG_LEVEL: str
    LOG_FILE: str

    @classmethod
    def from_env(cls) -> 'Settings':
        """Create Settings instance from environment variables."""
        load_dotenv()
        
        return cls(
            AMAZON_BASE_URL=os.getenv('AMAZON_BASE_URL', 'https://www.amazon.com'),
            CHROME_DRIVER_PATH=os.getenv('CHROME_DRIVER_PATH'),
            HEADLESS_MODE=os.getenv('HEADLESS_MODE', 'True').lower() == 'true',
            OUTPUT_FORMAT=os.getenv('OUTPUT_FORMAT', 'csv'),
            OUTPUT_DIR=os.getenv('OUTPUT_DIR', 'data'),
            MAX_PAGES=int(os.getenv('MAX_PAGES', '10')),
            SCROLL_PAUSE_TIME=int(os.getenv('SCROLL_PAUSE_TIME', '2')),
            REQUEST_TIMEOUT=int(os.getenv('REQUEST_TIMEOUT', '30')),
            LOG_LEVEL=os.getenv('LOG_LEVEL', 'INFO'),
            LOG_FILE=os.getenv('LOG_FILE', 'logs/scraper.log')
        ) 