"""
InsightInMinutes - Universal Web Scraper
Extracts readable prose from international news websites, strips boilerplate,
and provides custom selector overrides.
"""

import re
from typing import Tuple, Optional
import requests
from bs4 import BeautifulSoup
from config import SCRAPER_TARGET_PATTERNS

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9,bn;q=0.8",
}


def extract_universal_content(
    url: str, custom_class: Optional[str] = None
) -> Tuple[Optional[str], Optional[str]]:
    """
    Crawls a news article URL and extracts its main prose body.

    Returns:
        (extracted_text, None) on success, or (None, error_message) on failure.
    """
    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=14)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # 1. Custom CSS selector override if provided
        if custom_class and custom_class.strip():
            target = custom_class.strip()
            paragraphs = [
                p.get_text(strip=True)
                for div in soup.find_all(class_=target)
                for p in div.find_all("p")
            ]
            if paragraphs:
                return "\n\n".join(paragraphs), None

        # 2. Known outlet patterns via regex map
        for pattern, classes in SCRAPER_TARGET_PATTERNS.items():
            if re.search(pattern, url, re.IGNORECASE):
                paragraphs = []
                for cls in classes:
                    for div in soup.find_all(class_=cls):
                        paragraphs.extend(
                            [p.get_text(strip=True) for p in div.find_all("p")]
                        )
                if paragraphs:
                    return "\n\n".join(paragraphs), None

        # 3. Universal heuristic extraction: decompose DOM noise
        for unwanted in soup(
            ["nav", "footer", "header", "script", "style", "aside", "form", "iframe"]
        ):
            unwanted.decompose()

        paragraphs = [
            p.get_text(strip=True)
            for p in soup.find_all("p")
            if len(p.get_text(strip=True).split()) > 7
        ]
        combined = "\n\n".join(paragraphs)

        # Fallback to separator-based text if paragraph extraction is too sparse
        if len(combined.split()) < 35:
            combined = soup.get_text(separator="\n", strip=True)

        if len(combined.split()) < 20:
            return (
                None,
                "Unable to extract sufficient article text from this page. "
                "Please copy and paste the text directly into the Text Summarizer.",
            )

        return combined, None

    except requests.exceptions.RequestException as e:
        return None, f"Network/HTTP error fetching article: {str(e)}"
    except Exception as e:
        return None, f"Scraping extraction error: {str(e)}"
