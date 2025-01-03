# Amazon Web Scraper

This project is a professional web scraper for Amazon using Selenium WebDriver. It allows you to scrape product data from Amazon search results including titles, prices, ratings, and more.

## Features

- Search for products using custom queries
- Automatic page scrolling and pagination
- Extracts detailed product information:
  - Title
  - Product URL
  - Price
  - Stock Status
  - Delivery Information
  - Ratings and Reviews
  - Product Condition
  - Color/Options
  - Sponsored Status

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/amazon-scraper.git
cd amazon-scraper
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Create a `.env` file with your configuration:
```bash
cp .env.example .env
```

2. Run the scraper:
```bash
python src/main.py
```

## Project Structure

```
amazon-scraper/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── scraper/
│   │   ├── __init__.py
│   │   ├── amazon_scraper.py
│   │   └── utils.py
│   └── config/
│       ├── __init__.py
│       └── settings.py
├── data/
├── logs/
├── tests/
├── requirements.txt
├── .env.example
└── README.md
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 