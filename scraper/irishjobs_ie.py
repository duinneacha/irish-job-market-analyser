"""
scraper/irishjobs_ie.py — Scraper for IrishJobs.ie IT listings
"""

from bs4 import BeautifulSoup
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scraper.base import BaseScraper
from config import IRISHJOBS_BASE, IRISHJOBS_SEARCH, IRISHJOBS_PARAMS


class IrishJobsScraper(BaseScraper):

    SOURCE_NAME = "irishjobs_ie"

    def scrape_all(self, max_pages: int = 10) -> list[dict]:
        jobs = []
        for page in range(1, max_pages + 1):
            print(f"[irishjobs.ie] Scraping page {page}...")
            page_jobs = self._scrape_page(page)
            if not page_jobs:
                print(f"[irishjobs.ie] No jobs on page {page}, stopping.")
                break
            jobs.extend(page_jobs)
            self._jobs_found += len(page_jobs)

        print(f"[irishjobs.ie] Total scraped: {len(jobs)}")
        return jobs

    def _scrape_page(self, page: int) -> list[dict]:
        params = {**IRISHJOBS_PARAMS, "Page": page}
        resp = self.get(IRISHJOBS_SEARCH, params=params)
        if not resp:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")

        # IrishJobs uses a table-style layout
        job_rows = soup.select("tr.searchResultHeader, div.job_header, .job-result-card")

        if not job_rows:
            # Broader fallback
            job_rows = soup.select(".job-item, article.job, .resultRow")

        if not job_rows:
            return []

        results = []
        for row in job_rows:
            job = self._parse_row(row)
            if job:
                results.append(job)
        return results

    def _parse_row(self, row) -> dict | None:
        try:
            # Title
            title_el = row.select_one(
                "a.jobTitle, h3 a, .job-title a, td.jobTitle a, a[id*='JobTitle']"
            )
            if not title_el:
                return None
            title = self.clean_text(title_el.get_text())
            if not title or len(title) < 3:
                return None

            # URL
            href = title_el.get("href", "")
            url = href if href.startswith("http") else f"{IRISHJOBS_BASE}{href}"

            # Company
            company_el = row.select_one(
                ".company, td.company, span.company, a[id*='Company'], .job-company"
            )
            company = self.clean_text(company_el.get_text()) if company_el else ""

            # Location
            location_el = row.select_one(
                ".location, td.location, span.location, [id*='Location'], .job-location"
            )
            location_raw = self.clean_text(location_el.get_text()) if location_el else ""
            location_norm = self.normalise_location(location_raw)

            # Salary
            salary_el = row.select_one(
                ".salary, td.salary, span.salary, [id*='Salary'], .job-salary"
            )
            salary_raw = self.clean_text(salary_el.get_text()) if salary_el else ""
            salary_min, salary_max = self.parse_salary(salary_raw)

            # Description
            desc_el = row.select_one(".description, .job-description, p.description, .snippet")
            description = self.clean_text(desc_el.get_text()) if desc_el else ""

            # Date posted
            date_el = row.select_one(".date, .posted, [id*='Date'], td.date")
            posted_date = self.clean_text(date_el.get_text()) if date_el else self.today_iso()
            # Normalise to ISO if it looks like a relative date ("Today", "Yesterday")
            posted_date = self._normalise_date(posted_date)

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
                "posted_date": posted_date,
            }
        except Exception as e:
            print(f"[irishjobs.ie] Parse error: {e}")
            self._errors += 1
            return None

    def _normalise_date(self, raw: str) -> str:
        """Convert relative date strings to ISO date."""
        from datetime import datetime, timedelta, timezone
        today = datetime.now(timezone.utc).date()
        raw_lower = raw.lower().strip()
        if "today" in raw_lower:
            return today.isoformat()
        if "yesterday" in raw_lower:
            return (today - timedelta(days=1)).isoformat()
        # Try to parse actual dates
        for fmt in ["%d/%m/%Y", "%d %b %Y", "%Y-%m-%d", "%d-%m-%Y"]:
            try:
                return datetime.strptime(raw.strip(), fmt).date().isoformat()
            except ValueError:
                continue
        return today.isoformat()
