import time
import json
from bs4 import BeautifulSoup
from datetime import datetime

from scrapers.base_scraper import BaseScraper
from utils.text_cleaner import clean_text
from utils.date_parser import parse_date


class StarScraper(BaseScraper):
    """Scraper for The Star Kenya news website."""
    
    def __init__(self):
        """Initialize The Star scraper."""
        super().__init__('star')
        self.base_url = 'https://www.the-star.co.ke'
        self.categories = [
            'news',
            'business',
            'sports',
            'opinion',
            'entertainment'
        ]
        self.max_articles = 30  # Maximum number of articles to scrape in total
    
    def scrape_article_page(self, url):
        if self.article_exists(url):
            self.logger.info(f"Article already exists: {url}")
            return None
            
        soup = self.get_soup(url, wait_time=5)
        if not soup:
            return None
            
        try:
            # The Star often uses structured JSON-LD data which is much more reliable
            ld_json = soup.find("script", type="application/ld+json")
            
            # Initialize article data with default values
            title = ""
            publication_date = None
            author = "The Star"
            content = ""
            category = "News"
            
            # Extract data from JSON-LD if available
            if ld_json:
                try:
                    json_data = json.loads(ld_json.string)
                    if isinstance(json_data, list):
                        json_data = json_data[0]
                    
                    # Extract title
                    if json_data.get("headline"):
                        title = clean_text(json_data.get("headline"))
                        
                    # Extract publication date
                    if json_data.get("datePublished"):
                        publication_date = parse_date(json_data.get("datePublished"))
                        
                    # Extract author
                    if isinstance(json_data.get("author"), dict) and json_data.get("author", {}).get("name"):
                        author = clean_text(json_data.get("author", {}).get("name"))
                    elif isinstance(json_data.get("author"), str):
                        author = clean_text(json_data.get("author"))
                        
                    # Extract content
                    if json_data.get("articleBody"):
                        content = clean_text(json_data.get("articleBody"))
                        
                    # Extract category
                    if json_data.get("articleSection"):
                        category = clean_text(json_data.get("articleSection"))
                        
                    self.logger.info(f"Successfully extracted structured data from JSON-LD for {url}")
                        
                except Exception as e:
                    self.logger.error(f"Failed to parse JSON-LD for {url}: {e}")
            
            # If we couldn't get data from JSON-LD or it's missing fields, try HTML parsing
            
            # Extract title if not found in JSON-LD
            if not title:
                title_element = soup.select_one('h1.article-title') or soup.select_one('h1.news-head') or soup.select_one('h1')
                if title_element:
                    title = clean_text(title_element.text)
                else:
                    self.logger.warning(f"Could not find title on page: {url}")
                    return None
            
            # Extract publication date if not found in JSON-LD
            if not publication_date:
                date_element = soup.select_one('.article-metadata time') or soup.select_one('.publish-date') or soup.select_one('time')
                if date_element:
                    date_text = date_element.get('datetime') or clean_text(date_element.text)
                    publication_date = parse_date(date_text)
            
            # Extract author if not found in JSON-LD
            if author == "The Star":
                author_element = soup.select_one('.article-author') or soup.select_one('.author-name')
                if author_element:
                    author = clean_text(author_element.text)
            
            # Extract content if not found in JSON-LD
            if not content:
                # Try multiple selectors for content
                content_elements = []
                
                # Method 1: Article body paragraphs
                content_elements = soup.select('.article-body p') or soup.select('.news-content p')
                
                # Method 2: Try generic article paragraphs
                if not content_elements:
                    content_elements = soup.select('article p')
                
                # Method 3: Any main content paragraphs
                if not content_elements:
                    main_content = soup.select_one('main') or soup.select_one('.main-content')
                    if main_content:
                        content_elements = main_content.select('p')
                
                # Method 4: Any substantial paragraphs
                if not content_elements:
                    all_paragraphs = soup.select('p')
                    content_elements = [p for p in all_paragraphs if len(p.text.strip()) > 100]
                
                if content_elements:
                    content = '\n\n'.join([clean_text(p.text) for p in content_elements if p.text.strip()])
                else:
                    self.logger.warning(f"Could not extract content from {url}")
                    return None
            
            # Extract category if not found in JSON-LD
            if category == "News":
                category_element = soup.select_one('.article-category') or soup.select_one('.news-category')
                if category_element:
                    category = clean_text(category_element.text)
            
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
        url = f"{self.base_url}/{category}"
        self.logger.info(f"Scraping category: {category} from {url}")
        
        soup = self.get_soup(url)
        if not soup:
            return 0
            
        articles_count = 0
        
        try:
            # Find all article links on the page
            article_links = []
            
            # The Star specific article selectors
            # 1. Main article containers
            article_containers = soup.select("article.group") + soup.select("div.flex.group")
            for container in article_containers:
                link_elem = container.select_one("a")
                if link_elem and link_elem.get("href"):
                    article_links.append(link_elem.get("href"))
            
            # 2. Look for headline articles
            headline_links = soup.select(".headline a") + soup.select(".headline-article a")
            for link in headline_links:
                if link.get("href"):
                    article_links.append(link.get("href"))
            
            # 3. Look for feature articles
            feature_links = soup.select(".feature a") + soup.select(".featured-article a")
            for link in feature_links:
                if link.get("href"):
                    article_links.append(link.get("href"))
                    
            # 4. Additional article cards
            card_links = soup.select(".card a") + soup.select(".article-card a") + soup.select(".newscard a")
            for link in card_links:
                if link.get("href"):
                    article_links.append(link.get("href"))
            
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
        Implement the scraping process for The Star news.
        
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
