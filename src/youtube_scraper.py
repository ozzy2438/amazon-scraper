from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import random
import json
import os
from datetime import datetime, timedelta

class YouTubeScraper:
    def __init__(self):
        """Initialize the YouTube scraper."""
        self.driver = self._setup_driver()
        self.wait = WebDriverWait(self.driver, 10)
        
    def _setup_driver(self):
        """Set up Chrome driver with custom options."""
        options = Options()
        
        # Add random user agent
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        options.add_argument(f'user-agent={random.choice(user_agents)}')
        
        # Add additional options for security and stability
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-extensions')
        
        # Disable images and other media for faster loading
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.managed_default_content_settings.media_stream": 2,
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False
        }
        options.add_experimental_option("prefs", prefs)
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        # ChromeDriver'ın yolunu belirle
        chromedriver_path = "/opt/homebrew/bin/chromedriver"
        if not os.path.exists(chromedriver_path):
            raise Exception("ChromeDriver bulunamadı. Lütfen 'brew install chromedriver' komutunu çalıştırın.")
            
        service = Service(executable_path=chromedriver_path)
        
        return webdriver.Chrome(service=service, options=options)
        
    def _random_sleep(self, min_seconds=1, max_seconds=3):
        """Sleep for a random amount of time."""
        time.sleep(random.uniform(min_seconds, max_seconds))
        
    def _human_like_scroll(self, scroll_pause_time=1):
        """Scroll the page in a human-like manner."""
        last_height = self.driver.execute_script("return document.documentElement.scrollHeight")
        
        while True:
            # Scroll down with random distance
            scroll_distance = random.randint(100, 800)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_distance});")
            
            # Wait for new content to load
            time.sleep(scroll_pause_time)
            
            # Calculate new scroll height
            new_height = self.driver.execute_script("return document.documentElement.scrollHeight")
            
            # Break if we've reached the bottom
            if new_height == last_height:
                break
                
            last_height = new_height
            
    def _format_view_count(self, view_count_str):
        """Format view count string to integer."""
        try:
            # Remove any non-numeric characters except decimal points and K/M/B
            view_count_str = view_count_str.lower().split('view')[0].strip()
            multiplier = 1
            
            if 'b' in view_count_str:
                multiplier = 1000000000
                view_count_str = view_count_str.replace('b', '')
            elif 'm' in view_count_str:
                multiplier = 1000000
                view_count_str = view_count_str.replace('m', '')
            elif 'k' in view_count_str:
                multiplier = 1000
                view_count_str = view_count_str.replace('k', '')
                
            # Convert to float first to handle decimal points
            view_count = float(view_count_str.replace(',', ''))
            return int(view_count * multiplier)
        except:
            return 0
            
    def _format_date(self, date_str):
        """Convert relative date string to actual date."""
        try:
            date_str = date_str.lower()
            current_time = datetime.now()
            
            if 'saniye' in date_str or 'sn' in date_str:
                seconds = int(date_str.split()[0])
                return (current_time - timedelta(seconds=seconds)).strftime('%Y-%m-%d')
            elif 'dakika' in date_str or 'dk' in date_str:
                minutes = int(date_str.split()[0])
                return (current_time - timedelta(minutes=minutes)).strftime('%Y-%m-%d')
            elif 'saat' in date_str:
                hours = int(date_str.split()[0])
                return (current_time - timedelta(hours=hours)).strftime('%Y-%m-%d')
            elif 'gün' in date_str:
                days = int(date_str.split()[0])
                return (current_time - timedelta(days=days)).strftime('%Y-%m-%d')
            elif 'hafta' in date_str:
                weeks = int(date_str.split()[0])
                return (current_time - timedelta(weeks=weeks)).strftime('%Y-%m-%d')
            elif 'ay' in date_str:
                months = int(date_str.split()[0])
                return (current_time - timedelta(days=months*30)).strftime('%Y-%m-%d')
            elif 'yıl' in date_str:
                years = int(date_str.split()[0])
                return (current_time - timedelta(days=years*365)).strftime('%Y-%m-%d')
            else:
                return date_str
        except:
            return date_str
            
    def search_videos(self, query, max_videos=50, sort_by=None):
        """Search YouTube videos and extract information."""
        try:
            # Navigate to YouTube
            print(f"'{query}' için arama yapılıyor...")
            self.driver.get(f"https://www.youtube.com/results?search_query={query}")
            self._random_sleep(2, 4)
            
            # Apply sorting if specified
            if sort_by:
                try:
                    print("Sıralama uygulanıyor...")
                    # Wait for filter button and click
                    filter_button = self.wait.until(EC.element_to_be_clickable(
                        (By.XPATH, "//button[@aria-label='Filtreler']")
                    ))
                    filter_button.click()
                    self._random_sleep(1, 2)
                    
                    # Map sort options
                    sort_options = {
                        'upload_date': 'Yükleme tarihi',
                        'view_count': 'Görüntüleme sayısı',
                        'rating': 'Derecelendirme'
                    }
                    
                    # Click sort option
                    sort_option = self.wait.until(EC.element_to_be_clickable(
                        (By.XPATH, f"//div[@title='{sort_options[sort_by]}']")
                    ))
                    sort_option.click()
                    self._random_sleep(2, 3)
                except Exception as e:
                    print(f"Sıralama uygulanırken hata oluştu: {str(e)}")
                    print("Sıralama olmadan devam ediliyor...")
            
            videos_data = []
            processed_videos = set()
            
            print(f"En fazla {max_videos} video toplanacak...")
            
            while len(videos_data) < max_videos:
                try:
                    # Find all video elements
                    video_elements = self.wait.until(EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, "ytd-video-renderer")
                    ))
                    
                    for video in video_elements:
                        if len(videos_data) >= max_videos:
                            break
                            
                        try:
                            # Extract video information
                            title_element = video.find_element(By.CSS_SELECTOR, "#video-title")
                            title = title_element.text.strip()
                            link = title_element.get_attribute("href")
                            
                            # Skip if we've already processed this video
                            if not link or link in processed_videos:
                                continue
                                
                            # Get channel information
                            channel_element = video.find_element(By.CSS_SELECTOR, "#channel-info ytd-channel-name a")
                            channel_name = channel_element.text.strip()
                            channel_link = channel_element.get_attribute("href")
                            
                            # Get metadata (views and upload date)
                            try:
                                metadata = video.find_element(By.CSS_SELECTOR, "#metadata-line").text.split('\n')
                                view_count = self._format_view_count(metadata[0])
                                upload_date = self._format_date(metadata[1])
                            except:
                                view_count = 0
                                upload_date = ""
                            
                            # Get video duration
                            try:
                                duration_element = video.find_element(By.CSS_SELECTOR, "#overlays #text")
                                duration = duration_element.get_attribute("innerText").strip()
                            except:
                                try:
                                    duration_element = video.find_element(By.CSS_SELECTOR, "#overlays [overlay-style='DEFAULT']")
                                    duration = duration_element.get_attribute("innerText").strip()
                                except:
                                    duration = "CANLI" if "CANLI" in title or "LIVE" in title else ""
                            
                            # Get video thumbnail
                            try:
                                thumbnail = video.find_element(By.CSS_SELECTOR, "#thumbnail img").get_attribute("src")
                                if not thumbnail or thumbnail.endswith("html"):
                                    thumbnail = None
                            except:
                                thumbnail = None
                            
                            video_data = {
                                "title": title,
                                "link": link,
                                "channel_name": channel_name,
                                "channel_link": channel_link,
                                "view_count": view_count,
                                "upload_date": upload_date,
                                "duration": duration,
                                "thumbnail": thumbnail
                            }
                            
                            videos_data.append(video_data)
                            processed_videos.add(link)
                            print(f"Video {len(videos_data)}/{max_videos} toplandı: {title}")
                            
                        except Exception as e:
                            print(f"Video verisi çekilirken hata oluştu: {str(e)}")
                            continue
                    
                    # Break if we have enough videos
                    if len(videos_data) >= max_videos:
                        break
                        
                    # Scroll down to load more videos
                    self._human_like_scroll()
                    self._random_sleep(1, 2)
                    
                    # Break if we're not finding any new videos
                    if len(processed_videos) == len(videos_data):
                        break
                        
                except Exception as e:
                    print(f"Video listesi alınırken hata oluştu: {str(e)}")
                    break
            
            if videos_data:
                print(f"\nBaşarıyla {len(videos_data)} video toplandı!")
            else:
                print("\nHiç video toplanamadı!")
                
            return videos_data
            
        except Exception as e:
            print(f"Video arama sırasında hata oluştu: {str(e)}")
            return []
            
    def save_to_json(self, videos_data, filename=None):
        """Save scraped video data to JSON file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"youtube_videos_{timestamp}.json"
            
        try:
            with open(f"data/{filename}", "w", encoding="utf-8") as f:
                json.dump(videos_data, f, ensure_ascii=False, indent=2)
            print(f"Veriler başarıyla kaydedildi: data/{filename}")
        except Exception as e:
            print(f"JSON kaydetme sırasında hata oluştu: {str(e)}")
            
    def close(self):
        """Close the browser."""
        if self.driver:
            self.driver.quit() 