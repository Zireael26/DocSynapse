import re
from urllib.parse import urlparse
import aiohttp
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class ScrapingService:
    # ...existing code...

    def _should_skip_url(self, url: str, base_domain: str) -> bool:
        """Check if URL should be skipped based on language patterns"""
        try:
            parsed_url = urlparse(url)
            path = parsed_url.path.lower()

            # Common non-English language codes in URLs
            non_english_patterns = [
                r'/zh(-\w+)?/',  # Chinese variants (zh, zh-cn, zh-tw, zh-hant)
                r'/ja(-\w+)?/',  # Japanese
                r'/ko(-\w+)?/',  # Korean
                r'/fr(-\w+)?/',  # French
                r'/de(-\w+)?/',  # German
                r'/es(-\w+)?/',  # Spanish
                r'/pt(-\w+)?/',  # Portuguese
                r'/it(-\w+)?/',  # Italian
                r'/ru(-\w+)?/',  # Russian
                r'/ar(-\w+)?/',  # Arabic
                r'/hi(-\w+)?/',  # Hindi
                r'/hu(-\w+)?/',  # Hungarian
                r'/nl(-\w+)?/',  # Dutch
                r'/sv(-\w+)?/',  # Swedish
                r'/da(-\w+)?/',  # Danish
                r'/no(-\w+)?/',  # Norwegian
                r'/fi(-\w+)?/',  # Finnish
                r'/pl(-\w+)?/',  # Polish
                r'/cs(-\w+)?/',  # Czech
                r'/sk(-\w+)?/',  # Slovak
                r'/bg(-\w+)?/',  # Bulgarian
                r'/hr(-\w+)?/',  # Croatian
                r'/sr(-\w+)?/',  # Serbian
                r'/sl(-\w+)?/',  # Slovenian
                r'/et(-\w+)?/',  # Estonian
                r'/lv(-\w+)?/',  # Latvian
                r'/lt(-\w+)?/',  # Lithuanian
                r'/mt(-\w+)?/',  # Maltese
                r'/tr(-\w+)?/',  # Turkish
                r'/he(-\w+)?/',  # Hebrew
                r'/th(-\w+)?/',  # Thai
                r'/vi(-\w+)?/',  # Vietnamese
                r'/id(-\w+)?/',  # Indonesian
                r'/ms(-\w+)?/',  # Malay
                r'/tl(-\w+)?/',  # Filipino
            ]

            # Check for language patterns in path
            for pattern in non_english_patterns:
                if re.search(pattern, path):
                    return True

            # Check for language subdomain patterns (e.g., fr.example.com)
            host_parts = parsed_url.hostname.split('.') if parsed_url.hostname else []
            if len(host_parts) > 2:
                subdomain = host_parts[0].lower()
                non_english_subdomains = {
                    'zh', 'ja', 'ko', 'fr', 'de', 'es', 'pt', 'it', 'ru',
                    'ar', 'hi', 'hu', 'nl', 'sv', 'da', 'no', 'fi', 'pl',
                    'cs', 'sk', 'bg', 'hr', 'sr', 'sl', 'et', 'lv', 'lt',
                    'mt', 'tr', 'he', 'th', 'vi', 'id', 'ms', 'tl'
                }
                if subdomain in non_english_subdomains:
                    return True

            return False

        except Exception as e:
            logger.warning(f"Error checking URL pattern for {url}: {e}")
            return False

    # ...existing code...

    async def _crawl_page(self, session: aiohttp.ClientSession, url: str, visited: set,
                         to_visit: list, base_domain: str, max_pages: int,
                         max_depth: int, current_depth: int = 0) -> Optional[Dict]:
        # ...existing validation code...

        # Add language filtering check
        if self._should_skip_url(url, base_domain):
            logger.info(f"Skipping non-English URL: {url}")
            return None

        # ...rest of existing method...
