"""
Web scraping utilities for DocSynapse
"""
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
import logging
import asyncio
import aiohttp
import re
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class WebScraper:
    def __init__(self, session: Optional[aiohttp.ClientSession] = None):
        self.session = session

        # Language filtering patterns to exclude non-English content
        self.exclude_language_patterns = [
            r'/zh-?(?:cn|tw|hans?|hant?)\b',  # Chinese variants
            r'/ja\b',                         # Japanese
            r'/ko\b',                         # Korean
            r'/fr\b',                         # French
            r'/de\b',                         # German
            r'/es\b',                         # Spanish
            r'/pt\b',                         # Portuguese
            r'/it\b',                         # Italian
            r'/ru\b',                         # Russian
            r'/ar\b',                         # Arabic
            r'/hi\b',                         # Hindi
            r'/hu\b',                         # Hungarian
            r'/nl\b',                         # Dutch
            r'/sv\b',                         # Swedish
            r'/pl\b',                         # Polish
            r'/no\b',                         # Norwegian
            r'/da\b',                         # Danish
            r'/fi\b',                         # Finnish
        ]

    def _is_english_url(self, url: str) -> bool:
        """Check if URL is likely English content."""
        url_lower = url.lower()

        # Check for language patterns that indicate non-English content
        for pattern in self.exclude_language_patterns:
            if re.search(pattern, url_lower):
                return False

        # Additional checks for common non-English indicators
        non_english_indicators = [
            '/locale/', '/lang/', '/language/', '/intl/',
            '?lang=', '&lang=', '?locale=', '&locale=',
            '/docs/zh', '/docs/ja', '/docs/ko', '/docs/fr',
            '/docs/de', '/docs/es', '/docs/pt', '/docs/it',
            '/docs/ru', '/docs/ar', '/docs/hi', '/docs/hu'
        ]

        for indicator in non_english_indicators:
            if indicator in url_lower:
                return False

        return True

    def _is_valid_documentation_url(self, url: str, base_domain: str) -> bool:
        """Check if URL is valid documentation URL in English."""
        try:
            parsed = urlparse(url)

            # Must be same domain
            if base_domain not in parsed.netloc:
                return False

            # Must be English content
            if not self._is_english_url(url):
                return False

            # Avoid common non-content URLs
            excluded_paths = [
                '/api/', '/assets/', '/static/', '/images/', '/css/', '/js/',
                '/fonts/', '/_next/', '/favicon', '.png', '.jpg', '.gif',
                '.css', '.js', '.svg', '.ico'
            ]

            for excluded in excluded_paths:
                if excluded in url.lower():
                    return False

            return True

        except Exception:
            return False

    async def discover_urls(self, start_url: str,
                            max_pages: int = 100) -> List[str]:
        """Discover URLs from the website using BFS approach."""
        if not self.session:
            raise ValueError("Session not initialized")

        discovered_urls = set()
        visited_urls = set()
        to_visit = [start_url]
        base_domain = urlparse(start_url).netloc

        while to_visit and len(discovered_urls) < max_pages:
            current_batch = to_visit[:10]  # Process in batches
            to_visit = to_visit[10:]

            tasks = []
            for url in current_batch:
                if url not in visited_urls:
                    visited_urls.add(url)
                    tasks.append(
                        self._extract_links_from_page(url, base_domain)
                    )

            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)

                for result in results:
                    if isinstance(result, Exception):
                        continue
                    if result:
                        new_links = {
                            link for link in result
                            if link not in visited_urls
                            and link not in discovered_urls
                        }
                        to_visit.extend(new_links)
                        discovered_urls.update(result)

        return list(discovered_urls)[:max_pages]
    async def _extract_links_from_page(
        self, url: str, base_domain: str
    ) -> List[str]:
        """Extract documentation links from a single page."""
        try:
            async with self.session.get(url, timeout=30) as response:
                if response.status != 200:
                    return []

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                links = []
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    full_url = urljoin(url, href)

                    if self._is_valid_documentation_url(full_url, base_domain):
                        links.append(full_url)

                return links

        except Exception as e:
            logger.warning(f"Failed to extract links from {url}: {e}")
            return []

    async def scrape_page(self, url: str) -> Optional[Dict[str, str]]:
        """Scrape content from a single page."""
        if not self.session:
            raise ValueError("Session not initialized")

        try:
            async with self.session.get(url, timeout=30) as response:
                if response.status != 200:
                    msg = f"Failed to fetch {url}: HTTP {response.status}"
                    logger.warning(msg)
                    return None

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                # Remove unwanted elements
                for element in soup(['script', 'style', 'nav', 'header',
                                    'footer', 'aside']):
                    element.decompose()

                # Extract title
                title = ""
                if soup.title:
                    title = soup.title.get_text().strip()
                elif soup.h1:
                    title = soup.h1.get_text().strip()

                # Extract main content
                content = ""
                main_content = (soup.find('main') or
                               soup.find('article') or soup)
                if main_content:
                    content = main_content.get_text().strip()

                # Clean up content
                content = re.sub(r'\s+', ' ', content)

                # Skip pages with minimal content
                if len(content.strip()) < 100:
                    return None

                return {
                    "url": url,
                    "title": title,
                    "content": content,
                    "word_count": str(len(content.split()))
                }

        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None
