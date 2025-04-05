import time
from bs4 import BeautifulSoup
from datetime import datetime

from scrapers.base_scraper import BaseScraper
from utils.text_cleaner import clean_text
from utils.date_parser import parse_date


class DailyNationsScraper(BaseScraper):
    """Scraper for Daily Nation News website."""
    
    def __init__(self):
        """Initialize the Daily Nation scraper."""
        super().__init__('daily_nations')
        self.base_url = 'https://nation.africa'
        self.categories = [
            'news',
            'business',
            'sports',
            'opinion',
            'lifestyle'
        ]
        self.max_articles = 30  # Maximum number of articles to scrape in total
    
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
            
        soup = self.get_soup(url, wait_time=7)  # Longer wait time for content to load
        if not soup:
            return None
            
        try:
            # Extract title - Daily Nation has different article layouts
            title_element = soup.select_one('h1.article-title') or soup.select_one('h1.article-heading') or soup.select_one('h1')
            if not title_element:
                self.logger.warning(f"Could not find title on page: {url}")
                return None
            title = clean_text(title_element.text)
            
            # Extract publication date
            date_element = soup.select_one('.article-date') or soup.select_one('.article-metadata time') or soup.select_one('time')
            publication_date = None
            if date_element:
                date_text = date_element.get('datetime') or clean_text(date_element.text)
                publication_date = parse_date(date_text)
            
            # Extract author
            author_element = soup.select_one('.article-author') or soup.select_one('.author-name') or soup.select_one('.article-byline')
            author = clean_text(author_element.text) if author_element else "Daily Nation"
            
            # IMPROVED CONTENT EXTRACTION - Try multiple selectors to find the article content
            content = ""
            
            # Method 1: Main article content
            content_elements = soup.select('.article-body p') or soup.select('.article-content p')
            if content_elements:
                content = '\n\n'.join([clean_text(p.text) for p in content_elements if p.text.strip()])
                self.logger.info(f"Extracted content using main article selectors, length: {len(content)}")
            
            # Method 2: Story content
            if not content:
                content_elements = soup.select('.story-content p') or soup.select('.article-text p')
                if content_elements:
                    content = '\n\n'.join([clean_text(p.text) for p in content_elements if p.text.strip()])
                    self.logger.info(f"Extracted content using story content selectors, length: {len(content)}")
            
            # Method 3: Try to extract from article element
            if not content:
                article_element = soup.select_one('article')
                if article_element:
                    content_elements = article_element.select('p')
                    content = '\n\n'.join([clean_text(p.text) for p in content_elements if p.text.strip()])
                    self.logger.info(f"Extracted content from article element, length: {len(content)}")
            
            # Method 4: Try to use main content wrapper
            if not content:
                main_content = soup.select_one('main') or soup.select_one('.main-content') or soup.select_one('.content-body')
                if main_content:
                    content_elements = main_content.select('p')
                    content = '\n\n'.join([clean_text(p.text) for p in content_elements if p.text.strip()])
                    self.logger.info(f"Extracted content from main content wrapper, length: {len(content)}")
            
            # Fallback method: Find any substantive paragraphs
            if not content:
                all_paragraphs = soup.select('p')
                # Filter for paragraphs with substantial content (more than 100 characters)
                content_elements = [p for p in all_paragraphs if len(p.text.strip()) > 100]
                if content_elements:
                    content = '\n\n'.join([clean_text(p.text) for p in content_elements])
                    self.logger.info(f"Used fallback paragraph extraction, length: {len(content)}")
            
            # Check if we have any content
            if not content:
                self.logger.warning(f"Could not extract content from {url}")
                # Use title as minimal content to avoid empty content
                content = title
            
            # Extract category
            category_element = soup.select_one('.article-category') or soup.select_one('.article-section') or soup.select_one('.breadcrumbs a')
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
    
    def scrape_category(self, category, articles_needed):
        """
        Scrape articles from a specific category.
        
        Args:
            category (str): Category to scrape
            articles_needed (int): Maximum number of articles to scrape from this category
            
        Returns:
            int: Number of articles scraped
        """
        url = f"{self.base_url}/{category}"
        self.logger.info(f"Scraping category: {category} from {url}")
        
        soup = self.get_soup(url, wait_time=6)
        if not soup:
            return 0
            
        articles_count = 0
        
        try:
            # Find all article links on the page
            article_links = []
            
            # Daily Nation specific article selectors
            # 1. Main article cards
            article_elements = soup.select('article a') or soup.select('.article-card a') or soup.select('.card-link')
            for article in article_elements:
                link = article.get('href')
                if link:
                    article_links.append(link)
            
            # 2. Headline teasers
            headline_elements = soup.select('.headline-teasers_item a') or soup.select('.headline a')
            for headline in headline_elements:
                link = headline.get('href')
                if link:
                    article_links.append(link)
            
            # 3. Featured articles
            featured_elements = soup.select('.featured-article a') or soup.select('.feature a')
            for featured in featured_elements:
                link = featured.get('href')
                if link:
                    article_links.append(link)
                    
            # 4. Any other article containers
            other_elements = soup.select('.teaser a') or soup.select('.story-teaser a') or soup.select('.news-item a')
            for element in other_elements:
                link = element.get('href')
                if link:
                    article_links.append(link)
            
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
            
            # Scrape each article, but only up to the articles_needed limit
            for link in absolute_links[:articles_needed]:
                article_data = self.scrape_article_page(link)
                if article_data:
                    if self.save_article(article_data):
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
    
    def scrape(self):
        """
        Implement the scraping process for Daily Nation News.
        
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
            
            self.logger.info(f"Total articles scraped: {total_articles} (max limit: {self.max_articles})")
            return total_articles > 0
            
        except Exception as e:
            self.logger.error(f"Error in scrape process: {e}")
            return False
