"""
Amazon Web Scraper using Selenium WebDriver.
This module contains the main scraper class for extracting product data from Amazon.
"""

import logging
import time
from typing import Dict, List, Optional
import os

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
)
from webdriver_manager.firefox import GeckoDriverManager
from bs4 import BeautifulSoup
import pandas as pd
from rich.progress import Progress
from rich.console import Console

from config.settings import Settings

logger = logging.getLogger(__name__)
console = Console()

class AmazonScraper:
    """A class to scrape product data from Amazon using Selenium WebDriver."""

    def __init__(self, settings: Settings):
        """Initialize the scraper with settings."""
        self.settings = settings
        self.driver = self._setup_driver()
        self.wait = WebDriverWait(self.driver, settings.REQUEST_TIMEOUT)
        self.products: List[Dict] = []

    def _setup_driver(self) -> webdriver.Firefox:
        """Set up and configure the Firefox WebDriver."""
        firefox_options = Options()
        if self.settings.HEADLESS_MODE:
            firefox_options.add_argument("--headless")
        
        service = Service(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=firefox_options)
        driver.set_window_size(1920, 1080)
        return driver

    def search_products(self, query: str) -> None:
        """
        Search for products on Amazon using the provided query.
        
        Args:
            query: The search term to look for on Amazon.
        """
        try:
            self.driver.get(self.settings.AMAZON_BASE_URL)
            search_box = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text'][name='field-keywords']"))
            )
            search_box.clear()
            search_box.send_keys(query)
            search_box.send_keys(Keys.RETURN)
        except TimeoutException:
            logger.error("Timeout while searching for products")
            raise
        except Exception as e:
            logger.error(f"Error during product search: {str(e)}")
            raise

    def _scroll_page(self) -> None:
        """Scroll the page to load all dynamic content."""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(self.settings.SCROLL_PAUSE_TIME)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def _clean_url(self, url: str) -> str:
        """Clean URL by removing escape characters and query parameters."""
        if not url or url == "N/A":
            return "N/A"
        
        # Remove escape characters
        url = url.replace("\\/", "/")
        
        # Remove query parameters after first occurrence of /ref=
        if "/ref=" in url:
            url = url.split("/ref=")[0]
            
        # Replace encoded characters
        replacements = {
            "%E2%80%91": "-",
            "%E2%80%93": "-",
            "%E2%80%94": "-",
            "%20": " ",
            "%2C": ",",
            "%2F": "/",
            "%3A": ":",
            "%3F": "?",
            "%3D": "=",
            "%26": "&"
        }
        for encoded, decoded in replacements.items():
            url = url.replace(encoded, decoded)
        
        return url

    def _clean_text(self, text: str) -> str:
        """Clean text by removing extra whitespace and special characters."""
        if not text or text == "N/A":
            return "N/A"
        return " ".join(text.split())

    def _extract_price(self, soup: BeautifulSoup) -> str:
        """Extract price information using multiple methods."""
        price = "N/A"
        
        # Method 1: Direct price element
        price_selectors = [
            'span.a-price span.a-offscreen',
            'span.a-price-whole',
            'span[data-a-color="price"] span.a-offscreen',
            'span.a-price'
        ]
        
        for selector in price_selectors:
            price_element = soup.select_one(selector)
            if price_element and price_element.text.strip():
                price = self._clean_text(price_element.text)
                if "$" not in price and price != "N/A":
                    price = f"${price}"
                break
        
        # Method 2: Look for price in aria-label attributes
        if price == "N/A":
            elements_with_price = soup.find_all(lambda tag: tag.get('aria-label', '').lower().startswith('$'))
            if elements_with_price:
                price = elements_with_price[0]['aria-label'].split()[0]
        
        # Method 3: Look for price in any text content
        if price == "N/A":
            price_pattern = r'\$[\d,]+\.?\d{0,2}'
            import re
            price_matches = re.findall(price_pattern, soup.get_text())
            if price_matches:
                price = price_matches[0]
        
        return price

    def _extract_product_data(self, product_element) -> Optional[Dict]:
        """
        Extract product data from a single product element.
        
        Args:
            product_element: The WebElement containing product information.
            
        Returns:
            Dictionary containing product data or None if extraction fails.
        """
        try:
            # Initialize BeautifulSoup for better parsing
            soup = BeautifulSoup(product_element.get_attribute('innerHTML'), 'html.parser')
            
            # Extract title - try multiple selectors
            title = "N/A"
            title_selectors = [
                'h2 a span.a-text-normal',
                'h2 span.a-text-normal',
                'span.a-size-medium',
                'span.a-size-base-plus',
                'h2 a span'
            ]
            for selector in title_selectors:
                title_element = soup.select_one(selector)
                if title_element and title_element.text.strip():
                    title = self._clean_text(title_element.text)
                    break
            
            # Extract product link
            link = "N/A"
            link_selectors = [
                'h2 a[href]',
                'a.a-link-normal[href]'
            ]
            for selector in link_selectors:
                link_element = soup.select_one(selector)
                if link_element and 'href' in link_element.attrs:
                    link = self._clean_url(f"{self.settings.AMAZON_BASE_URL}{link_element['href']}")
                    break
            
            # Extract price using the dedicated method
            price = self._extract_price(soup)
            
            # Extract rating
            rating = "N/A"
            rating_selectors = [
                'i.a-icon-star-small span',
                'i.a-icon-star span',
                'span[aria-label*="out of 5 stars"]',
                'span[class*="a-icon-alt"]'
            ]
            for selector in rating_selectors:
                rating_element = soup.select_one(selector)
                if rating_element:
                    rating_text = rating_element.get('aria-label', rating_element.text)
                    rating = rating_text.split()[0]
                    break
            
            # Extract review count
            review_count = "0"
            review_selectors = [
                'span[aria-label*="stars"] + span',
                'span.a-size-base.s-underline-text',
                'span[aria-label*="total ratings"]',
                'span[aria-label*="total reviews"]'
            ]
            for selector in review_selectors:
                review_element = soup.select_one(selector)
                if review_element:
                    count = review_element.text.strip().replace(',', '')
                    if count.isdigit():
                        review_count = count
                        break
            
            # Extract delivery information
            delivery = "N/A"
            delivery_selectors = [
                'span[data-component-type="s-delivery-badge"] span',
                'span.a-text-bold:not([class*="a-color"])',
                'span[aria-label*="Delivery"]',
                'span.a-color-base.a-text-bold'
            ]
            for selector in delivery_selectors:
                delivery_element = soup.select_one(selector)
                if delivery_element:
                    delivery = self._clean_text(delivery_element.text)
                    break
            
            # Extract stock status
            stock_status = "In Stock"
            stock_selectors = [
                'span[aria-label*="stock"]',
                'span.a-color-price',
                'span[data-a-color="price"]'
            ]
            for selector in stock_selectors:
                stock_element = soup.select_one(selector)
                if stock_element and "left in stock" in stock_element.text.lower():
                    stock_status = self._clean_text(stock_element.text)
                    break
            
            # Check if product is sponsored
            sponsored = bool(soup.select_one('span[data-component-type="s-sponsored-label"], span.s-label-popover-default'))
            
            return {
                'title': title,
                'product_link': link,
                'price': price,
                'rating': rating,
                'review_count': review_count,
                'delivery': delivery,
                'stock_status': stock_status,
                'sponsored': sponsored
            }
            
        except Exception as e:
            logger.error(f"Error extracting product data: {str(e)}")
            return None

    def scrape_products(self, max_pages: int = None) -> List[Dict]:
        """
        Scrape product data from search results pages.
        
        Args:
            max_pages: Maximum number of pages to scrape.
            
        Returns:
            List of dictionaries containing product data.
        """
        if max_pages is None:
            max_pages = self.settings.MAX_PAGES

        with Progress() as progress:
            task = progress.add_task("[cyan]Scraping products...", total=max_pages)
            
            for page in range(max_pages):
                try:
                    self._scroll_page()
                    
                    # Wait for product grid to load
                    product_grid = self.wait.until(
                        EC.presence_of_all_elements_located(
                            (By.CSS_SELECTOR, '[data-component-type="s-search-result"]')
                        )
                    )
                    
                    # Extract data from each product
                    for product_element in product_grid:
                        product_data = self._extract_product_data(product_element)
                        if product_data:
                            self.products.append(product_data)
                    
                    # Try to go to next page
                    try:
                        next_button = self.driver.find_element(
                            By.CSS_SELECTOR, '.s-pagination-next:not(.s-pagination-disabled)'
                        )
                        next_button.click()
                        time.sleep(2)  # Wait for page load
                    except NoSuchElementException:
                        logger.info("No more pages to scrape")
                        break
                    
                    progress.update(task, advance=1)
                    
                except Exception as e:
                    logger.error(f"Error on page {page + 1}: {str(e)}")
                    break

        return self.products

    def save_results(self, filename: str) -> None:
        """
        Save scraped product data to both CSV and JSON formats.
        
        Args:
            filename: Base name of the file to save results to (without extension)
        """
        if not self.products:
            logger.warning("No products to save")
            return

        df = pd.DataFrame(self.products)
        
        # Remove any file extension from the filename
        base_filename = os.path.splitext(filename)[0]
        
        # Save as CSV
        csv_filename = f"{base_filename}.csv"
        df.to_csv(csv_filename, index=False)
        logger.info(f"Results saved to {csv_filename}")
        
        # Save as JSON
        json_filename = f"{base_filename}.json"
        df.to_json(json_filename, orient='records', indent=2)
        logger.info(f"Results saved to {json_filename}")

    def close(self) -> None:
        """Close the WebDriver and clean up resources."""
        if self.driver:
            self.driver.quit()
