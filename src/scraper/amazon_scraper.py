"""
Amazon Web Scraper using Selenium WebDriver.
This module contains the main scraper class for extracting product data from Amazon.
"""

import logging
import time
from typing import Dict, List, Optional
import os
import re

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
)
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

    def _setup_driver(self) -> webdriver.Chrome:
        """Set up and configure the Chrome WebDriver."""
        chrome_options = Options()
        if self.settings.HEADLESS_MODE:
            chrome_options.add_argument("--headless=new")
            
        # Add additional options for stability
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        
        # ChromeDriver'ın yolunu belirle
        chromedriver_path = "/opt/homebrew/bin/chromedriver"
        if not os.path.exists(chromedriver_path):
            raise Exception("ChromeDriver bulunamadı. Lütfen 'brew install chromedriver' komutunu çalıştırın.")
            
        service = Service(executable_path=chromedriver_path)
        
        return webdriver.Chrome(service=service, options=chrome_options)

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
        # Remove multiple spaces and newlines
        text = " ".join(text.split())
        # Remove unwanted characters
        text = text.replace("\\", "").replace("\"", "").strip()
        return text

    def _extract_price(self, soup: BeautifulSoup) -> str:
        """Extract price information using multiple methods."""
        price = "N/A"
        
        # Method 1: Direct price element with common selectors
        price_selectors = [
            'span.a-price span.a-offscreen',
            'span.a-price-whole',
            'span[data-a-color="price"] span.a-offscreen',
            'span.a-price',
            'span.a-color-price',
            'span.a-price span[aria-hidden="true"]',
            'span[data-a-strike="true"]',  # For original prices
            'span.apexPriceToPay span.a-offscreen'  # For deal prices
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
        
        # Method 3: Look for price in any text content with regex pattern
        if price == "N/A":
            price_pattern = r'\$[\d,]+\.?\d{0,2}'
            import re
            price_matches = re.findall(price_pattern, soup.get_text())
            if price_matches:
                # Get the first valid price
                for match in price_matches:
                    try:
                        # Remove commas and convert to float to validate
                        float(match.replace('$', '').replace(',', ''))
                        price = match
                        break
                    except ValueError:
                        continue
        
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
            soup = BeautifulSoup(product_element.get_attribute('innerHTML'), 'html.parser')
            
            # Extract detailed title with all product information
            title = "N/A"
            
            # First try to get the full product title from the product link
            link_element = soup.select_one('h2 a.a-link-normal')
            if link_element:
                title_from_link = link_element.get('title', '') or link_element.text
                if title_from_link and len(title_from_link.strip()) > 10:  # Ensure it's a meaningful title
                    title = self._clean_text(title_from_link)
            
            # If we didn't get a good title from the link, try other selectors
            if title == "N/A" or len(title.split()) < 4:
                title_selectors = [
                    'h2 a-size-mini a-spacing-none a-color-base s-line-clamp-4',  # Extended product description
                    '.a-size-medium.a-color-base.a-text-normal',
                    '.a-size-base-plus.a-color-base.a-text-normal',
                    'h2 .a-link-normal',
                    'h2 span',
                    '.a-text-normal',
                    '[data-cy="title-recipe"]'
                ]
                
                for selector in title_selectors:
                    title_elements = soup.select(selector)
                    for element in title_elements:
                        # Try to get the most detailed text
                        title_text = element.get('aria-label', '') or element.get('title', '') or element.text
                        if title_text and len(title_text.strip()) > len(title):
                            title = self._clean_text(title_text)
            
            # Additional title cleaning and formatting
            if title != "N/A":
                # Remove redundant "by Amazon" or similar phrases
                title = re.sub(r'\s+by Amazon\b', '', title, flags=re.IGNORECASE)
                
                # Clean up multiple spaces and special characters
                title = re.sub(r'\s+', ' ', title)
                title = title.replace(' ,', ',')
                
                # Remove any HTML entities
                title = re.sub(r'&[a-zA-Z]+;', ' ', title)
                
                # Remove duplicate product names
                parts = title.split('-')
                if len(parts) > 1:
                    # Keep only unique parts
                    unique_parts = []
                    seen = set()
                    for part in parts:
                        cleaned_part = part.strip().lower()
                        if cleaned_part not in seen and len(cleaned_part) > 0:
                            seen.add(cleaned_part)
                            unique_parts.append(part.strip())
                    title = ' - '.join(unique_parts)
                
                # Ensure proper spacing around hyphens
                title = re.sub(r'\s*-\s*', ' - ', title)
                
                # Remove any remaining unnecessary whitespace
                title = ' '.join(title.split())
                
                # If title is still too short, try to get more information from the product card
                if len(title.split()) < 4:
                    # Look for additional product details
                    details_selectors = [
                        '.a-size-base:not(.a-color-price)',
                        '.a-color-base:not(.a-color-price)',
                        '.a-text-normal:not(.a-color-price)'
                    ]
                    
                    additional_info = []
                    for selector in details_selectors:
                        for element in soup.select(selector):
                            text = self._clean_text(element.text)
                            if text and text not in title and len(text) > 5:
                                additional_info.append(text)
                    
                    if additional_info:
                        title = f"{title} - {' - '.join(additional_info)}"
            
            # Extract product link with improved cleaning
            link = "N/A"
            link_selectors = [
                'h2 a[href]',
                'a.a-link-normal[href]',
                'a[href*="/dp/"]',  # Product detail page links
                'a[href*="/gp/"]'   # Alternative product page links
            ]
            for selector in link_selectors:
                link_element = soup.select_one(selector)
                if link_element and 'href' in link_element.attrs:
                    link = self._clean_url(f"{self.settings.AMAZON_BASE_URL}{link_element['href']}")
                    break
            
            # Extract price using the dedicated method
            price = self._extract_price(soup)
            
            # Extract rating with improved accuracy
            rating = "N/A"
            rating_selectors = [
                'i.a-icon-star-small span',
                'i.a-icon-star span',
                'span[aria-label*="out of 5 stars"]',
                'span[class*="a-icon-alt"]',
                'a[title*="out of 5 stars"]'
            ]
            for selector in rating_selectors:
                rating_element = soup.select_one(selector)
                if rating_element:
                    rating_text = rating_element.get('aria-label', '') or rating_element.get('title', '') or rating_element.text
                    if 'out of 5' in rating_text.lower():
                        try:
                            rating = rating_text.split('out of')[0].strip()
                            float(rating)  # Validate it's a number
                        except (ValueError, IndexError):
                            continue
                        break
            
            # Extract review count with improved cleaning
            review_count = "0"
            review_selectors = [
                'span[aria-label*="stars"] + span',
                'span.a-size-base.s-underline-text',
                'span[aria-label*="total ratings"]',
                'span[aria-label*="total reviews"]',
                'a[href*="customerReviews"] span'
            ]
            for selector in review_selectors:
                review_element = soup.select_one(selector)
                if review_element:
                    count = re.sub(r'[^\d]', '', review_element.text.strip())
                    if count.isdigit():
                        review_count = count
                        break
            
            # Extract delivery information with more detail
            delivery = "N/A"
            delivery_selectors = [
                'span[data-component-type="s-delivery-badge"] span',
                'span.a-text-bold:not([class*="a-color"])',
                'span[aria-label*="Delivery"]',
                'span.a-color-base.a-text-bold',
                'div[data-component-type="s-delivery-prediction"]',
                'span[data-component-type="s-estimated-delivery"]'
            ]
            for selector in delivery_selectors:
                delivery_element = soup.select_one(selector)
                if delivery_element:
                    delivery_text = delivery_element.get('aria-label', '') or delivery_element.text
                    delivery = self._clean_text(delivery_text)
                    # Extract specific delivery date if available
                    date_match = re.search(r'(delivery|arrives|get it)\s+by\s+([^\.]+)', delivery.lower())
                    if date_match:
                        delivery = f"Delivery by {date_match.group(2).strip().title()}"
                    break
            
            # Extract detailed stock status
            stock_status = "In Stock"
            stock_selectors = [
                'span[aria-label*="stock"]',
                'span.a-color-price',
                'span[data-a-color="price"]',
                'span[aria-label*="left in stock"]',
                'span.a-size-base.a-color-price',
                'span[data-component-type="s-stock-status"]'
            ]
            for selector in stock_selectors:
                stock_element = soup.select_one(selector)
                if stock_element:
                    status_text = stock_element.get('aria-label', '') or stock_element.text
                    if "left in stock" in status_text.lower():
                        stock_status = self._clean_text(status_text)
                    elif "out of stock" in status_text.lower():
                        stock_status = "Out of Stock"
                    elif "only" in status_text.lower() and "left" in status_text.lower():
                        stock_status = self._clean_text(status_text)
                    break
            
            # Check if product is sponsored with improved detection
            sponsored = bool(soup.select_one('span[data-component-type="s-sponsored-label"], span.s-label-popover-default, span[class*="sponsored"]'))
            
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
            page = 1
            
            while page <= max_pages:
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
                    
                    print(f"\nSayfa {page}: {len(product_grid)} ürün bulundu.")
                    
                    # Try to go to next page
                    try:
                        # Wait for the next button to be clickable
                        next_button = self.wait.until(
                            EC.element_to_be_clickable(
                                (By.CSS_SELECTOR, '.s-pagination-next:not(.s-pagination-disabled)')
                            )
                        )
                        
                        # Scroll the next button into view
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                        time.sleep(1)  # Wait for scroll
                        
                        # Click using JavaScript
                        self.driver.execute_script("arguments[0].click();", next_button)
                        
                        # Wait for the page to load
                        time.sleep(2)
                        
                        # Verify page change by checking URL or page number
                        if "page=" in self.driver.current_url:
                            page += 1
                            progress.update(task, advance=1)
                        else:
                            print("\nSayfa değiştirilemedi, tekrar deneniyor...")
                            continue
                            
                    except Exception as e:
                        print(f"\nSon sayfaya ulaşıldı veya hata oluştu: {str(e)}")
                        break
                    
                except Exception as e:
                    print(f"\nSayfa {page} işlenirken hata oluştu: {str(e)}")
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
