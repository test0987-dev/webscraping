"""
Date parsing utilities for the Kenya news scraping project.
"""
import re
from datetime import datetime, timedelta


def parse_date(date_text):
    """
    Parse date text from various formats to a datetime object.
    
    Args:
        date_text (str): Date text from an article
        
    Returns:
        datetime: Parsed datetime object or None if parsing fails
    """
    if not date_text:
        return None
    
    date_text = date_text.strip().lower()
    
    try:
        # Try common date formats
        for fmt in ('%B %d, %Y', '%d %B %Y', '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y'):
            try:
                return datetime.strptime(date_text, fmt)
            except ValueError:
                continue
        
        # Handle relative dates like "2 days ago", "yesterday", etc.
        if 'ago' in date_text:
            # Extract the number and unit (e.g., "2 days ago")
            match = re.search(r'(\d+)\s+(\w+)\s+ago', date_text)
            if match:
                num = int(match.group(1))
                unit = match.group(2).rstrip('s')  # Remove plural 's' if present
                
                now = datetime.now()
                if unit in ('second', 'sec'):
                    return now - timedelta(seconds=num)
                elif unit in ('minute', 'min'):
                    return now - timedelta(minutes=num)
                elif unit in ('hour', 'hr'):
                    return now - timedelta(hours=num)
                elif unit in ('day',):
                    return now - timedelta(days=num)
                elif unit in ('week', 'wk'):
                    return now - timedelta(weeks=num)
                elif unit in ('month', 'mo'):
                    # Approximate a month as 30 days
                    return now - timedelta(days=num*30)
                elif unit in ('year', 'yr'):
                    # Approximate a year as 365 days
                    return now - timedelta(days=num*365)
        
        # Handle "yesterday", "today"
        if 'yesterday' in date_text:
            return datetime.now() - timedelta(days=1)
        elif 'today' in date_text:
            return datetime.now()
        
        # Last resort: try to extract a date with a regex
        date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', date_text)
        if date_match:
            day, month, year = map(int, date_match.groups())
            # Fix two-digit years
            if year < 100:
                year += 2000 if year < 50 else 1900
            return datetime(year, month, day)
        
        return None
    
    except Exception as e:
        print(f"Error parsing date '{date_text}': {e}")
        return None