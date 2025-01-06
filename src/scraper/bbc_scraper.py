"""BBC News Scraper using Selenium WebDriver."""

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
import csv
from datetime import datetime

class BBCScraper:
    """A class to scrape news articles from BBC News using both Selenium and Crawl4AI."""

    def __init__(self):
        """Initialize the BBC scraper."""
        self.driver = self._setup_driver()
        self.wait = WebDriverWait(self.driver, 10)
        self.base_url = "https://www.bbc.co.uk/search"
        
    def _setup_driver(self):
        """Set up Chrome driver with custom options."""
        options = Options()
        
        # Add random user agent
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        options.add_argument(f'user-agent={random.choice(user_agents)}')
        
        # Add additional options for stability
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        # Set ChromeDriver path
        chromedriver_path = "/opt/homebrew/bin/chromedriver"
        if not os.path.exists(chromedriver_path):
            raise Exception("ChromeDriver not found. Please run 'brew install chromedriver' command.")
            
        service = Service(executable_path=chromedriver_path)
        
        return webdriver.Chrome(service=service, options=options)
        
    def _scroll_page(self):
        """Scroll the page to load all dynamic content."""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        while True:
            # Scroll down smoothly
            current_height = 0
            while current_height < last_height:
                self.driver.execute_script(f"window.scrollTo(0, {current_height});")
                current_height += random.randint(100, 200)
                time.sleep(0.1)
            
            # Wait for new content
            time.sleep(random.uniform(1, 2))
            
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
                
            last_height = new_height
            
    def save_results(self, articles, filename=None):
        """Save scraped articles to both JSON and CSV files."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bbc_news_{timestamp}"
            
        try:
            # Create data directory if it doesn't exist
            os.makedirs("data", exist_ok=True)
            
            # Save as JSON
            json_filename = f"data/{filename}.json"
            with open(json_filename, "w", encoding="utf-8") as f:
                json.dump(articles, f, ensure_ascii=False, indent=2)
            print(f"Data saved as JSON: {json_filename}")
            
            # Save as CSV
            csv_filename = f"data/{filename}.csv"
            with open(csv_filename, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=articles[0].keys() if articles else [])
                writer.writeheader()
                writer.writerows(articles)
            print(f"Data saved as CSV: {csv_filename}")
            
        except Exception as e:
            print(f"Error occurred while saving file: {str(e)}")
            
    def scrape_news(self, query, max_articles=50):
        try:
            url = f"{self.base_url}?q={query}"
            print(f"Searching for '{query}' on BBC News...")
            self.driver.get(url)
            
            # Wait for page to load
            print("Loading page...")
            WebDriverWait(self.driver, 20).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            time.sleep(3)
            
            articles_data = []
            processed_urls = set()
            page_number = 1
            
            while len(articles_data) < max_articles:
                print(f"\nScanning page {page_number}...")
                
                # Scroll and load content
                for _ in range(3):
                    self._scroll_page()
                    time.sleep(2)
                
                try:
                    # Find all article cards with multiple selectors
                    article_selectors = [
                        "div[data-testid='newport-article']",
                        "div.sc-4ea10043-1",
                        "div[data-testid='default-promo']",
                        "div.ssrcss-1f3bvyz-Stack",
                        "div.gs-c-promo"
                    ]
                    
                    articles = []
                    for selector in article_selectors:
                        try:
                            found_articles = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            if found_articles:
                                articles.extend(found_articles)
                                print(f"Found {len(found_articles)} articles with '{selector}'")
                        except Exception as e:
                            print(f"Error searching with selector '{selector}': {str(e)}")
                            continue
                    
                    print(f"\nTotal {len(articles)} articles found on this page.")
                    
                    if not articles:
                        print("No article cards found. Checking page structure...")
                        # Debug: Print page source for analysis
                        print("\nPage HTML structure:")
                        print(self.driver.page_source[:1000] + "...")  # First 1000 chars
                    
                    # Process found articles
                    unique_articles = []
                    seen_links = set()
                    
                    for article in articles:
                        if len(articles_data) >= max_articles:
                            break
                            
                        # Check if article is displayed
                        try:
                            if not article.is_displayed():
                                continue
                        except:
                            continue
                            
                        # Get article link first to check uniqueness
                        try:
                            link_element = article.find_element(By.CSS_SELECTOR, "a[href*='/news/']")
                            link = link_element.get_attribute("href")
                            if link in seen_links:
                                continue
                            seen_links.add(link)
                            unique_articles.append(article)
                        except:
                            continue
                    
                    print(f"Number of unique articles: {len(unique_articles)}")
                    
                    for article in unique_articles:
                            
                        try:
                            # Title and link - Enhanced selectors
                            try:
                                title_selectors = [
                                    "h3",
                                    "a[href*='/news/'] span",
                                    "a[href*='/news/'] p",
                                    "h3 a span",
                                    "h3 a",
                                    "a[data-testid='internal-link']"
                                ]
                                
                                title = None
                                link = None
                                
                                for selector in title_selectors:
                                    try:
                                        element = article.find_element(By.CSS_SELECTOR, selector)
                                        if selector.endswith("a"):
                                            link = element.get_attribute("href")
                                            title = element.text.strip()
                                        else:
                                            title = element.text.strip()
                                            link = element.find_element(By.XPATH, "./ancestor::a").get_attribute("href")
                                            
                                        if title and link and "/news/" in link:
                                            break
                                    except:
                                        continue
                                
                                if not title or not link or not "/news/" in link:
                                    print("Valid title/link not found")
                                    continue
                                    
                            except Exception as e:
                                print(f"Title/link not found: {str(e)}")
                                continue
                            
                            if not link or link in processed_urls or not title:
                                continue
                            
                            # Simplified date extraction
                            date = "N/A"
                            try:
                                date_selectors = [
                                    "span.card-metadata-date",
                                    "time[datetime]",
                                    "div[data-testid='timestamp'] time",
                                    "div[data-testid='timestamp'] span",
                                    "span[data-seconds]"
                                ]
                                
                                for selector in date_selectors:
                                    try:
                                        date_element = article.find_element(By.CSS_SELECTOR, selector)
                                        
                                        # Try datetime attribute
                                        datetime_attr = date_element.get_attribute("datetime")
                                        if datetime_attr:
                                            try:
                                                parsed_date = datetime.fromisoformat(datetime_attr.replace('Z', '+00:00'))
                                                date = parsed_date.strftime("%Y-%m-%d %H:%M:%S")
                                                break
                                            except ValueError:
                                                pass
                                        
                                        # Try data-seconds attribute
                                        seconds_attr = date_element.get_attribute("data-seconds")
                                        if seconds_attr and seconds_attr.isdigit():
                                            try:
                                                parsed_date = datetime.fromtimestamp(int(seconds_attr))
                                                date = parsed_date.strftime("%Y-%m-%d %H:%M:%S")
                                                break
                                            except ValueError:
                                                pass
                                                
                                        # Get text content as fallback
                                        text_content = date_element.text.strip()
                                        if text_content and date == "N/A":
                                            date = text_content
                                            
                                    except:
                                        continue
                                        
                                if date == "N/A":
                                    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    
                            except Exception as e:
                                print(f"Error extracting date: {str(e)}")
                                date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            
                            # Description - Enhanced selectors
                            try:
                                desc_selectors = [
                                    "div.sc-4ea10043-3",
                                    "p[data-testid='text-summary']",
                                    "p.ssrcss-1q0x1qg-Paragraph",
                                    "p[data-component='text-block']",
                                    "div[data-testid='story-promo-summary']"
                                ]
                                description = "N/A"
                                for selector in desc_selectors:
                                    try:
                                        desc_element = article.find_element(By.CSS_SELECTOR, selector)
                                        description = desc_element.text.strip()
                                        if description:
                                            break
                                    except:
                                        continue
                            except Exception as e:
                                print(f"Description not found: {str(e)}")
                                description = "N/A"
                            
                            # Validate article data before adding
                            if (title and link and "/news/" in link and 
                                link not in processed_urls and
                                description != "N/A"):
                                
                                article_data = {
                                    "title": title,
                                    "description": description,
                                    "link": link,
                                    "date": date
                                }
                                
                                articles_data.append(article_data)
                                processed_urls.add(link)
                                print(f"Article {len(articles_data)}/{max_articles} collected: {title}")
                                print(f"Link: {link}")
                                print(f"Date: {date}")
                                print(f"Description: {description[:100]}...")
                                print("-" * 80)
                            else:
                                print("Invalid article data - skipping")
                                if not title:
                                    print("Reason: Title not found")
                                elif not link or "/news/" not in link:
                                    print("Reason: Not a valid news link")
                                elif link in processed_urls:
                                    print("Reason: Article already processed")
                                elif description == "N/A":
                                    print("Reason: Description not found")
                            
                        except Exception as e:
                            print(f"Error while extracting article data: {str(e)}")
                            continue
                    
                    if len(articles_data) >= max_articles:
                        print(f"\nReached target number of articles ({max_articles})")
                        break
                    
                    # Next page with improved handling
                    try:
                        next_button = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "a[aria-label*='Next']"))
                        )
                        
                        if next_button.is_displayed() and next_button.is_enabled():
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                            time.sleep(2)  # Wait longer for stability
                            
                            # Try to click with JavaScript if regular click fails
                            try:
                                next_button.click()
                            except:
                                self.driver.execute_script("arguments[0].click();", next_button)
                                
                            page_number += 1
                            print(f"\nMoving to next page (Page {page_number})")
                            time.sleep(3)  # Wait for page load
                            
                            # Verify page change
                            WebDriverWait(self.driver, 10).until(
                                lambda driver: driver.execute_script("return document.readyState") == "complete"
                            )
                        else:
                            print("\nNo more pages.")
                            break
                    except Exception as e:
                        print(f"\nNext page not found: {str(e)}")
                        break
                        
                except Exception as e:
                    print(f"Error processing page: {str(e)}")
                    if "stale element" in str(e).lower():
                        print("Reloading page...")
                        self.driver.refresh()
                        time.sleep(3)
                        continue
                    break
            
            # Final results
            if articles_data:
                print(f"\nSuccessfully collected {len(articles_data)} articles!")
                print("\nLatest articles:")
                for i, article in enumerate(articles_data[-3:], 1):
                    print(f"{i}. {article['title']}")
                    print(f"   Link: {article['link']}")
                    print(f"   Date: {article['date']}")
                    print("-" * 80)
                    
                # Save results
                self.save_results(articles_data)
            else:
                print("\nNo articles found!")
                print("Please check your search term or try a different one.")
                
            return articles_data
            
        except Exception as e:
            print(f"Error occurred while collecting news: {str(e)}")
            return []
            
    def close(self):
        """Close the browser."""
        if self.driver:
            self.driver.quit() 

    def _get_article_titles(self, article):
        try:
            # First find all h2 tags in article
            title_elements = article.find_elements(By.CSS_SELECTOR, "h2, h3")
            if title_elements:
                # Get first title element
                return title_elements[0].text.strip()
            return "Title not found"
        except Exception as e:
            print(f"Title not found: {str(e)}")
            return "Title not found"

    def _get_articles(self):
        try:
            # Wait for page to fully load
            time.sleep(10)  # Wait 10 seconds
            
            # Print page HTML structure
            print("Page HTML:")
            page_source = self.driver.page_source
            print(page_source)
            
            # Find all links on page
            links = self.driver.find_elements(By.TAG_NAME, "a")
            print(f"\nTotal number of links: {len(links)}")
            
            # Filter news links
            news_links = [link for link in links if '/news/' in link.get_attribute('href')]
            print(f"Number of news links: {len(news_links)}")
            
            # Collect information for each news link
            for link in news_links:
                try:
                    title = link.text.strip()
                    if title:
                        print(f"Title found: {title}")
                        self.articles.append({
                            'title': title,
                            'link': link.get_attribute('href'),
                            'timestamp': '',
                            'summary': '',
                            'section': ''
                        })
                except Exception as e:
                    print(f"Error processing link: {str(e)}")
                    continue
            
            return len(self.articles)
        except Exception as e:
            print(f"Error getting articles: {str(e)}")
            return 0
