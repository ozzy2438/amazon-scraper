import os
import sys
from scraper.bbc_scraper import BBCScraper

def check_chromedriver():
    """Check if ChromeDriver is installed."""
    chromedriver_path = "/opt/homebrew/bin/chromedriver"
    if not os.path.exists(chromedriver_path):
        print("\nHATA: ChromeDriver bulunamadı!")
        print("Lütfen ChromeDriver'ı yüklemek için şu komutu çalıştırın:")
        print("\nbrew install chromedriver")
        sys.exit(1)

def main():
    scraper = None
    try:
        # ChromeDriver kontrolü
        check_chromedriver()
        
        print("\n" + "=" * 80)
        print("BBC Haber Makalesi Toplayıcı".center(80))
        print("=" * 80 + "\n")
        
        # Parametreleri ayarla
        query = "data science"  # Query'yi data science olarak değiştirdik
        max_articles = 100      # 100 makale için ayarladık
        
        print(f"Arama Terimi: {query}")
        print(f"Maksimum Makale Sayısı: {max_articles}")
        print("-" * 80 + "\n")
        
        # Scraper'ı başlat
        scraper = BBCScraper()
        
        # Haberleri topla
        articles = scraper.scrape_news(query=query, max_articles=max_articles)
        
        if articles:
            # Sonuçları kaydet
            scraper.save_results(articles)
            print(f"\nToplanan makaleler başarıyla kaydedildi!")
            print(f"Toplam {len(articles)} makale bulundu.")
        else:
            print("\nUYARI: Hiç makale bulunamadı!")
            
    except Exception as e:
        print(f"\nHata oluştu: {str(e)}")
        
    finally:
        if scraper:
            print("\nTarayıcı kapatılıyor...")
            scraper.driver.quit()
            print("İşlem tamamlandı.")

if __name__ == "__main__":
    main()
