"""
Competitor analysis scraper - Free implementation.
Uses direct HTTP requests and meta tag extraction.
"""

import httpx
from urllib.parse import urlparse
from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup
from loguru import logger


class CompetitorScraper:
    """Scrape competitor websites for analysis."""
    
    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0"
        }
    
    async def scrape(self, url: str) -> Dict[str, Any]:
        """
        Scrape a competitor website.
        
        Args:
            url: Website URL to scrape
        
        Returns:
            Scraped data or error info
        """
        # Normalize URL
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract meta data
                data = {
                    "url": url,
                    "title": self._get_title(soup),
                    "description": self._get_meta(soup, "description"),
                    "keywords": self._get_keywords(soup),
                    "og_title": self._get_meta(soup, "og:title"),
                    "og_description": self._get_meta(soup, "og:description"),
                    "h1_tags": self._get_h1_tags(soup),
                    "text_preview": self._get_text_preview(soup),
                    "links": self._get_external_links(soup, url),
                    "success": True,
                }
                
                return data
                
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error scraping {url}: {e.response.status_code}")
            return {
                "url": url,
                "success": False,
                "error": f"HTTP {e.response.status_code}",
                "error_type": "http_error"
            }
        except httpx.ConnectError as e:
            logger.warning(f"Connection error scraping {url}: {e}")
            return {
                "url": url,
                "success": False,
                "error": "Connection failed - site may block scraping",
                "error_type": "connection_error"
            }
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return {
                "url": url,
                "success": False,
                "error": str(e),
                "error_type": "unknown"
            }
    
    def _get_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract page title."""
        title_tag = soup.find('title')
        return title_tag.get_text(strip=True) if title_tag else None
    
    def _get_meta(self, soup: BeautifulSoup, name: str) -> Optional[str]:
        """Extract meta tag content."""
        # Try name attribute
        tag = soup.find('meta', attrs={'name': name})
        if tag:
            return tag.get('content')
        
        # Try property attribute (OpenGraph)
        tag = soup.find('meta', attrs={'property': name})
        if tag:
            return tag.get('content')
        
        return None
    
    def _get_keywords(self, soup: BeautifulSoup) -> List[str]:
        """Extract keywords from meta tags."""
        keywords_str = self._get_meta(soup, 'keywords')
        if keywords_str:
            return [k.strip() for k in keywords_str.split(',') if k.strip()]
        return []
    
    def _get_h1_tags(self, soup: BeautifulSoup) -> List[str]:
        """Extract H1 tags."""
        h1s = soup.find_all('h1')
        return [h.get_text(strip=True) for h in h1s if h.get_text(strip=True)]
    
    def _get_text_preview(self, soup: BeautifulSoup, max_length: int = 2000) -> str:
        """Extract text preview from body."""
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer"]):
            script.decompose()
        
        # Get text
        text = soup.get_text(separator=' ', strip=True)
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text[:max_length]
    
    def _get_external_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract external links."""
        base_domain = urlparse(base_url).netloc
        links = []
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('http'):
                domain = urlparse(href).netloc
                if domain != base_domain:
                    links.append(href)
        
        return list(set(links))[:10]  # Limit to 10 unique links


# Pricing extraction patterns
PRICING_KEYWORDS = [
    "price", "pricing", "plan", "subscription", "$", "€", "£",
    "month", "year", "monthly", "yearly", "annual", "free trial",
    "starter", "professional", "enterprise", "basic", "premium"
]


def extract_picing_indicators(text: str) -> List[str]:
    """
    Extract potential pricing indicators from text.
    
    Args:
        text: Text content to analyze
    
    Returns:
        List of sentences containing pricing keywords
    """
    import re
    
    sentences = re.split(r'[.!?]+', text)
    indicators = []
    
    for sentence in sentences:
        sentence = sentence.strip().lower()
        if any(keyword in sentence for keyword in PRICING_KEYWORDS):
            # Get original case version
            original = text[text.lower().find(sentence):text.lower().find(sentence) + len(sentence)]
            if len(sentence) > 20:  # Filter out very short fragments
                indicators.append(original[:200])
    
    return indicators[:5]  # Return top 5


async def scrape_multiple(urls: List[str]) -> List[Dict[str, Any]]:
    """
    Scrape multiple competitor URLs.
    
    Args:
        urls: List of URLs to scrape
    
    Returns:
        List of scrape results
    """
    scraper = CompetitorScraper()
    results = []
    
    for url in urls:
        result = await scraper.scrape(url)
        results.append(result)
    
    return results
