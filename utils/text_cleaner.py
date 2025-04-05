"""
Text cleaning utilities for the Kenya news scraping project.
"""
import re
import html


def clean_text(text):
    """
    Clean text by removing extra whitespace, HTML entities, and other issues.
    
    Args:
        text (str): The text to clean
        
    Returns:
        str: Cleaned text
    """
    if not text:
        return ""
    
    # Decode HTML entities
    text = html.unescape(text)
    
    # Replace newlines and tabs with spaces
    text = re.sub(r'[\n\t\r]+', ' ', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


def extract_summary(content, max_words=50):
    """
    Extract a summary from the article content.
    
    Args:
        content (str): The article content
        max_words (int): Maximum number of words for the summary
        
    Returns:
        str: Article summary
    """
    if not content:
        return ""
    
    # Get the first paragraph or start of the content
    first_para = content.split('\n')[0] if '\n' in content else content
    
    # Split into words and limit to max_words
    words = first_para.split()
    if len(words) <= max_words:
        return first_para
    
    # Join the first max_words
    summary = ' '.join(words[:max_words]) + '...'
    return summary