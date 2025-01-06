import os
import sys
from scraper.google_shopping_scraper import GoogleShoppingScraper

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
        print("Google Shopping Ürün Toplayıcı".center(80))
        print("=" * 80 + "\n")
        
        # Parametreleri ayarla
        query = "iphone 15"    # Query'yi iPhone 15 olarak değiştirdik
        max_products = 30    # 30 ürün toplayacak
        
        print(f"Arama Terimi: {query}")
        print(f"Maksimum Ürün Sayısı: {max_products}")
        print("-" * 80 + "\n")
        
        # Scraper'ı başlat
        scraper = GoogleShoppingScraper()
        
        # Ürünleri topla
        products = scraper.scrape_products(query=query, max_products=max_products)
        
        if products:
            # Sonuçları kaydet
            scraper.save_results(products)
            print(f"\nToplanan ürünler başarıyla kaydedildi!")
            print(f"Toplam {len(products)} ürün bulundu.")
        else:
            print("\nUYARI: Hiç ürün bulunamadı!")
            
    except Exception as e:
        print(f"\nHata oluştu: {str(e)}")
        
    finally:
        if scraper:
            print("\nTarayıcı kapatılıyor...")
            scraper.close()
            print("İşlem tamamlandı.")

if __name__ == "__main__":
    main() 