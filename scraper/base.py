"""
scraper/base.py — Base scraper class with shared HTTP and parsing utilities
"""

import time
import hashlib
import re
import requests
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import HEADERS, REQUEST_DELAY, IRISH_LOCATIONS


class BaseScraper(ABC):
    """
    Abstract base for all job board scrapers.
    Subclasses implement `scrape_page()` and `parse_job()`.
    """

    SOURCE_NAME: str = "base"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self._jobs_found = 0
        self._jobs_added = 0
        self._jobs_duplicate = 0
        self._errors = 0

    # ── HTTP helpers ───────────────────────────────────────────────────────────

    def get(self, url: str, params: dict = None, retries: int = 3) -> Optional[requests.Response]:
        """GET with retry and polite delay."""
        for attempt in range(retries):
            try:
                time.sleep(REQUEST_DELAY)
                resp = self.session.get(url, params=params, timeout=15)
                resp.raise_for_status()
                return resp
            except requests.RequestException as e:
                print(f"[{self.SOURCE_NAME}] Attempt {attempt + 1}/{retries} failed: {e}")
                if attempt == retries - 1:
                    self._errors += 1
                    return None
                time.sleep(REQUEST_DELAY * (attempt + 1))
        return None

    # ── Parsing utilities ──────────────────────────────────────────────────────

    @staticmethod
    def make_external_id(url: str) -> str:
        """Hash a URL to a stable short ID for deduplication."""
        return hashlib.md5(url.encode()).hexdigest()[:16]

    @staticmethod
    def normalise_location(raw: str) -> str:
        """Map a raw location string to a canonical city name."""
        if not raw:
            return "Unknown"
        raw_lower = raw.lower()
        for city, keywords in IRISH_LOCATIONS.items():
            if any(kw.lower() in raw_lower for kw in keywords):
                return city
        return "Other Ireland"

    @staticmethod
    def parse_salary(raw: str) -> tuple[Optional[int], Optional[int]]:
        """
        Extract (min, max) salary as integers from a raw string.
        Handles formats like "€45,000 - €60,000", "45k", "Up to €80,000"
        Returns (None, None) if unparseable.
        """
        if not raw:
            return None, None

        # Normalise: remove currency symbols, commas, spaces
        cleaned = raw.replace("€", "").replace(",", "").replace(" ", "")

        # Handle "k" shorthand: 60k → 60000
        cleaned = re.sub(r"(\d+)[Kk]", lambda m: str(int(m.group(1)) * 1000), cleaned)

        numbers = [int(n) for n in re.findall(r"\d{4,6}", cleaned)]

        # Filter out obviously wrong values (< 15k or > 500k)
        numbers = [n for n in numbers if 15000 <= n <= 500000]

        if len(numbers) == 0:
            return None, None
        if len(numbers) == 1:
            return numbers[0], numbers[0]
        return min(numbers), max(numbers)

    @staticmethod
    def clean_text(text: str) -> str:
        """Collapse whitespace and strip."""
        if not text:
            return ""
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def today_iso() -> str:
        return datetime.now(timezone.utc).date().isoformat()

    # ── Abstract interface ─────────────────────────────────────────────────────

    @abstractmethod
    def scrape_all(self, max_pages: int = 10) -> list[dict]:
        """
        Scrape all available pages up to max_pages.
        Returns a list of normalised job dicts.
        """
        ...

    # ── Stats ──────────────────────────────────────────────────────────────────

    @property
    def stats(self) -> dict:
        return {
            "source": self.SOURCE_NAME,
            "found": self._jobs_found,
            "added": self._jobs_added,
            "duplicate": self._jobs_duplicate,
            "errors": self._errors,
        }
