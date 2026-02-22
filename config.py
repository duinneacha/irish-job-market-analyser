# config.py — Central configuration for the Irish Job Market Analyser

# ── Job board URLs ────────────────────────────────────────────────────────────

JOBS_IE_BASE = "https://www.jobs.ie"
JOBS_IE_SEARCH = "https://www.jobs.ie/jobs/it/"

IRISHJOBS_BASE = "https://www.irishjobs.ie"
IRISHJOBS_SEARCH = "https://www.irishjobs.ie/ShowResults.aspx"
IRISHJOBS_PARAMS = {
    "Keywords": "",
    "Location": "101",   # Ireland
    "Category": "37",    # IT
    "Recruiter": "Company",
    "SortType": "date",
}

# ── Request headers (polite scraping) ─────────────────────────────────────────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-IE,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Polite delay between requests (seconds)
REQUEST_DELAY = 2

# ── Database ───────────────────────────────────────────────────────────────────
DB_PATH = "data/jobs.db"

# ── Tech skills to extract from job descriptions ──────────────────────────────
# Organised by category for cleaner analysis
SKILLS = {
    "Languages": [
        "Python", "JavaScript", "TypeScript", "Java", "C#", "C\\+\\+", "Go",
        "Rust", "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R", "MATLAB",
    ],
    "Frontend": [
        "React", "Vue", "Angular", "Svelte", "Next\\.js", "Nuxt", "HTML",
        "CSS", "Tailwind", "Bootstrap", "jQuery", "Webpack", "Vite",
    ],
    "Backend": [
        "Node\\.js", "Django", "Flask", "FastAPI", "Spring", "Laravel",
        "Express", "Rails", "ASP\\.NET", "\\.NET", "GraphQL", "REST API",
    ],
    "Data & ML": [
        "Pandas", "NumPy", "Scikit-learn", "TensorFlow", "PyTorch", "Keras",
        "Spark", "Hadoop", "Kafka", "Airflow", "dbt", "Power BI", "Tableau",
        "Looker", "Machine Learning", "Deep Learning", "NLP", "LLM",
    ],
    "Cloud & DevOps": [
        "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform", "Ansible",
        "Jenkins", "GitHub Actions", "CI/CD", "Linux", "Bash",
    ],
    "Databases": [
        "SQL", "PostgreSQL", "MySQL", "SQLite", "MongoDB", "Redis", "Elasticsearch",
        "DynamoDB", "Snowflake", "BigQuery", "Oracle", "Supabase",
    ],
    "Other": [
        "Git", "Agile", "Scrum", "Jira", "Figma", "Microservices",
        "API", "Cybersecurity", "Salesforce", "SAP",
    ],
}

# Flat list for quick lookup
ALL_SKILLS = [skill for group in SKILLS.values() for skill in group]

# ── Irish cities / regions for location parsing ───────────────────────────────
IRISH_LOCATIONS = {
    "Cork": ["Cork", "Carrigaline", "Ballincollig", "Midleton", "Cobh"],
    "Dublin": ["Dublin", "Swords", "Tallaght", "Dundrum", "Dún Laoghaire"],
    "Limerick": ["Limerick"],
    "Galway": ["Galway"],
    "Waterford": ["Waterford"],
    "Remote": ["Remote", "Work from Home", "WFH", "Hybrid"],
}
