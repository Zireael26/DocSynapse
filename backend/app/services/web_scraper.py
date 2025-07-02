import asyncio
import time
from typing import List, Set, Optional, Dict, Any
from urllib.parse import urljoin, urlparse
import aiohttp
from bs4 import BeautifulSoup
from app.core.logging import logger
from app.schemas.job_schemas import ScrapingProgress
import re

class WebScraper:
    def __init__(self, max_concurrent: int = 10, delay: float = 1.0, max_pages: int = 100):
        self.max_concurrent = max_concurrent
        self.delay = delay
        self.max_pages = max_pages
        self.semaphore = asyncio.Semaphore(max_concurrent)

        # Language filtering patterns
        self.non_english_patterns = [
            r'/zh/',      # Chinese
            r'/zh-cn/',   # Simplified Chinese
            r'/zh-tw/',   # Traditional Chinese
            r'/zh-hant/', # Traditional Chinese (Hong Kong/Taiwan)
            r'/ja/',      # Japanese
            r'/ko/',      # Korean
            r'/fr/',      # French
            r'/de/',      # German
            r'/es/',      # Spanish
            r'/it/',      # Italian
            r'/pt/',      # Portuguese
            r'/ru/',      # Russian
            r'/ar/',      # Arabic
            r'/hi/',      # Hindi
            r'/hu/',      # Hungarian
            r'/nl/',      # Dutch
            r'/sv/',      # Swedish
            r'/no/',      # Norwegian
            r'/da/',      # Danish
            r'/fi/',      # Finnish
            r'/pl/',      # Polish
            r'/tr/',      # Turkish
            r'/th/',      # Thai
            r'/vi/',      # Vietnamese
        ]

        # Compile patterns for better performance
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.non_english_patterns]

    def is_english_url(self, url: str) -> bool:
        """Check if URL is likely English content based on language codes in path"""
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()

        # Check against known non-English patterns
        for pattern in self.compiled_patterns:
            if pattern.search(path):
                return False

        return True

    def should_skip_url(self, url: str, base_domain: str) -> bool:
        """Determine if URL should be skipped based on various criteria"""
        parsed_url = urlparse(url)

        # Skip if different domain
        if parsed_url.netloc and parsed_url.netloc not in base_domain:
            return True

        # Skip non-English URLs
        if not self.is_english_url(url):
            logger.info(f"Skipping non-English URL: {url}")
            return True

        # Skip common non-content URLs
        skip_patterns = [
            r'/api/',
            r'/downloads?/',
            r'/login',
            r'/register',
            r'/auth/',
            r'/admin/',
            r'\.pdf$',
            r'\.zip$',
            r'\.tar\.gz$',
            r'/search',
            r'/contact',
            r'/privacy',
            r'/terms',
        ]

        path = parsed_url.path.lower()
        for pattern in skip_patterns:
            if re.search(pattern, path):
                return True

        return False

    async def fetch(self, session: aiohttp.ClientSession, url: str) -> Optional[str]:
        """Fetch content from a URL using aiohttp"""
        try:
            async with self.semaphore:
                await asyncio.sleep(self.delay)
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        logger.warning(f"Received non-200 response: {response.status} for URL: {url}")
        except Exception as e:
            logger.error(f"Error fetching URL {url}: {e}")
        return None

    def extract_links(self, html: str, base_url: str) -> Set[str]:
        """Extract and normalize links from HTML content"""
        soup = BeautifulSoup(html, 'html.parser')
        links = set()

        for tag in soup.find_all('a', href=True):
            url = tag['href']
            # Join relative URLs with the base URL
            full_url = urljoin(base_url, url)
            links.add(full_url)

        return links

    async def scrape_page(self, session: aiohttp.ClientSession, url: str, base_domain: str) -> Set[str]:
        """Scrape a single page for links"""
        html = await self.fetch(session, url)
        if html:
            return self.extract_links(html, url)
        return set()

    async def scrape(self, start_url: str) -> Set[str]:
        """Main scraping method"""
        visited = set()
        to_visit = {start_url}
        base_domain = urlparse(start_url).netloc

        async with aiohttp.ClientSession() as session:
            while to_visit and len(visited) < self.max_pages:
                url = to_visit.pop()
                if url in visited or self.should_skip_url(url, base_domain):
                    continue

                logger.info(f"Scraping URL: {url}")
                visited.add(url)
                links = await self.scrape_page(session, url, base_domain)
                to_visit.update(links - visited)

        return visited

    def run(self, start_url: str) -> Set[str]:
        """Run the scraper"""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.scrape(start_url))
