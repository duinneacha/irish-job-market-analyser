"""
database/db.py — SQLite connection and CRUD helpers
"""

import sqlite3
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
import sys

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DB_PATH

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_connection() -> sqlite3.Connection:
    """Return a connection with row_factory set for dict-style access."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")   # Better concurrency
    return conn


def init_db() -> None:
    """Create tables if they don't exist."""
    with get_connection() as conn:
        schema = SCHEMA_PATH.read_text()
        conn.executescript(schema)
    print(f"[DB] Initialised at {DB_PATH}")


def insert_job(job: dict) -> Optional[int]:
    """
    Insert a job record. Returns the new row ID, or None if duplicate.

    Expected keys: source, external_id, title, company, location_raw,
    location_norm, salary_raw, salary_min, salary_max, description,
    url, posted_date
    """
    sql = """
        INSERT OR IGNORE INTO jobs
            (source, external_id, title, company, location_raw, location_norm,
             salary_raw, salary_min, salary_max, description, url,
             posted_date, scraped_at)
        VALUES
            (:source, :external_id, :title, :company, :location_raw, :location_norm,
             :salary_raw, :salary_min, :salary_max, :description, :url,
             :posted_date, :scraped_at)
    """
    job.setdefault("scraped_at", datetime.now(timezone.utc).isoformat())
    with get_connection() as conn:
        cur = conn.execute(sql, job)
        return cur.lastrowid if cur.rowcount > 0 else None


def insert_skills(job_id: int, skills: list[dict]) -> None:
    """
    Insert extracted skills for a job.
    Each item: {"skill": str, "category": str}
    """
    sql = """
        INSERT OR IGNORE INTO job_skills (job_id, skill, category)
        VALUES (?, ?, ?)
    """
    with get_connection() as conn:
        conn.executemany(sql, [(job_id, s["skill"], s["category"]) for s in skills])


def log_scrape_run(source: str, found: int, added: int, dupes: int, errors: int, notes: str = "") -> None:
    sql = """
        INSERT INTO scrape_log (run_at, source, jobs_found, jobs_added, jobs_duplicate, errors, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    with get_connection() as conn:
        conn.execute(sql, (datetime.now(timezone.utc).isoformat(), source, found, added, dupes, errors, notes))


# ── Query helpers used by the Streamlit dashboard ─────────────────────────────

def query_df(sql: str, params: tuple = ()) -> "pd.DataFrame":
    """Run a SQL query and return a pandas DataFrame."""
    import pandas as pd
    with get_connection() as conn:
        return pd.read_sql_query(sql, conn, params=params)


def total_jobs() -> int:
    with get_connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]


def jobs_last_n_days(n: int = 7) -> int:
    sql = "SELECT COUNT(*) FROM jobs WHERE posted_date >= date('now', ?)"
    with get_connection() as conn:
        return conn.execute(sql, (f"-{n} days",)).fetchone()[0]


def top_skills(limit: int = 20, location: str = None, days: int = None) -> "pd.DataFrame":
    """Return top skills with count, optionally filtered by location/recency."""
    import pandas as pd
    where_clauses = []
    params = []

    if location and location != "All Ireland":
        where_clauses.append("j.location_norm = ?")
        params.append(location)
    if days:
        where_clauses.append("j.posted_date >= date('now', ?)")
        params.append(f"-{days} days")

    where = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    sql = f"""
        SELECT js.skill, js.category, COUNT(*) as count
        FROM job_skills js
        JOIN jobs j ON j.id = js.job_id
        {where}
        GROUP BY js.skill
        ORDER BY count DESC
        LIMIT ?
    """
    params.append(limit)
    with get_connection() as conn:
        return pd.read_sql_query(sql, conn, params=params)


def jobs_by_location() -> "pd.DataFrame":
    sql = """
        SELECT location_norm, COUNT(*) as count
        FROM jobs
        WHERE location_norm IS NOT NULL
        GROUP BY location_norm
        ORDER BY count DESC
    """
    return query_df(sql)


def jobs_over_time(days: int = 90) -> "pd.DataFrame":
    sql = """
        SELECT posted_date as date, COUNT(*) as count
        FROM jobs
        WHERE posted_date >= date('now', ?)
        GROUP BY posted_date
        ORDER BY posted_date ASC
    """
    return query_df(sql, (f"-{days} days",))


def top_companies(limit: int = 15, location: str = None) -> "pd.DataFrame":
    where = ""
    params = []
    if location and location != "All Ireland":
        where = "WHERE location_norm = ?"
        params.append(location)
    sql = f"""
        SELECT company, COUNT(*) as job_count
        FROM jobs
        {where}
        WHERE company IS NOT NULL {"AND" if where else "WHERE"} company != ''
        GROUP BY company
        ORDER BY job_count DESC
        LIMIT ?
    """
    # Simplified version without the double WHERE issue
    if location and location != "All Ireland":
        sql = f"""
            SELECT company, COUNT(*) as job_count
            FROM jobs
            WHERE location_norm = ? AND company IS NOT NULL AND company != ''
            GROUP BY company
            ORDER BY job_count DESC
            LIMIT ?
        """
        params.append(limit)
    else:
        sql = f"""
            SELECT company, COUNT(*) as job_count
            FROM jobs
            WHERE company IS NOT NULL AND company != ''
            GROUP BY company
            ORDER BY job_count DESC
            LIMIT ?
        """
        params = [limit]
    return query_df(sql, tuple(params))


def salary_distribution() -> "pd.DataFrame":
    sql = """
        SELECT salary_min, salary_max, location_norm, title
        FROM jobs
        WHERE salary_min IS NOT NULL AND salary_min > 0
        ORDER BY salary_min DESC
    """
    return query_df(sql)


def skills_by_category() -> "pd.DataFrame":
    sql = """
        SELECT js.category, js.skill, COUNT(*) as count
        FROM job_skills js
        GROUP BY js.category, js.skill
        ORDER BY js.category, count DESC
    """
    return query_df(sql)
