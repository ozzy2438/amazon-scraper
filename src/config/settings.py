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
    LINKEDIN_BASE_URL: str
    JOB_SEARCH_DELAY: float
    MAX_JOBS_PER_SEARCH: int
    DEFAULT_COUNTRY: str
    DEFAULT_CITY: str

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
            LOG_FILE=os.getenv('LOG_FILE', 'logs/scraper.log'),
            LINKEDIN_BASE_URL=os.getenv('LINKEDIN_BASE_URL', 'https://www.linkedin.com/jobs'),
            JOB_SEARCH_DELAY=float(os.getenv('JOB_SEARCH_DELAY', '1')),
            MAX_JOBS_PER_SEARCH=int(os.getenv('MAX_JOBS_PER_SEARCH', '100')),
            DEFAULT_COUNTRY=os.getenv('DEFAULT_COUNTRY', 'Turkey'),
            DEFAULT_CITY=os.getenv('DEFAULT_CITY', 'Istanbul')
        ) 