import argparse
from youtube_scraper import YouTubeScraper

def main():
    parser = argparse.ArgumentParser(description='YouTube Video Scraper')
    parser.add_argument('--query', type=str, required=True, help='Arama sorgusu')
    parser.add_argument('--max_videos', type=int, default=50, help='Maksimum video sayısı (varsayılan: 50)')
    parser.add_argument('--sort_by', type=str, choices=['upload_date', 'view_count', 'rating'],
                      help='Sıralama kriteri: upload_date, view_count, veya rating')
    
    args = parser.parse_args()
    
    try:
        scraper = YouTubeScraper()
        videos = scraper.search_videos(
            query=args.query,
            max_videos=args.max_videos,
            sort_by=args.sort_by
        )
        
        if videos:
            scraper.save_to_json(videos)
            
    except Exception as e:
        print(f"Hata oluştu: {str(e)}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main() 