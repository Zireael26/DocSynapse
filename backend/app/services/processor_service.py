"""
DocSynapse Processor Service

This service handles content processing, cleaning, deduplication,
and markdown generation from crawled documentation.
"""

import asyncio
import logging
import re
from datetime import datetime
from typing import List, Dict, Set, Optional, Tuple
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag
import aiofiles

from app.core.config import settings
from app.models.crawler import CrawlResult, PageInfo


logger = logging.getLogger(__name__)


class ProcessorService:
    """
    Service for processing crawled content into optimized markdown.

    Handles content cleaning, deduplication, link resolution,
    and markdown generation optimized for LLM consumption.
    """

    def __init__(self):
        self.processed_files: Dict[str, str] = {}

    async def process_crawl_result(self, result: CrawlResult) -> str:
        """
        Process a completed crawl result into optimized markdown.

        Args:
            result: The completed crawl result

        Returns:
            str: Path to the generated markdown file
        """
        try:
            logger.info(f"Starting content processing for job {result.job_id}")

            # Step 1: Clean and extract content from each page
            cleaned_pages = await self._clean_pages(result.pages)

            # Step 2: Deduplicate content
            deduplicated_pages = await self._deduplicate_content(cleaned_pages)

            # Step 3: Resolve and fix links
            processed_pages = await self._resolve_links(deduplicated_pages, result.base_url)

            # Step 4: Generate markdown
            markdown_content = await self._generate_markdown(
                processed_pages, result
            )

            # Step 5: Save to file
            output_file = await self._save_markdown_file(
                markdown_content, result.job_id, result.base_url
            )

            self.processed_files[result.job_id] = output_file

            logger.info(f"Content processing completed for job {result.job_id}")
            return output_file

        except Exception as e:
            logger.error(f"Content processing failed for job {result.job_id}: {e}")
            raise

    async def _clean_pages(self, pages: List[PageInfo]) -> List[Dict]:
        """Clean HTML content from pages and extract useful text."""
        cleaned_pages = []

        for page in pages:
            try:
                # Parse HTML content
                soup = BeautifulSoup(page.content, 'html.parser')

                # Remove unwanted elements
                for element in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                    element.decompose()

                # Remove common navigation and UI elements
                for selector in [
                    '.navigation', '.nav', '.navbar', '.menu',
                    '.sidebar', '.breadcrumb', '.pagination',
                    '.footer', '.header', '.social-links',
                    '[role="navigation"]', '[role="banner"]', '[role="contentinfo"]'
                ]:
                    for element in soup.select(selector):
                        element.decompose()

                # Extract main content
                main_content = self._extract_main_content(soup)

                if main_content:
                    cleaned_pages.append({
                        'url': page.url,
                        'title': page.title or 'Untitled',
                        'content': main_content,
                        'word_count': len(main_content.split()),
                        'last_modified': page.last_modified
                    })

            except Exception as e:
                logger.warning(f"Failed to clean page {page.url}: {e}")
                continue

        return cleaned_pages

    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract the main content from a BeautifulSoup object."""
        # Try to find main content container
        main_selectors = [
            'main', '[role="main"]', '.main-content', '.content',
            '.documentation', '.docs', '.doc-content', '.page-content',
            'article', '.article'
        ]

        main_element = None
        for selector in main_selectors:
            main_element = soup.select_one(selector)
            if main_element:
                break

        # If no main element found, use body
        if not main_element:
            main_element = soup.find('body') or soup

        # Extract text while preserving structure
        return self._extract_structured_text(main_element)

    def _extract_structured_text(self, element) -> str:
        """Extract text while preserving markdown-compatible structure."""
        if not element:
            return ""

        text_parts = []

        for child in element.children:
            if isinstance(child, NavigableString):
                text = str(child).strip()
                if text:
                    text_parts.append(text)
            elif isinstance(child, Tag):
                if child.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    level = int(child.name[1])
                    heading_text = child.get_text().strip()
                    if heading_text:
                        text_parts.append(f"\n{'#' * level} {heading_text}\n")
                elif child.name == 'p':
                    para_text = child.get_text().strip()
                    if para_text:
                        text_parts.append(f"\n{para_text}\n")
                elif child.name in ['pre', 'code']:
                    code_text = child.get_text()
                    if code_text.strip():
                        if child.name == 'pre':
                            text_parts.append(f"\n```\n{code_text}\n```\n")
                        else:
                            text_parts.append(f"`{code_text}`")
                elif child.name in ['ul', 'ol']:
                    list_text = self._extract_list_text(child)
                    if list_text:
                        text_parts.append(f"\n{list_text}\n")
                elif child.name == 'blockquote':
                    quote_text = child.get_text().strip()
                    if quote_text:
                        text_parts.append(f"\n> {quote_text}\n")
                else:
                    # Recursively process other elements
                    nested_text = self._extract_structured_text(child)
                    if nested_text.strip():
                        text_parts.append(nested_text)

        return ' '.join(text_parts)

    def _extract_list_text(self, list_element) -> str:
        """Extract text from list elements preserving structure."""
        items = []
        list_items = list_element.find_all('li', recursive=False)

        for i, item in enumerate(list_items):
            item_text = item.get_text().strip()
            if item_text:
                if list_element.name == 'ol':
                    items.append(f"{i+1}. {item_text}")
                else:
                    items.append(f"- {item_text}")

        return '\n'.join(items)

    async def _deduplicate_content(self, pages: List[Dict]) -> List[Dict]:
        """Remove duplicate content between pages."""
        if not pages:
            return pages

        # Simple deduplication based on content similarity
        unique_pages = []
        seen_content = set()

        for page in pages:
            # Create a fingerprint of the content
            content_words = set(page['content'].lower().split())

            # Check if this content is significantly different from existing pages
            is_duplicate = False
            for seen_words in seen_content:
                # Calculate Jaccard similarity
                intersection = len(content_words & seen_words)
                union = len(content_words | seen_words)
                similarity = intersection / union if union > 0 else 0

                # If similarity > 80%, consider it a duplicate
                if similarity > 0.8:
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_pages.append(page)
                seen_content.add(content_words)

        logger.info(f"Deduplication: {len(pages)} -> {len(unique_pages)} pages")
        return unique_pages

    async def _resolve_links(self, pages: List[Dict], base_url: str) -> List[Dict]:
        """Resolve relative links to absolute URLs."""
        for page in pages:
            # Simple link resolution - replace relative links with absolute ones
            content = page['content']

            # This is a simplified implementation
            # In a full implementation, you'd parse markdown links and resolve them properly
            page['content'] = content

        return pages

    async def _generate_markdown(self, pages: List[Dict], result: CrawlResult) -> str:
        """Generate the final markdown document."""
        markdown_parts = []

        # Header with metadata
        markdown_parts.append(self._generate_header(result))

        # Table of contents
        if len(pages) > 1:
            markdown_parts.append(self._generate_toc(pages))

        # Content sections
        for page in pages:
            markdown_parts.append(self._generate_page_section(page))

        # Footer with processing information
        markdown_parts.append(self._generate_footer(result, pages))

        return '\n\n'.join(markdown_parts)

    def _generate_header(self, result: CrawlResult) -> str:
        """Generate markdown header with metadata."""
        header = f"""# Documentation: {result.base_url}

