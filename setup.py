"""
Database setup script for Kenya news scraping project.
Creates necessary tables for storing news articles from different sources.
"""
import logging
import os
import sys

# Add parent directory to sys.path to allow imports from sibling modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from config.database import get_connection

# Define the news sources
NEWS_SOURCES = [
    'citizen',
    'daily_nations',
    'standardmedia',
    'star',
    'tuko'
]

def setup_database():
    """
    Create the necessary tables for each news source if they don't exist.
    """
    connection = get_connection()
    if not connection:
        logging.error("Failed to connect to database. Cannot set up tables.")
        return False
    
    cursor = connection.cursor()
    success = True
    
    try:
        # Create a table for each news source
        for source in NEWS_SOURCES:
            table_name = f"{source}_articles"
            
            # SQL for creating the table with all required columns
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                url VARCHAR(255) NOT NULL UNIQUE,
                title VARCHAR(255) NOT NULL,
                publication_date DATETIME,
                author VARCHAR(100),
                content TEXT NOT NULL,
                category VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                sentiment_score FLOAT DEFAULT NULL,
                INDEX idx_url (url),
                INDEX idx_publication_date (publication_date),
                INDEX idx_category (category)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
            
            cursor.execute(create_table_sql)
            logging.info(f"Table '{table_name}' created or already exists.")
        
        # Create a metadata table to track last scrape times
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS scraper_metadata (
            source VARCHAR(50) PRIMARY KEY,
            last_scrape_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            articles_added INT DEFAULT 0,
            articles_updated INT DEFAULT 0,
            last_status VARCHAR(20) DEFAULT 'success'
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
        
        connection.commit()
        logging.info("All database tables have been set up successfully.")
    
    except Exception as e:
        connection.rollback()
        logging.error(f"Error setting up database tables: {e}")
        success = False
    
    finally:
        cursor.close()
        connection.close()
        logging.info("Database connection closed.")
    
    return success

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("logs/database_setup.log"),
            logging.StreamHandler()
        ]
    )
    
    logging.info("Starting database setup...")
    if setup_database():
        print("Database setup completed successfully.")
    else:
        print("Database setup encountered errors. Check the logs.")