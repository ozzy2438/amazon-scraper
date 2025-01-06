from scraper.amazon_scraper import AmazonScraper
from config.settings import Settings
import os

def main():
    try:
        # Create data directory if it doesn't exist
        os.makedirs("data", exist_ok=True)
        
        # Initialize settings and scraper
        settings = Settings.from_env()
        scraper = AmazonScraper(settings)
        
        # Search for MacBook M3 Pro
        print("MacBook M3 Pro için arama yapılıyor...")
        scraper.search_products("MacBook M3 Pro")
        
        # Scrape products with maximum 200 pages
        print("\nÜrünler toplanıyor...")
        products = scraper.scrape_products(max_pages=200)
        
        if products:
            # Save results with timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/amazon_products_{timestamp}"
            scraper.save_results(filename)
            print(f"\nToplam {len(products)} ürün başarıyla kaydedildi!")
        else:
            print("\nHiç ürün bulunamadı!")
            
    except Exception as e:
        print(f"Hata oluştu: {str(e)}")
    finally:
        if scraper:
            scraper.close()

if __name__ == "__main__":
    main() 