"""HTML to text extraction using readability-lxml and BeautifulSoup."""

import logging
import re
from typing import Optional

from bs4 import BeautifulSoup
from readability import Document

logger = logging.getLogger(__name__)


def extract_text(html: str, max_length: int = 50000) -> Optional[str]:
    """
    Extract clean text content from HTML.

    Args:
        html: Raw HTML string
        max_length: Maximum text length to return

    Returns:
        Cleaned text content or None on error
    """
    try:
        # Use readability to extract main content
        doc = Document(html)
        content_html = doc.summary()
        
        # Parse with BeautifulSoup for text extraction
        soup = BeautifulSoup(content_html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text
        text = soup.get_text(separator=' ', strip=True)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Truncate if needed
        if len(text) > max_length:
            text = text[:max_length]
            logger.debug(f"Text truncated to {max_length} characters")
        
        logger.debug(f"Extracted {len(text)} characters of text")
        return text
        
    except Exception as e:
        logger.error(f"Error extracting text from HTML: {e}")
        return None


def extract_metadata(html: str) -> dict:
    """
    Extract metadata from HTML (title, meta tags, etc.).

    Args:
        html: Raw HTML string

    Returns:
        Dictionary with metadata fields
    """
    metadata = {
        "title": None,
        "meta_description": None,
        "canonical_url": None,
        "h1_tags": [],
        "headings_count": {"h1": 0, "h2": 0, "h3": 0, "h4": 0, "h5": 0, "h6": 0},
    }
    
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract title
        title_tag = soup.find('title')
        if title_tag:
            metadata["title"] = title_tag.get_text(strip=True)
        
        # Extract meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            metadata["meta_description"] = meta_desc['content']
        
        # Extract canonical URL
        canonical = soup.find('link', attrs={'rel': 'canonical'})
        if canonical and canonical.get('href'):
            metadata["canonical_url"] = canonical['href']
        
        # Extract H1 tags
        h1_tags = soup.find_all('h1')
        metadata["h1_tags"] = [h1.get_text(strip=True) for h1 in h1_tags]
        
        # Count all headings
        for level in range(1, 7):
            headings = soup.find_all(f'h{level}')
            metadata["headings_count"][f"h{level}"] = len(headings)
        
        logger.debug(f"Extracted metadata: title={metadata['title'][:50] if metadata['title'] else 'None'}")
        
    except Exception as e:
        logger.error(f"Error extracting metadata: {e}")
    
    return metadata
