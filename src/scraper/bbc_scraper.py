"""BBC News Scraper using Selenium WebDriver."""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dateutil import parser
import random
import time
import os
import json
import csv
from datetime import datetime
import requests
from typing import List, Dict
from bs4 import BeautifulSoup
from collections import Counter
import re

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
        """Improved page scrolling with dynamic content loading."""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        for _ in range(3):  # 3 kez scroll dene
            # Smooth scroll
            current_height = 0
            while current_height < last_height:
                self.driver.execute_script(f"window.scrollTo(0, {current_height});")
                current_height += random.randint(100, 300)
                time.sleep(0.1)
            
            # Dinamik içeriğin yüklenmesi için bekle
            time.sleep(random.uniform(1.5, 3))
            
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
            json_path = os.path.join("data", f"{filename}.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(articles, f, ensure_ascii=False, indent=2)
            
            # Save as CSV
            csv_path = os.path.join("data", f"{filename}.csv")
            with open(csv_path, "w", encoding="utf-8", newline="") as f:
                # CSV başlıklarını belirle
                fieldnames = [
                    "title", "description", "link", "date", "category", 
                    "author", "image_url", "related_articles", "content_preview"
                ]
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                # Her makaleyi CSV'ye yaz
                for article in articles:
                    # Liste ve sözlük tipindeki verileri stringe çevir
                    row = {
                        "title": article["title"],
                        "description": article["description"],
                        "link": article["link"],
                        "date": article["date"],
                        "category": article["category"],
                        "author": article["author"],
                        "image_url": ", ".join(article["image_url"]),
                        "related_articles": json.dumps(article["related_articles"], ensure_ascii=False),
                        "content_preview": article["content_preview"]
                    }
                    writer.writerow(row)
                    
            print(f"\nMakaleler kaydedildi:")
            print(f"JSON: {json_path}")
            print(f"CSV: {csv_path}")
            print(f"\nToplam {len(articles)} makale kaydedildi.")
            
        except Exception as e:
            print(f"Dosya kaydederken hata oluştu: {str(e)}")
            raise e  # Hatayı yukarı fırlat
            
    def scrape_news(self, query, max_articles=100):
        try:
            articles_data = []
            processed_urls = set()
            page = 1
            
            while len(articles_data) < max_articles:
                # Sayfa URL'sini oluştur
                url = f"{self.base_url}?q={query}&page={page}"
                print(f"\nSayfa {page} taranıyor...")
                self.driver.get(url)
                
                # Sayfanın yüklenmesini bekle
                WebDriverWait(self.driver, 20).until(
                    lambda driver: driver.execute_script("return document.readyState") == "complete"
                )
                time.sleep(3)
                
                # Yeni seçiciler
                article_selectors = [
                    "div.ssrcss-1f3bvyz-Stack",  # Ana makale container
                    "div.gs-c-promo"  # Alternatif container
                ]
                
                articles_found_on_page = False
                
                for selector in article_selectors:
                    articles = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for article in articles:
                        try:
                            # Başlık ve link için seçiciler
                            title_link = article.find_element(By.CSS_SELECTOR, "a")
                            title = title_link.get_attribute("aria-label") or title_link.text.strip()
                            link = title_link.get_attribute("href")
                            
                            # Description için seçici
                            try:
                                description = article.find_element(By.CSS_SELECTOR, "p.ssrcss-1q0x1qg-Paragraph").text.strip()
                            except:
                                description = ""
                                
                            if not title or not link or link in processed_urls:
                                continue
                                
                            articles_found_on_page = True
                            
                            # Tarihi şimdi olarak ayarla
                            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            
                            article_data = {
                                "title": title,
                                "description": description,
                                "link": link,
                                "date": date,
                                "category": "Technology",
                                "author": "BBC News",
                                "image_url": [],
                                "related_articles": self.get_related_articles(link),
                                "content_preview": description
                            }
                            
                            articles_data.append(article_data)
                            processed_urls.add(link)
                            print(f"Makale eklendi ({len(articles_data)}/{max_articles}): {title}")
                            
                            if len(articles_data) >= max_articles:
                                break
                                
                        except Exception as e:
                            print(f"Makale işlenirken hata: {str(e)}")
                            continue
                            
                    if len(articles_data) >= max_articles:
                        break
                        
                # Eğer sayfada hiç makale bulunamadıysa veya max sayıya ulaşıldıysa döngüyü bitir
                if not articles_found_on_page or len(articles_data) >= max_articles:
                    break
                    
                # Sonraki sayfaya geç
                page += 1
                print(f"Sonraki sayfaya geçiliyor (Sayfa {page})...")
                
            if not articles_data:
                print("\nHiç makale bulunamadı!")
                print("Öneriler:")
                print("1. Arama terimini değiştirin")
                print("2. Farklı bir zamanda deneyin")
                print("3. İnternet bağlantınızı kontrol edin")
                
            return articles_data
            
        except Exception as e:
            print(f"Haber toplama sırasında hata oluştu: {str(e)}")
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

    def get_related_articles(self, article_url: str) -> List[Dict]:
        """Get related articles from the article page."""
        try:
            response = requests.get(article_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # İlgili makale seçicileri
                related_articles = []
                
                # Tüm linkleri bul
                links = soup.find_all('a', href=True)
                
                for link in links:
                    href = link.get('href', '')
                    # Sadece BBC news linklerini al
                    if '/news/' in href and href != article_url:
                        title = link.text.strip()
                        if title and href not in [a['url'] for a in related_articles]:
                            if not href.startswith('http'):
                                href = f"https://www.bbc.co.uk{href}"
                            related_articles.append({
                                'title': title,
                                'url': href
                            })
                            if len(related_articles) >= 3:
                                break
                                
                return related_articles[:3]
                
        except Exception as e:
            print(f"Error getting related articles: {str(e)}")
            
        return []
