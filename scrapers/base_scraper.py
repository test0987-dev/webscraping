import os
import sys
import time
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from bs4 import BeautifulSoup

# Add parent directory to sys.path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from config.database import get_connection
from utils.text_cleaner import clean_text
from utils.date_parser import parse_date


class BaseScraper:
    """Base class for news scrapers with common functionality."""
    
    def __init__(self, source_name):
        self.source_name = source_name
        self.table_name = f"{source_name}_articles"
        self.driver = None
        self.connection = None
        self.logger = self._setup_logger()
        
    def _setup_logger(self):
        """Set up a logger for this scraper instance."""
        logger = logging.getLogger(f"{self.source_name}_scraper")
        logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # File handler
        file_handler = logging.FileHandler(f"logs/{self.source_name}_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter and add to handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def initialize_webdriver(self):
        """Initialize and configure the Selenium WebDriver."""
        try:
            # Setup Firefox options
            options = FirefoxOptions()
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.set_preference("general.useragent.override", 
                                "Mozilla/5.0 (X11; Linux x86_64; rv:134.0) Gecko/20100101 Firefox/134.0")
            options.set_preference("intl.accept_languages", "en-US,en;q=0.5")
            options.set_preference("network.http.accept-encoding", "gzip, deflate, br, zstd")
            options.set_preference("privacy.donottrackheader.enabled", True)
            
            # Initialize WebDriver
            service = FirefoxService(GeckoDriverManager().install())
            self.driver = webdriver.Firefox(service=service, options=options)
            self.logger.info(f"WebDriver initialized for {self.source_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize WebDriver: {e}")
            return False
    
    def close_webdriver(self):
        """Safely close the WebDriver."""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("WebDriver closed")
            except Exception as e:
                self.logger.error(f"Error closing WebDriver: {e}")
    
    def initialize_db(self):
        """Initialize database connection."""
        try:
            self.connection = get_connection()
            if self.connection and self.connection.is_connected():
                self.logger.info("Database connection established")
                return True
            else:
                self.logger.error("Failed to connect to database")
                return False
        except Exception as e:
            self.logger.error(f"Error connecting to database: {e}")
            return False
    
    def close_db(self):
        """Safely close the database connection."""
        if self.connection and self.connection.is_connected():
            try:
                self.connection.close()
                self.logger.info("Database conn closed")
            except Exception as e:
                self.logger.error(f"Error closing database connection: {e}")
    
    def get_soup(self, url, wait_time=5):
        if not self.driver:
            self.logger.error("WebDriver not initialized")
            return None
            
        try:
            self.logger.info(f"Loading URL: {url}")
            self.driver.get(url)
            time.sleep(wait_time)  # Wait for page to load
            
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            return soup
        except Exception as e:
            self.logger.error(f"Error loading URL {url}: {e}")
            return None
    
    def article_exists(self, url):
        if not self.connection or not self.connection.is_connected():
            self.logger.error("Database conn not initialized")
            return False
            
        try:
            cursor = self.connection.cursor()
            query = f"SELECT COUNT(*) FROM {self.table_name} WHERE url = %s"
            cursor.execute(query, (url,))
            count = cursor.fetchone()[0]
            cursor.close()
            return count > 0
        except Exception as e:
            self.logger.error(f"Error checking if article exists: {e}")
            return False
    
    def save_article(self, article_data):
        if not self.connection or not self.connection.is_connected():
            self.logger.error("Database conn not initialized")
            return False
            
        # Check if the article already exists
        if self.article_exists(article_data['url']):
            self.logger.info(f"Article already exists: {article_data['url']}")
            return self.update_article(article_data)
            
        try:
            cursor = self.connection.cursor()
            
            # Insert new article
            query = f"""
            INSERT INTO {self.table_name} 
            (url, title, publication_date, author, content, category) 
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            values = (
                article_data['url'],
                article_data['title'],
                article_data['publication_date'],
                article_data['author'],
                article_data['content'],
                article_data['category']
            )
            
            cursor.execute(query, values)
            self.connection.commit()
            cursor.close()
            
            self.logger.info(f"Article saved: {article_data['title']}")
            self.update_metadata(1, 0)
            return True
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"Error saving article: {e}")
            return False
    
    def update_article(self, article_data):
        if not self.connection or not self.connection.is_connected():
            self.logger.error("Database conn initialized")
            return False
            
        try:
            cursor = self.connection.cursor()
            
            # Update existing article
            query = f"""
            UPDATE {self.table_name} 
            SET title = %s, publication_date = %s, author = %s, content = %s, category = %s
            WHERE url = %s
            """
            
            values = (
                article_data['title'],
                article_data['publication_date'],
                article_data['author'],
                article_data['content'],
                article_data['category'],
                article_data['url']
            )
            
            cursor.execute(query, values)
            self.connection.commit()
            cursor.close()
            
            self.logger.info(f"Article updated: {article_data['title']}")
            self.update_metadata(0, 1)
            return True
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"Error updating article: {e}")
            return False
    
    def update_metadata(self, articles_added=0, articles_updated=0, status='success'):
        if not self.connection or not self.connection.is_connected():
            self.logger.error("Database conn not initialized")
            return False
            
        try:
            cursor = self.connection.cursor()
            
            # Check if metadata entry exists
            query = "SELECT COUNT(*) FROM scraper_metadata WHERE source = %s"
            cursor.execute(query, (self.source_name,))
            count = cursor.fetchone()[0]
            
            if count == 0:
                # Insert new metadata entry
                query = """
                INSERT INTO scraper_metadata 
                (source, last_scrape_time, articles_added, articles_updated, last_status) 
                VALUES (%s, NOW(), %s, %s, %s)
                """
                cursor.execute(query, (self.source_name, articles_added, articles_updated, status))
            else:
                # Update existing metadata
                query = """
                UPDATE scraper_metadata 
                SET last_scrape_time = NOW(), 
                    articles_added = articles_added + %s, 
                    articles_updated = articles_updated + %s, 
                    last_status = %s
                WHERE source = %s
                """
                cursor.execute(query, (articles_added, articles_updated, status, self.source_name))
                
            self.connection.commit()
            cursor.close()
            return True
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"Error updating metadata: {e}")
            return False
    
    def scrape(self):
        raise NotImplementedError("Subclasses must implement ")
    
    def run(self):
        """
        Run the full scraping process.
        """
        success = False
        try:
            # Initialize resources
            if not self.initialize_webdriver():
                return False
                
            if not self.initialize_db():
                self.close_webdriver()
                return False
            
            # Run the scraping process
            self.logger.info(f"Starting scraping for {self.source_name}")
            success = self.scrape()
            
            # Update final status
            if success:
                self.logger.info(f"Scraping completed successfully for {self.source_name}")
                self.update_metadata(status='success')
            else:
                self.logger.error(f"Scraping failed for {self.source_name}")
                self.update_metadata(status='failed')
                
        except Exception as e:
            self.logger.error(f"Error during scraping process: {e}")
            self.update_metadata(status='error')
            success = False
            
        finally:
            # Clean up resources
            self.close_webdriver()
            self.close_db()
            
        return success