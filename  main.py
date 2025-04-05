import os
import sys
import logging
import argparse
from datetime import datetime

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Import all scrapers
from scrapers.citizen import CitizenScraper
from scrapers.daily_nations import DailyNationsScraper
from scrapers.standardmedia import StandardMediaScraper
from scrapers.star import StarScraper
from scrapers.tuko_new import TukoScraper


def setup_main_logger():
    """Set up the main logger."""
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    # Create logger
    logger = logging.getLogger('main')
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers if any
    if logger.handlers:
        logger.handlers = []
    
    # Create log filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f"logs/main_{timestamp}.log"
    
    # File handler
    file_handler = logging.FileHandler(log_file)
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


def run_scraper(scraper_class, logger):
    scraper_name = scraper_class.__name__
    try:
        logger.info(f"Starting {scraper_name}")
        scraper = scraper_class()
        success = scraper.run()
        status = "successful" if success else "failed"
        logger.info(f"{scraper_name} completed: {status}")
        return success
    except Exception as e:
        logger.error(f"Error running {scraper_name}: {e}")
        return False


def main():
    """Main function to run all scrapers."""
    logger = setup_main_logger()
    logger.info("Starting Kenya News scraping process")
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run Kenya News scrapers')
    parser.add_argument('--sources', nargs='+', help='Specific sources to scrape')
    args = parser.parse_args()
    
    # Map of available scrapers
    scrapers = {
        'citizen': CitizenScraper,
        'daily_nations': DailyNationsScraper,
        'standardmedia': StandardMediaScraper,
        'star': StarScraper,
        'tuko': TukoScraper
    }
    
    # Determine which scrapers to run
    scrapers_to_run = {}
    if args.sources:
        # Run only specified sources
        for source in args.sources:
            if source in scrapers:
                scrapers_to_run[source] = scrapers[source]
            else:
                logger.warning(f"Unknown source: {source}")
    else:
        # Run all scrapers
        scrapers_to_run = scrapers
    
    if not scrapers_to_run:
        logger.error("No valid scrapers to run")
        return False
    
    # Run each scraper
    results = {}
    for name, scraper_class in scrapers_to_run.items():
        logger.info(f"Running {name} scraper")
        success = run_scraper(scraper_class, logger)
        results[name] = success
    
    # Log summary
    logger.info("Scraping process completed")
    logger.info("Summary:")
    for name, success in results.items():
        logger.info(f"  {name}: {'Success' if success else 'Failed'}")
    
    # Check if all scrapers succeeded
    all_success = all(results.values())
    logger.info(f"Overall status: {'Success' if all_success else 'Partial failure'}")
    
    return all_success


if __name__ == "__main__":
    exit_code = 0 if main() else 1
    sys.exit(exit_code)