import os
import sys
from scraper.bbc_scraper import BBCScraper

def check_chromedriver():
    """Check if ChromeDriver is installed."""
    chromedriver_path = "/opt/homebrew/bin/chromedriver"
    if not os.path.exists(chromedriver_path):
        print("\nERROR: ChromeDriver not found!")
        print("Please install ChromeDriver by running the following command:")
        print("\nbrew install chromedriver")
        sys.exit(1)

def main():
    scraper = None
    try:
        # Check ChromeDriver installation
        check_chromedriver()
        
        print("\n" + "="*80)
        print("BBC News Article Collector".center(80))
        print("="*80 + "\n")
        
        # Initialize scraper
        scraper = BBCScraper()
        
        # Search parameters
        query = "ChatGPT"
        max_articles = 20
        
        print(f"Search Term: {query}")
        print(f"Maximum Number of Articles: {max_articles}")
        print("-"*80 + "\n")
        
        # Start scraping
        articles = scraper.scrape_news(query=query, max_articles=max_articles)
        
        if articles:
            print("\nCollected articles saved successfully!")
            print(f"Total {len(articles)} articles found.")
        else:
            print("\nWARNING: No articles found!")
            print("Suggestions:")
            print("1. Try changing the search term")
            print("2. Try again at a different time")
            print("3. Check your internet connection")
            
    except KeyboardInterrupt:
        print("\n\nStopped by user.")
    except Exception as e:
        print(f"\nCritical error occurred: {str(e)}")
        print("\nError details:")
        import traceback
        traceback.print_exc()
    finally:
        if scraper:
            print("\nClosing browser...")
            scraper.close()
            print("Process completed.")

if __name__ == "__main__":
    main()
