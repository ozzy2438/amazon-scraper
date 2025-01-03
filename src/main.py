"""Main entry point for the Amazon scraper application."""

import argparse
import os
from datetime import datetime

from rich.console import Console
from rich.prompt import Prompt

from config.settings import Settings
from scraper.amazon_scraper import AmazonScraper
from scraper.utils import setup_logging, ensure_dir

console = Console()

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Amazon Product Scraper')
    parser.add_argument(
        '--query',
        type=str,
        help='Search query for products'
    )
    parser.add_argument(
        '--pages',
        type=int,
        help='Number of pages to scrape (default: from settings)'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output file path (default: auto-generated)'
    )
    return parser.parse_args()

def main():
    """Main function to run the scraper."""
    # Load settings
    settings = Settings.from_env()
    
    # Set up logging
    setup_logging(settings.LOG_FILE, settings.LOG_LEVEL)
    
    # Parse command line arguments
    args = parse_args()
    
    # Get search query
    query = args.query or Prompt.ask("Enter search query")
    
    # Create output directory
    ensure_dir(settings.OUTPUT_DIR)
    
    # Generate output filename if not provided
    if not args.output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"amazon_products_{timestamp}.{settings.OUTPUT_FORMAT}"
        output_path = os.path.join(settings.OUTPUT_DIR, filename)
    else:
        output_path = args.output
    
    try:
        # Initialize and run scraper
        with console.status("[bold green]Initializing scraper..."):
            scraper = AmazonScraper(settings)
        
        console.print(f"[yellow]Searching for: {query}")
        scraper.search_products(query)
        
        console.print("[yellow]Scraping products...")
        products = scraper.scrape_products(args.pages)
        
        # Save results
        scraper.save_results(output_path)
        console.print(f"[green]Successfully saved {len(products)} products to {output_path}")
        
    except KeyboardInterrupt:
        console.print("\n[red]Scraping interrupted by user")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}")
    finally:
        if 'scraper' in locals():
            scraper.close()

if __name__ == "__main__":
    main() 