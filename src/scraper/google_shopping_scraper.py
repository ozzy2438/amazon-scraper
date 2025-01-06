"""Google Shopping Scraper using Selenium WebDriver."""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random
import time
import os
import json
from datetime import datetime
from typing import List, Dict

class GoogleShoppingScraper:
    """A class to scrape products from Google Shopping."""
    
    def __init__(self):
        """Initialize the Google Shopping scraper."""
        self.driver = self._setup_driver()
        self.wait = WebDriverWait(self.driver, 10)
        self.base_url = "https://www.google.com/search"
        
    def _setup_driver(self):
        """Set up Chrome driver with custom options."""
        options = Options()
        
        # Add random user agent
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        options.add_argument(f'user-agent={random.choice(user_agents)}')
        
        # Add additional options to avoid detection
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-notifications')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Set ChromeDriver path
        chromedriver_path = "/opt/homebrew/bin/chromedriver"
        if not os.path.exists(chromedriver_path):
            raise Exception("ChromeDriver not found. Please install it first.")
            
        service = Service(executable_path=chromedriver_path)
        driver = webdriver.Chrome(service=service, options=options)
        
        # Execute CDP commands to avoid detection
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": random.choice(user_agents)})
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """
        })
        
        return driver
        
    def scrape_products(self, query: str, max_products: int = 50) -> List[Dict]:
        """Scrape products from Google Shopping."""
        try:
            products_data = []
            processed_urls = set()
            page = 1
            
            while len(products_data) < max_products:
                # URL'yi doğru parametrelerle oluştur
                params = {
                    'q': query.replace(" ", "+"),  # Boşlukları + ile değiştir
                    'tbm': 'shop',
                    'hl': 'en',
                    'gl': 'us',
                    'start': (page-1)*40,
                    'sa': 'X',
                    'ved': '0ahUKEwi',
                    'source': 'lnms'
                }
                
                url = f"{self.base_url}?" + "&".join(f"{k}={v}" for k, v in params.items())
                print(f"\nSayfa {page} taranıyor: {url}")
                self.driver.get(url)
                
                # Sayfanın tam yüklenmesini bekle
                time.sleep(5)
                
                # İlk scroll öncesi ürünleri bekle
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.sh-dgr__content, div.sh-dlr__list-result"))
                    )
                except:
                    print("İlk ürünler yüklenemedi, devam ediliyor...")
                
                # Smooth scroll
                print("Sayfa scroll ediliyor...")
                for _ in range(5):  # 5 kez scroll
                    try:
                        # Yumuşak scroll
                        height = self.driver.execute_script("return document.body.scrollHeight")
                        for i in range(0, height, 100):
                            self.driver.execute_script(f"window.scrollTo(0, {i});")
                            time.sleep(0.1)
                        time.sleep(2)  # Her scroll sonrası bekle
                    except:
                        print("Scroll hatası!")
                        break
                
                # En güncel selektörler
                product_selectors = [
                    "div.sh-dgr__content",
                    "div.sh-dlr__list-result",
                    "div.KZmu8e",
                    "div[jscontroller='O8k1Cd']",
                    "div.sh-pr__product-result",
                    "div.u30d4",
                    "div.sh-dla__content",
                    "div[data-docid]"  # Ürün ID'si olan elementler
                ]
                
                # Tüm ürünleri topla
                all_products = []
                for selector in product_selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            print(f"{len(elements)} ürün bulundu ({selector})")
                            all_products.extend(elements)
                    except Exception as e:
                        print(f"Selektör hatası ({selector}): {str(e)}")
                
                # Tekrarlanan ürünleri temizle
                products = list(set(all_products))
                
                if not products:
                    print("Alternatif arama yapılıyor...")
                    try:
                        # Ana container'ı bul
                        main = self.driver.find_element(By.ID, "main")
                        # Tüm potansiyel ürün elementlerini al
                        products = main.find_elements(By.CSS_SELECTOR, "div[jsdata]")
                    except:
                        pass
                
                if not products:
                    print("Bu sayfada ürün bulunamadı!")
                    self._save_debug_info(page)
                    break
                
                print(f"Toplam {len(products)} benzersiz ürün bulundu.")
                
                # Her ürünü işle
                for product in products:
                    try:
                        # Ürünü görünür yap ve bekle
                        self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", product)
                        time.sleep(0.5)
                        
                        product_data = self._extract_product_data(product)
                        
                        if not product_data or product_data["url"] in processed_urls:
                            continue
                        
                        products_data.append(product_data)
                        processed_urls.add(product_data["url"])
                        
                        print(f"Ürün eklendi ({len(products_data)}/{max_products}): {product_data['title'][:50]}...")
                        
                        if len(products_data) >= max_products:
                            break
                            
                    except Exception as e:
                        print(f"Ürün işlenirken hata: {str(e)}")
                        continue
                
                if len(products_data) >= max_products:
                    break
                
                # Sonraki sayfa kontrolü
                try:
                    next_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.ID, "pnnext"))
                    )
                    self.driver.execute_script("arguments[0].click();", next_button)
                    time.sleep(3)
                    page += 1
                except:
                    print("Sonraki sayfa bulunamadı.")
                    break
            
            return products_data
            
        except Exception as e:
            print(f"Ürün toplama sırasında hata oluştu: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def _scroll_page(self):
        """Scroll the page to load dynamic content."""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
    
    def _find_products(self, container):
        """Find product elements using multiple selectors."""
        selectors = [
            "div.sh-dgr__content",  # Main product container
            "div.u30d4",           # Product grid item
            "div.i0X6df",         # Product list item
            "div.KZmu8e",         # Shopping item
            "div[jscontroller='O8k1Cd']", # Product card
            "div.sh-dlr__list-result",  # List view result
            "div.sh-dla__content",  # Alternative product container
            "div.sh-pr__product-container" # Product container
        ]
        
        for selector in selectors:
            try:
                elements = container.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"Found {len(elements)} products with selector: {selector}")
                    return elements
            except Exception as e:
                print(f"Selector error ({selector}): {str(e)}")
                continue
        
        return []
    
    def _save_debug_info(self, page):
        """Save debug information."""
        try:
            debug_file = f"debug_page_{page}.html"
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            print(f"Debug info saved to: {debug_file}")
        except Exception as e:
            print(f"Error saving debug info: {str(e)}")
    
    def _go_to_next_page(self):
        """Attempt to go to next page."""
        try:
            next_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.ID, "pnnext"))
            )
            next_button.click()
            time.sleep(2)
            return True
        except:
            print("No next page found or not clickable.")
            return False
            
    def _extract_product_data(self, product) -> Dict:
        """Extract data from a product element."""
        try:
            # Updated selectors for product data
            url_selectors = [
                "a.Lq5OHe",           # Main product link
                "a[data-item-id]",    # Product with ID
                "a[jsname]",          # Generic product link
                "a[href*='shopping/product']",  # Shopping product link
                "a.shntl"            # Alternative product link
            ]
            
            title_selectors = [
                "h3.tAxDx",          # Main title
                "div.EI11Pd",        # Product name
                "span.pymv4e",       # Title text
                "a[aria-label]",     # Link with label
                "h3.r2ido"          # Alternative title
            ]
            
            price_selectors = [
                "span.a8Pemb",        # Main price
                "span[aria-label*='$']", # Price with label
                "span.T14wmb",        # Sale price
                "span.kHxwFf"         # Alternative price
            ]
            
            # Extract URL and ID
            url = None
            product_id = None
            for selector in url_selectors:
                try:
                    url_elem = product.find_element(By.CSS_SELECTOR, selector)
                    url = url_elem.get_attribute("href")
                    product_id = (url_elem.get_attribute("data-item-id") or 
                                url_elem.get_attribute("jsname") or 
                                str(hash(url)))
                    if url:
                        break
                except:
                    continue
            
            if not url:
                return None
            
            # Extract title
            title = None
            for selector in title_selectors:
                try:
                    title_elem = product.find_element(By.CSS_SELECTOR, selector)
                    title = (title_elem.get_attribute("aria-label") or 
                            title_elem.text.strip())
                    if title:
                        break
                except:
                    continue
            
            if not title:
                return None
            
            # Extract price
            price = None
            for selector in price_selectors:
                try:
                    price_elem = product.find_element(By.CSS_SELECTOR, selector)
                    price_text = price_elem.text.strip()
                    if price_text:
                        # Remove currency symbol and convert to float
                        price = float(price_text.replace("$", "").replace(",", ""))
                        break
                except:
                    continue
            
            # Extract merchant info
            merchant = None
            try:
                merchant_elem = product.find_element(By.CSS_SELECTOR, "div.aULzUe")
                merchant = merchant_elem.text.strip()
            except:
                pass
            
            return {
                "url": url,
                "product_id": product_id,
                "title": title,
                "price": price,
                "merchant": merchant,
                "currency": "USD"
            }
            
        except Exception as e:
            print(f"Error extracting product data: {str(e)}")
            return None
            
    def save_results(self, products: List[Dict], filename: str = None):
        """Save scraped products to JSON file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"google_shopping_{timestamp}"
            
        try:
            # Create data directory if it doesn't exist
            os.makedirs("data", exist_ok=True)
            
            # Save as JSON
            json_path = os.path.join("data", f"{filename}.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(products, f, ensure_ascii=False, indent=2)
                
            print(f"\nProducts saved:")
            print(f"JSON: {json_path}")
            print(f"\nTotal {len(products)} products saved.")
            
        except Exception as e:
            print(f"Error saving file: {str(e)}")
            raise e
            
    def close(self):
        """Close the browser."""
        if self.driver:
            self.driver.quit()
