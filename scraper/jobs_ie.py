"""
scraper/jobs_ie.py — Scraper for Jobs.ie IT listings
"""

from bs4 import BeautifulSoup
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scraper.base import BaseScraper
from config import JOBS_IE_SEARCH, JOBS_IE_BASE


class JobsIeScraper(BaseScraper):

    SOURCE_NAME = "jobs_ie"

    def scrape_all(self, max_pages: int = 10) -> list[dict]:
        jobs = []
        for page in range(1, max_pages + 1):
            print(f"[jobs.ie] Scraping page {page}...")
            page_jobs = self._scrape_page(page)
            if not page_jobs:
                print(f"[jobs.ie] No jobs on page {page}, stopping.")
                break
            jobs.extend(page_jobs)
            self._jobs_found += len(page_jobs)

        print(f"[jobs.ie] Total scraped: {len(jobs)}")
        return jobs

    def _scrape_page(self, page: int) -> list[dict]:
        params = {"page": page} if page > 1 else {}
        resp = self.get(JOBS_IE_SEARCH, params=params)
        if not resp:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        job_cards = soup.select('article[data-testid="job-item"]')

        if not job_cards:
            return []

        results = []
        for card in job_cards:
            job = self._parse_card(card)
            if job:
                results.append(job)
        return results

    def _parse_card(self, card) -> dict | None:
        try:
            # Title
            title_el = card.select_one('[data-at="job-item-title"]')
            if not title_el:
                return None
            title = self.clean_text(title_el.get_text())
            if not title:
                return None

            # URL
            link = card.select_one('a[href*="/job/"]')
            href = link["href"] if link and link.get("href") else ""
            url = href if href.startswith("http") else f"{JOBS_IE_BASE}{href}"

            # Company
            company_el = card.select_one('[data-at="job-item-company-name"]')
            company = self.clean_text(company_el.get_text()) if company_el else ""

            # Location
            location_el = card.select_one('[data-at="job-item-location"]')
            location_raw = self.clean_text(location_el.get_text()) if location_el else ""
            location_norm = self.normalise_location(location_raw)

            # Salary
            salary_el = card.select_one('[data-at="job-item-salary-info"]')
            salary_raw = self.clean_text(salary_el.get_text()) if salary_el else ""
            salary_min, salary_max = self.parse_salary(salary_raw)

            # Description snippet
            desc_el = card.select_one('[data-at="jobcard-content"]')
            description = self.clean_text(desc_el.get_text()) if desc_el else ""

            return {
                "source": self.SOURCE_NAME,
                "external_id": self.make_external_id(url),
                "title": title,
                "company": company,
                "location_raw": location_raw,
                "location_norm": location_norm,
                "salary_raw": salary_raw,
                "salary_min": salary_min,
                "salary_max": salary_max,
                "description": description,
                "url": url,
                "posted_date": self.today_iso(),
            }
        except Exception as e:
            print(f"[jobs.ie] Parse error: {e}")
            self._errors += 1
            return None
