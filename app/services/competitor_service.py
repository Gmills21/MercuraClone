"""
Competitor Analysis Service for OpenMercura
Free implementation using web scraping and free search APIs
"""

import json
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from app.utils.resilience import (
    with_retry,
    RetryConfig,
    CircuitBreaker,
    CircuitBreakerOpen
)

logger = logging.getLogger(__name__)

# Retry configuration for web scraping
SCRAPING_RETRY_CONFIG = RetryConfig(
    max_attempts=2,
    base_delay=1.0,
    max_delay=10.0,
    retryable_exceptions=[
        httpx.TimeoutException,
        httpx.ConnectError,
        httpx.NetworkError
    ]
)


@dataclass
class CompetitorData:
    """Data structure for competitor information."""
    url: str
    name: str
    title: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[List[str]] = None
    pricing: Optional[str] = None
    features: Optional[List[str]] = None
    last_updated: str = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.utcnow().isoformat()


class CompetitorAnalysisService:
    """Service for analyzing competitor websites."""
    
    def __init__(self):
        self.timeout = 30.0
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
        self.circuit_breaker = CircuitBreaker("competitor_scraping")

        
    async def analyze_url(self, url: str) -> CompetitorData:
        """
        Analyze a competitor URL and extract key information.
        
        Args:
            url: The competitor website URL
            
        Returns:
            CompetitorData with extracted information
        """
        # Validate URL
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        if self.circuit_breaker.is_open:
            return CompetitorData(
                url=url,
                name=urlparse(url).netloc,
                error="Competitor analysis temporarily unavailable due to recent errors"
            )
        
        @self.circuit_breaker.protect
        async def _fetch_and_parse():
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
                response = await client.get(url)
                
                # Handle rate limiting
                if response.status_code == 429:
                    return CompetitorData(
                        url=url,
                        name=urlparse(url).netloc,
                        error="Rate limited - too many requests"
                    )
                
                # Handle other errors
                if response.status_code != 200:
                    return CompetitorData(
                        url=url,
                        name=urlparse(url).netloc,
                        error=f"HTTP {response.status_code} - Data unavailable"
                    )
                
                # Parse HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract data
                return CompetitorData(
                    url=url,
                    name=self._extract_name(soup, url),
                    title=self._extract_title(soup),
                    description=self._extract_description(soup),
                    keywords=self._extract_keywords(soup),
                    pricing=self._extract_pricing(soup),
                    features=self._extract_features(soup)
                )
        
        try:
            return await with_retry(_fetch_and_parse, config=SCRAPING_RETRY_CONFIG)
        except httpx.TimeoutException:
            return CompetitorData(
                url=url,
                name=urlparse(url).netloc,
                error="Request timeout - site may be slow or blocking"
            )
        except httpx.ConnectError:
            return CompetitorData(
                url=url,
                name=urlparse(url).netloc,
                error="Connection error - site may be down or blocking"
            )
        except CircuitBreakerOpen:
            return CompetitorData(
                url=url,
                name=urlparse(url).netloc,
                error="Competitor analysis temporarily unavailable"
            )
        except Exception as e:
            logger.error(f"Error analyzing {url}: {e}")
            return CompetitorData(
                url=url,
                name=urlparse(url).netloc,
                error=f"Analysis failed: {str(e)}"
            )
    
    async def analyze_multiple(
        self, 
        urls: List[str]
    ) -> List[CompetitorData]:
        """
        Analyze multiple competitor URLs.
        
        Args:
            urls: List of competitor URLs
            
        Returns:
            List of CompetitorData
        """
        results = []
        for url in urls:
            data = await self.analyze_url(url)
            results.append(data)
            # Small delay to be respectful
            time.sleep(0.5)
        return results
    
    async def compare_competitors(
        self,
        urls: List[str],
        our_product: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a comparison table of competitors.
        
        Args:
            urls: List of competitor URLs to compare
            our_product: Optional our product data for comparison
            
        Returns:
            Comparison data structure
        """
        competitors = await self.analyze_multiple(urls)
        
        comparison = {
            "generated_at": datetime.utcnow().isoformat(),
            "competitor_count": len(urls),
            "competitors": [],
            "our_product": our_product,
            "summary": {
                "successful_analyses": sum(1 for c in competitors if not c.error),
                "failed_analyses": sum(1 for c in competitors if c.error),
                "common_keywords": [],
                "pricing_range": {"min": None, "max": None}
            }
        }
        
        # Process each competitor
        all_keywords = []
        prices = []
        
        for comp in competitors:
            comp_dict = {
                "name": comp.name,
                "url": comp.url,
                "title": comp.title,
                "description": comp.description,
                "features": comp.features,
                "pricing": comp.pricing,
                "error": comp.error
            }
            
            if comp.keywords:
                all_keywords.extend(comp.keywords)
            
            # Try to extract numeric price
            if comp.pricing:
                price_val = self._extract_price_value(comp.pricing)
                if price_val:
                    prices.append(price_val)
                    comp_dict["price_numeric"] = price_val
            
            comparison["competitors"].append(comp_dict)
        
        # Calculate summary stats
        keyword_freq = {}
        for kw in all_keywords:
            keyword_freq[kw.lower()] = keyword_freq.get(kw.lower(), 0) + 1
        
        comparison["summary"]["common_keywords"] = [
            {"keyword": k, "count": v} 
            for k, v in sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        if prices:
            comparison["summary"]["pricing_range"] = {
                "min": min(prices),
                "max": max(prices),
                "average": round(sum(prices) / len(prices), 2)
            }
        
        return comparison
    
    def _extract_name(self, soup: BeautifulSoup, url: str) -> str:
        """Extract company name from the page."""
        # Try og:site_name first
        site_name = soup.find('meta', property='og:site_name')
        if site_name and site_name.get('content'):
            return site_name['content'].strip()
        
        # Try logo alt text
        logo = soup.find('img', class_=lambda x: x and 'logo' in x.lower())
        if logo and logo.get('alt'):
            return logo['alt'].strip()
        
        # Try title
        if soup.title:
            title = soup.title.string.strip()
            # Remove common suffixes
            for suffix in [' - Home', ' | Home', ' - ', ' | ']:
                if suffix in title:
                    return title.split(suffix)[0].strip()
            return title
        
        # Fallback to domain
        return urlparse(url).netloc.replace('www.', '')
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract page title."""
        if soup.title:
            return soup.title.string.strip()
        
        og_title = soup.find('meta', property='og:title')
        if og_title:
            return og_title.get('content', '').strip()
        
        return None
    
    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract meta description."""
        # Try meta description
        desc = soup.find('meta', attrs={'name': 'description'})
        if desc:
            return desc.get('content', '').strip()
        
        # Try og:description
        og_desc = soup.find('meta', property='og:description')
        if og_desc:
            return og_desc.get('content', '').strip()
        
        return None
    
    def _extract_keywords(self, soup: BeautifulSoup) -> Optional[List[str]]:
        """Extract keywords from meta tags and content."""
        keywords = []
        
        # Try meta keywords
        meta_kw = soup.find('meta', attrs={'name': 'keywords'})
        if meta_kw:
            content = meta_kw.get('content', '')
            keywords = [k.strip() for k in content.split(',') if k.strip()]
        
        # Extract from headings if no meta keywords
        if not keywords:
            for heading in soup.find_all(['h1', 'h2']):
                text = heading.get_text(strip=True)
                if text and len(text) < 100:
                    keywords.append(text)
        
        return keywords[:10] if keywords else None
    
    def _extract_pricing(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract pricing information from the page."""
        pricing_keywords = ['price', 'pricing', 'cost', 'plan', 'subscription', '$', '€', '£']
        
        # Look for pricing sections
        for elem in soup.find_all(['div', 'section', 'span', 'p']):
            text = elem.get_text(strip=True).lower()
            if any(kw in text for kw in pricing_keywords):
                # Check if it contains dollar amounts
                parent = elem.parent
                if parent:
                    parent_text = parent.get_text(strip=True)
                    if len(parent_text) < 500:  # Keep it concise
                        return parent_text[:200]
        
        return None
    
    def _extract_features(self, soup: BeautifulSoup) -> Optional[List[str]]:
        """Extract feature list from the page."""
        features = []
        
        # Look for feature lists
        feature_selectors = [
            '.feature', '.features', '.feature-list',
            '[class*="feature"]', '[class*="benefit"]'
        ]
        
        for selector in feature_selectors:
            elems = soup.select(selector)
            for elem in elems:
                text = elem.get_text(strip=True)
                if text and 10 < len(text) < 200:
                    features.append(text[:150])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_features = []
        for f in features:
            key = f.lower()[:50]
            if key not in seen:
                seen.add(key)
                unique_features.append(f)
        
        return unique_features[:10] if unique_features else None
    
    def _extract_price_value(self, text: str) -> Optional[float]:
        """Extract numeric price value from text."""
        import re
        
        # Look for dollar amounts
        pattern = r'\$[\d,]+(?:\.\d{2})?'
        matches = re.findall(pattern, text)
        
        if matches:
            # Take the first price found
            price_str = matches[0].replace('$', '').replace(',', '')
            try:
                return float(price_str)
            except ValueError:
                pass
        
        return None
    
    async def search_competitors(
        self,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, str]]:
        """
        Search for competitors using free search (DuckDuckGo).
        
        Args:
            query: Search query
            limit: Number of results to return
            
        Returns:
            List of search results with title and URL
        """
        # DuckDuckGo HTML search (no API key required)
        search_url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
                response = await client.get(search_url)
                
                if response.status_code != 200:
                    return []
                
                soup = BeautifulSoup(response.text, 'html.parser')
                results = []
                
                # Parse search results
                for result in soup.find_all('div', class_='result'):
                    title_elem = result.find('a', class_='result__a')
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        url = title_elem.get('href', '')
                        
                        # Extract URL from DuckDuckGo redirect
                        if url.startswith('/l/?'):
                            import urllib.parse
                            parsed = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
                            if 'uddg' in parsed:
                                url = parsed['uddg'][0]
                        
                        results.append({
                            "title": title,
                            "url": url
                        })
                        
                        if len(results) >= limit:
                            break
                
                return results
                
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []


# Global service instance
competitor_service = CompetitorAnalysisService()