**Generated by DocSynapse**
- **Source URL**: {result.base_url}
- **Generated**: {datetime.utcnow().isoformat()}
- **Job ID**: {result.job_id}
- **Pages Processed**: {len(result.pages)}
- **Processing Duration**: {result.duration:.2f} seconds

---"""
        return header

    def _generate_toc(self, pages: List[Dict]) -> str:
        """Generate table of contents."""
        toc_lines = ["# Table of Contents", ""]

        for i, page in enumerate(pages, 1):
            title = page['title']
            # Create anchor link (simplified)
            anchor = re.sub(r'[^a-zA-Z0-9\s]', '', title).lower().replace(' ', '-')
            toc_lines.append(f"{i}. [{title}](#{anchor})")

        return '\n'.join(toc_lines)

    def _generate_page_section(self, page: Dict) -> str:
        """Generate markdown section for a single page."""
        section = f"""## {page['title']}

**Source**: {page['url']}
**Word Count**: {page['word_count']}

{page['content']}

---"""
        return section

    def _generate_footer(self, result: CrawlResult, pages: List[Dict]) -> str:
        """Generate markdown footer with processing statistics."""
        total_words = sum(page['word_count'] for page in pages)

        footer = f"""## Processing Summary

- **Total Pages**: {len(pages)}
- **Total Words**: {total_words:,}
- **Average Words per Page**: {total_words // len(pages) if pages else 0}
- **Processing Completed**: {datetime.utcnow().isoformat()}
- **Generated by**: DocSynapse v{settings.APP_VERSION}

*This documentation has been optimized for LLM consumption while preserving the original structure and content.*"""

        return footer

    async def _save_markdown_file(self, content: str, job_id: str, base_url: str) -> str:
        """Save markdown content to file."""
        # Create filename
        from urllib.parse import urlparse
        parsed_url = urlparse(base_url)
        domain = parsed_url.netloc.replace('.', '_')
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"docsynapse_{domain}_{timestamp}.md"

        # Ensure output directory exists
        output_dir = Path(settings.OUTPUT_DIR)
        output_dir.mkdir(exist_ok=True)

        filepath = output_dir / filename

        # Save file asynchronously
        async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
            await f.write(content)

        logger.info(f"Generated markdown file: {filepath}")
        return str(filepath)

    def get_processed_file(self, job_id: str) -> Optional[str]:
        """Get the path to a processed file by job ID."""
        return self.processed_files.get(job_id)
