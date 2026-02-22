-- Irish Job Market Analyser — Database Schema

-- Core jobs table
CREATE TABLE IF NOT EXISTS jobs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source          TEXT NOT NULL,          -- 'jobs_ie' | 'irishjobs_ie'
    external_id     TEXT,                   -- ID from source site (for dedup)
    title           TEXT NOT NULL,
    company         TEXT,
    location_raw    TEXT,                   -- As scraped
    location_norm   TEXT,                   -- Normalised: Cork | Dublin | Remote | etc.
    salary_raw      TEXT,                   -- As scraped (e.g. "€60,000 - €75,000")
    salary_min      INTEGER,                -- Parsed lower bound
    salary_max      INTEGER,                -- Parsed upper bound
    description     TEXT,
    url             TEXT,
    posted_date     TEXT,                   -- ISO date string
    scraped_at      TEXT NOT NULL,          -- ISO datetime
    UNIQUE(source, external_id)
);

-- Extracted skills per job (normalised many-to-many)
CREATE TABLE IF NOT EXISTS job_skills (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id      INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    skill       TEXT NOT NULL,
    category    TEXT NOT NULL,
    UNIQUE(job_id, skill)
);

-- Scrape run log (useful for debugging and audit trail)
CREATE TABLE IF NOT EXISTS scrape_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    run_at          TEXT NOT NULL,
    source          TEXT NOT NULL,
    jobs_found      INTEGER DEFAULT 0,
    jobs_added      INTEGER DEFAULT 0,
    jobs_duplicate  INTEGER DEFAULT 0,
    errors          INTEGER DEFAULT 0,
    notes           TEXT
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_jobs_location   ON jobs(location_norm);
CREATE INDEX IF NOT EXISTS idx_jobs_posted     ON jobs(posted_date);
CREATE INDEX IF NOT EXISTS idx_jobs_source     ON jobs(source);
CREATE INDEX IF NOT EXISTS idx_job_skills_skill ON job_skills(skill);
CREATE INDEX IF NOT EXISTS idx_job_skills_job   ON job_skills(job_id);
