import asyncio
from crawl4ai import AsyncWebCrawler
import json
import os
from datetime import datetime

async def save_results(articles, filename=None):
    """Save scraped articles to JSON file."""
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
        print(f"Veriler JSON olarak kaydedildi: {json_filename}")
            
    except Exception as e:
        print(f"Dosya kaydetme sırasında hata oluştu: {str(e)}")

async def main():
    # Create an instance of AsyncWebCrawler
    async with AsyncWebCrawler(verbose=True) as crawler:
        # BBC News arama URL'si
        query = "ChatGPT"
        url = f"https://www.bbc.co.uk/search?q={query}"
        
        print(f"BBC News'de '{query}' için arama yapılıyor...")
        
        # Run the crawler on the search URL
        result = await crawler.arun(url=url)
        
        if result and result.markdown:
            # Extract article data
            articles = []
            
            # Process the markdown content
            lines = result.markdown.split('\n')
            current_article = {}
            
            for line in lines:
                line = line.strip()
                if not line:
                    if current_article:
                        articles.append(current_article.copy())
                        current_article = {}
                    continue
                    
                if line.startswith('# '):  # Title
                    current_article['title'] = line[2:]
                elif line.startswith('> '):  # Description
                    current_article['description'] = line[2:]
                elif line.startswith('[') and '](' in line:  # Link
                    start = line.find('](') + 2
                    end = line.find(')', start)
                    if start > 1 and end > start:
                        current_article['link'] = line[start:end]
                        
            # Add last article if exists
            if current_article:
                articles.append(current_article)
                
            # Save results
            if articles:
                print(f"\nToplam {len(articles)} makale bulundu.")
                print("\nÖrnek makaleler:")
                for i, article in enumerate(articles[:3], 1):
                    print(f"\n{i}. {article.get('title', 'Başlık yok')}")
                    print(f"Link: {article.get('link', 'Link yok')}")
                    print(f"Açıklama: {article.get('description', 'Açıklama yok')}")
                    
                await save_results(articles)
            else:
                print("\nHiç makale bulunamadı!")
        else:
            print("Sayfa içeriği alınamadı!")

# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())