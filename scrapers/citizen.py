import os
import sys
import time
from bs4 import BeautifulSoup
from datetime import datetime

# Add parent directory to sys.path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from scrapers.base_scraper import BaseScraper
from utils.text_cleaner import clean_text
from utils.date_parser import parse_date


class CitizenScraper(BaseScraper):
    """Scraper for Citizen TV News website."""
    
    def __init__(self):
        """Initialize the Citizen scraper."""
        super().__init__('citizen')
        self.base_url = 'https://www.citizen.digital'
        self.categories = [
            'news',
            'business',
            'sports',
            'lifestyle',
            'entertainment'
        ]
    
    def scrape_article_page(self, url):
        """
        Scrape a single article page.
        
        Args:
            url (str): URL of the article to scrape
            
        Returns:
            dict: Article data or None if failed
        """
        if self.article_exists(url):
            self.logger.info(f"Article already exists: {url}")
            return None
            
        soup = self.get_soup(url, wait_time=6)  # Longer wait time to ensure page loads
        if not soup:
            return None
            
        try:
            # Extract article title - Citizen has desktop and mobile title variations
            title_element = soup.select_one('h1.title-on-desktop a') or soup.select_one('h1.title-on-mobile a')
            if not title_element:
                title_element = soup.select_one('h1.article-title') or soup.select_one('h1')
            
            if not title_element:
                self.logger.warning(f"Could not find title on page: {url}")
                return None
                
            title = clean_text(title_element.text)
            
            # Extract publication date
            date_element = soup.select_one('span.timepublished') or soup.select_one('.article-date')
            publication_date = None
            if date_element:
                date_text = clean_text(date_element.text)
                publication_date = parse_date(date_text)
            
            # Extract author - Citizen often uses "Citizen Digital" as default author
            author_element = soup.select_one('.article-author')
            author = clean_text(author_element.text) if author_element else "Citizen Digital"
            
            # Extract content - look for article body paragraphs
            content_elements = soup.select('.article-body p') or soup.select('.topstory-excerpt p')
            if not content_elements:
                # Try alternative content containers
                content_elements = soup.select('div.topstory-excerpt p')
            
            content = '\n\n'.join([clean_text(p.text) for p in content_elements if p.text.strip()])
            
            # Extract category
            category_element = soup.select_one('.next-topstory-tags span:first-child') or soup.select_one('.article-category')
            category = clean_text(category_element.text) if category_element else "News"
            
            # Create article data
            article_data = {
                'url': url,
                'title': title,
                'publication_date': publication_date,
                'author': author,
                'content': content,
                'category': category
            }
            
            return article_data
            
        except Exception as e:
            self.logger.error(f"Error scraping article {url}: {e}")
            return None
    
    def scrape_category(self, category):
        """
        Scrape articles from a specific category.
        
        Args:
            category (str): Category to scrape
            
        Returns:
            int: Number of articles scraped
        """
        url = f"{self.base_url}/{category}"
        self.logger.info(f"Scraping category: {category} from {url}")
        
        soup = self.get_soup(url, wait_time=8)  # Longer wait time for page to load
        if not soup:
            return 0
            
        articles_count = 0
        
        try:
            # Find all article links on the page
            article_links = []
            
            # Citizen specific article selectors:
            # 1. Main pinned story 
            main_story_element = soup.select_one('.main-pinned-story a')
            if main_story_element and main_story_element.get('href'):
                article_links.append(main_story_element.get('href'))
            
            # 2. Other pinned stories
            other_stories = soup.select('.other-pinned-stories h3 a')
            for story in other_stories:
                if story.get('href'):
                    article_links.append(story.get('href'))
            
            # 3. Featured stories
            featured_stories = soup.select('.topstory.featuredstory h1 a')
            for story in featured_stories:
                if story.get('href'):
                    article_links.append(story.get('href'))
            
            # 4. Additional story cards
            story_cards = soup.select('.article-card a') or soup.select('.story-card a')
            for card in story_cards:
                if card.get('href'):
                    article_links.append(card.get('href'))
            
            # Make sure all links are absolute URLs
            absolute_links = []
            for link in article_links:
                if not link.startswith('http'):
                    link = self.base_url + link if link.startswith('/') else self.base_url + '/' + link
                absolute_links.append(link)
            
            # Remove duplicate links
            absolute_links = list(set(absolute_links))
            
            # Log the number of articles found
            self.logger.info(f"Found {len(absolute_links)} articles in {category}")
            
            # Scrape each article
            for link in absolute_links[:15]:  # Limit to 15 articles per category for testing
                article_data = self.scrape_article_page(link)
                if article_data:
                    if self.save_article(article_data):
                        articles_count += 1
                    # Add a small delay to avoid overloading the server
                    time.sleep(2)
            
            return articles_count
            
        except Exception as e:
            self.logger.error(f"Error scraping category {category}: {e}")
            return articles_count
    
    def scrape(self):
        """
        Implement the scraping process for Citizen TV News.
        
        Returns:
            bool: True if scraping was successful, False otherwise
        """
        try:
            total_articles = 0
            
            # Scrape each category
            for category in self.categories:
                articles_count = self.scrape_category(category)
                total_articles += articles_count
                self.logger.info(f"Scraped {articles_count} articles from {category}")
                
                # Update metadata after each category
                self.update_metadata(articles_count, 0)
                
                # Add a small delay between categories
                time.sleep(5)
            
            self.logger.info(f"Total articles scraped: {total_articles}")
            return total_articles > 0
            
        except Exception as e:
            self.logger.error(f"Error in scrape process: {e}")
            return False