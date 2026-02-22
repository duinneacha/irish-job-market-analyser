"""
run_scraper.py — Orchestrator: run all scrapers, extract skills, log results.

Usage:
    python run_scraper.py                    # Run all scrapers
    python run_scraper.py --source jobs_ie   # Run single scraper
    python run_scraper.py --dry-run          # Print jobs without saving
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))

from database.db import init_db, insert_job, log_scrape_run
from analysis.skills import extract_and_store
from scraper.jobs_ie import JobsIeScraper
from scraper.irishjobs_ie import IrishJobsScraper


def run_scraper(scraper, max_pages: int = 10, dry_run: bool = False) -> dict:
    """Run a single scraper and persist results."""
    source = scraper.SOURCE_NAME
    print(f"\n{'='*50}")
    print(f"[{source}] Starting scrape at {datetime.now(timezone.utc).isoformat()}")
    print(f"{'='*50}")

    jobs = scraper.scrape_all(max_pages=max_pages)

    added = 0
    dupes = 0

    for job in jobs:
        if dry_run:
            print(f"  DRY RUN | {job['title'][:60]} | {job['company']} | {job['location_norm']}")
            continue

        job_id = insert_job(job)

        if job_id:
            # Extract and store skills for newly inserted jobs
            skill_count = extract_and_store(
                job_id,
                description=job.get("description", ""),
                title=job.get("title", ""),
            )
            print(f"  + [{job_id}] {job['title'][:50]} | {job['company']} | {job['location_norm']} | {skill_count} skills")
            added += 1
        else:
            dupes += 1

    stats = scraper.stats
    stats["added"] = added
    stats["duplicate"] = dupes

    if not dry_run:
        log_scrape_run(
            source=source,
            found=stats["found"],
            added=added,
            dupes=dupes,
            errors=stats["errors"],
        )

    print(f"\n[{source}] Done — found: {stats['found']}, added: {added}, dupes: {dupes}, errors: {stats['errors']}")
    return stats


def run_all(max_pages: int = 10, dry_run: bool = False) -> dict:
    """Run all scrapers and return aggregated stats."""
    init_db()

    scrapers = [
        JobsIeScraper(),
        IrishJobsScraper(),
    ]

    total = {"found": 0, "added": 0, "duplicate": 0, "errors": 0}

    for scraper in scrapers:
        try:
            stats = run_scraper(scraper, max_pages=max_pages, dry_run=dry_run)
            for key in total:
                total[key] += stats.get(key, 0)
        except Exception as e:
            print(f"[ERROR] {scraper.SOURCE_NAME} failed: {e}")
            total["errors"] += 1

    print(f"\n{'='*50}")
    print(f"ALL SCRAPERS COMPLETE")
    print(f"  Total found:     {total['found']}")
    print(f"  Total added:     {total['added']}")
    print(f"  Total dupes:     {total['duplicate']}")
    print(f"  Total errors:    {total['errors']}")
    print(f"{'='*50}\n")

    return total


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Irish Job Market Scraper")
    parser.add_argument("--source", choices=["jobs_ie", "irishjobs_ie", "all"], default="all")
    parser.add_argument("--max-pages", type=int, default=10)
    parser.add_argument("--dry-run", action="store_true", help="Print jobs without saving")
    args = parser.parse_args()

    init_db()

    if args.source == "all":
        run_all(max_pages=args.max_pages, dry_run=args.dry_run)
    elif args.source == "jobs_ie":
        run_scraper(JobsIeScraper(), max_pages=args.max_pages, dry_run=args.dry_run)
    elif args.source == "irishjobs_ie":
        run_scraper(IrishJobsScraper(), max_pages=args.max_pages, dry_run=args.dry_run)
