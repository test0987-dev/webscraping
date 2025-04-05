import time
import csv
from bs4 import BeautifulSoup
from datetime import datetime
from uuid import uuid4

from scrapers.base_scraper import BaseScraper
from utils.text_cleaner import clean_text
from utils.date_parser import parse_date


class TukoScraper(BaseScraper):
    """Scraper for Tuko News website."""

    def __init__(self):
        """Initialize the Tuko scraper."""
        super().__init__('tuko')
        self.base_url = 'https://www.tuko.co.ke'
        self.categories = [
            'news',
            'entertainment',
            'politics',
            'lifestyle',
            'sports'
        ]
        self.articles = []
        self.max_articles = 30  # Maximum number of articles to scrape in total

    def scrape_article_page(self, url):
        if self.article_exists(url):
            self.logger.info(f"Article already exists: {url}")
            return None

        soup = self.get_soup(url, wait_time=6)
        if not soup:
            return None

        try:
            title_element = soup.select_one('h1.article-title') or soup.select_one('.c-article__headline') or soup.select_one('h1')
            if not title_element:
                self.logger.warning(f"Could not find title on page: {url}")
                return None
            title = clean_text(title_element.text)

            date_element = soup.select_one('.article-date') or soup.select_one('.c-article__date') or soup.select_one('time')
            publication_date = None
            if date_element:
                date_text = date_element.get('datetime') or clean_text(date_element.text)
                publication_date = parse_date(date_text)

            author_element = soup.select_one('.article-author') or soup.select_one('.c-article__author') or soup.select_one('.author-name')
            author = clean_text(author_element.text) if author_element else "Tuko"

            content = ""
            
            content_elements = soup.select('.article-body p') or soup.select('.c-article__content p')
            if content_elements:
                content = '\n\n'.join([clean_text(p.text) for p in content_elements if p.text.strip()])
                self.logger.info(f"Extracted content using main article selectors, length: {len(content)}")
            
            if not content:
                content_elements = soup.select('.story-content p') or soup.select('.entry-content p')
                if content_elements:
                    content = '\n\n'.join([clean_text(p.text) for p in content_elements if p.text.strip()])
                    self.logger.info(f"Extracted content using story content selectors, length: {len(content)}")
            
            if not content:
                article_element = soup.select_one('article')
                if article_element:
                    content_elements = article_element.select('p')
                    content = '\n\n'.join([clean_text(p.text) for p in content_elements if p.text.strip()])
                    self.logger.info(f"Extracted content from article element, length: {len(content)}")
            
            if not content:
                main_content = soup.select_one('main') or soup.select_one('.main-content') or soup.select_one('.content-wrapper')
                if main_content:
                    content_elements = main_content.select('p')
                    content = '\n\n'.join([clean_text(p.text) for p in content_elements if p.text.strip()])
                    self.logger.info(f"Extracted content from main content wrapper, length: {len(content)}")
            
            if not content:
                all_paragraphs = soup.select('p')
                content_elements = [p for p in all_paragraphs if len(p.text.strip()) > 100]
                if content_elements:
                    content = '\n\n'.join([clean_text(p.text) for p in content_elements])
                    self.logger.info(f"Used fallback paragraph extraction, length: {len(content)}")
            
            if not content:
                self.logger.warning(f"Could not extract content from {url}")
                content = title
            
            category_element = soup.select_one('.article-category') or soup.select_one('.c-article__category') or soup.select_one('.category')
            category = clean_text(category_element.text) if category_element else "News"

            article_data = {
                'id': str(uuid4()),
                'url': url,
                'title': title,
                'publication_date': publication_date,
                'author': author,
                'content': content,
                'category': category,
                'created_at': publication_date or datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            }

            return article_data

        except Exception as e:
            self.logger.error(f"Error scraping article {url}: {e}")
            return None

    def scrape_category(self, category, articles_needed):
        url = f"{self.base_url}/{category}"
        self.logger.info(f"Scraping category: {category} from {url}")

        soup = self.get_soup(url, wait_time=6)
        if not soup:
            return 0

        articles_count = 0
        try:
            article_links = []
            article_elements = soup.select('.article-card a') or soup.select('.c-article-card a')
            for card in article_elements:
                link = card.get('href')
                if link:
                    article_links.append(link)

            featured_elements = soup.select('.featured-article a') or soup.select('.c-featured a')
            for featured in featured_elements:
                link = featured.get('href')
                if link:
                    article_links.append(link)

            headline_elements = soup.select('.headline a') or soup.select('.c-headline a')
            for headline in headline_elements:
                link = headline.get('href')
                if link:
                    article_links.append(link)

            story_elements = soup.select('.story-card a') or soup.select('.c-story-card a')
            for story in story_elements:
                link = story.get('href')
                if link:
                    article_links.append(link)

            absolute_links = []
            for link in article_links:
                if not link.startswith('http'):
                    link = self.base_url + link if link.startswith('/') else self.base_url + '/' + link
                absolute_links.append(link)

            absolute_links = list(set(absolute_links))

            self.logger.info(f"Found {len(absolute_links)} articles in {category}")

            # Only scrape up to the number of articles needed for this category
            for link in absolute_links[:articles_needed]:
                article_data = self.scrape_article_page(link)
                if article_data:
                    if self.save_article(article_data):
                        self.articles.append(article_data)
                        articles_count += 1
                        
                        # Stop if we've reached the maximum number of articles needed
                        if articles_count >= articles_needed:
                            self.logger.info(f"Reached article limit for category {category}")
                            break
                            
                    # Add a small delay to avoid overloading the server
                    time.sleep(2)

            return articles_count

        except Exception as e:
            self.logger.error(f"Error scraping category {category}: {e}")
            return articles_count

    def save_articles_to_csv(self, filename="tuko_articles.csv"):
        """Save all scraped articles to CSV."""
        fieldnames = ['id', 'url', 'title', 'publication_date', 'author',
                      'content', 'category', 'created_at', 'last_updated']

        try:
            with open(filename, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for article in self.articles:
                    writer.writerow(article)
            self.logger.info(f"✅ Saved {len(self.articles)} articles to {filename}")
        except Exception as e:
            self.logger.error(f"Failed to save CSV: {e}")

    def scrape(self):
        """
        Implement the scraping process for Tuko News.
        
        Returns:
            bool: True if scraping was successful, False otherwise
        """
        try:
            total_articles = 0
            remaining_articles = self.max_articles
            
            # Scrape each category, but only up to the maximum total limit
            for category in self.categories:
                if remaining_articles <= 0:
                    self.logger.info(f"Reached maximum article limit of {self.max_articles}")
                    break
                    
                # Calculate how many articles to get from this category
                # Distribute remaining articles evenly among remaining categories
                remaining_categories = len(self.categories) - self.categories.index(category)
                articles_per_category = max(1, remaining_articles // remaining_categories)
                
                self.logger.info(f"Aiming to scrape up to {articles_per_category} articles from {category}")
                articles_count = self.scrape_category(category, articles_per_category)
                
                total_articles += articles_count
                remaining_articles -= articles_count
                
                self.logger.info(f"Scraped {articles_count} articles from {category}, {total_articles} total so far")
                
                # Update metadata after each category
                self.update_metadata(articles_count, 0)
                
                # Add a small delay between categories
                time.sleep(5)
            
            self.save_articles_to_csv()
            self.logger.info(f"Total articles scraped: {total_articles} (max limit: {self.max_articles})")
            return total_articles > 0
        except Exception as e:
            self.logger.error(f"Error in scrape process: {e}")
            return False
