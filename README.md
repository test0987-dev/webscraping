# Kenya News Scraper

A robust data collection system for scraping news articles from major Kenyan news websites.

## Overview

This project provides automated scrapers for several popular Kenyan news sources:

- Citizen Digital (`citizen.py`)
- Daily Nation (`daily_nations.py`)
- The Standard Media (`standardmedia.py`)
- The Star (`star.py`)
- Tuko (`tuko_new.py`)

Each scraper follows a standardized approach to extract article content, metadata, and categorize news items for analysis or archiving.

## Project Structure

```
Kenya_news/
│
├── config/                  # Configuration settings
│   ├── database.py          # Database connection settings
│   └── settings.py          # General application settings
│
├── scrapers/                # News website scrapers
│   ├── base_scraper.py      # Base class with common functionality
│   ├── citizen.py           # Citizen Digital scraper
│   ├── daily_nations.py     # Daily Nation scraper
│   ├── standardmedia.py     # Standard Media scraper
│   ├── star.py              # The Star scraper
│   └── tuko_new.py          # Tuko News scraper
│
├── utils/                   # Utility functions
│   ├── date_parser.py       # Date string parsing functions
│   ├── logger.py            # Logging configuration
│   └── text_cleaner.py      # Text cleaning utilities
│
├── logs/                    # Log files directory
├── main.py                  # Entry point for running scrapers
└── setup.py                 # Project setup script
```

## Installation

### Prerequisites

- Python 3.8 or higher
- Firefox browser (for WebDriver)
- MySQL database (optional, for storage)

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/Kenya_news.git
   cd Kenya_news
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Configure database settings in `config/settings.py`

## Usage

### Running All Scrapers

To run all news scrapers:

```
python main.py
```

### Running Specific Scrapers

To run only specific scrapers:

```
python main.py --sources citizen star
```

Available sources: `citizen`, `daily_nations`, `standardmedia`, `star`, `tuko`

## Scraper Design

Each scraper extends the `BaseScraper` class, which provides common functionality:

- WebDriver initialization
- Database connection management
- Article existence checking
- Content saving
- Logging

The scrapers are designed to:
- Scrape up to 30 articles total by default (configurable)
- Distribute articles evenly across categories
- Extract article details including title, author, date, content, and category
- Use fallback mechanisms for content extraction when primary methods fail
- Handle relative URLs and website-specific page structures

## Features

- **Robust Content Extraction**: Multiple extraction methods with fallbacks
- **Smart Article Limits**: Configurable article limits to prevent overloading
- **Database Integration**: Stores articles in MySQL for easy querying
- **Duplicate Prevention**: Avoids re-scraping existing articles
- **Comprehensive Logging**: Detailed logs for debugging and monitoring
- **Error Handling**: Graceful error handling throughout the scraping process

## Customization

### Adjusting Article Limits

Each scraper has a `max_articles` property in the `__init__` method that can be modified to change the total article limit.

### Adding New Sources

To add a new news source:

1. Create a new scraper file extending `BaseScraper`
2. Implement the required methods: `scrape_article_page`, `scrape_category`, and `scrape`
3. Add the scraper to the `scrapers` dictionary in `main.py`

## Troubleshooting

- **WebDriver Issues**: Make sure Firefox is installed and geckodriver is in PATH
- **Database Errors**: Check connection settings in `config/settings.py`
- **Empty Content**: Some websites may change their structure; update selectors as needed
- **Rate Limiting**: Increase `wait_time` and `time.sleep()` intervals if getting blocked

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- BeautifulSoup4 for HTML parsing
- Selenium for browser automation
- Various Kenyan news sources for providing public content 