# 🇮🇪 Irish Tech Job Market Analyser

A live dashboard tracking tech job postings from Irish job boards — built to demonstrate
full-stack data engineering skills: automated scraping, structured storage, NLP-style
skill extraction, and interactive visualisation.

**Live app:** [irish-job-market.streamlit.app](https://irish-job-market.streamlit.app) *(deploy URL — update once live)*
**Portfolio:** [aidandennehy.ie](https://www.aidandennehy.ie)

---

## What it does

- Scrapes IT job listings daily from **Jobs.ie** and **IrishJobs.ie**
- Extracts 70+ tech skills from job descriptions using regex pattern matching
- Stores everything in a **SQLite database** with a clean normalised schema
- Runs automatically every night via a **GitHub Actions** workflow
- Visualises insights in a **Streamlit dashboard**: top skills, hiring companies,
  salary ranges, posting trends, role type breakdown, and Cork vs Dublin splits

## Tech stack

| Layer | Technology |
|-------|-----------|
| Scraping | Python · Requests · BeautifulSoup4 |
| Storage | SQLite (WAL mode) |
| Analysis | Pandas · NumPy |
| Dashboard | Streamlit · Plotly |
| Automation | GitHub Actions |

## Project structure

```
irish-job-market-analyser/
├── app.py                  # Streamlit dashboard
├── run_scraper.py          # Scraper orchestrator
├── config.py               # Skills list, URLs, settings
├── requirements.txt
├── scraper/
│   ├── base.py             # Shared HTTP + parsing utilities
│   ├── jobs_ie.py          # Jobs.ie scraper
│   └── irishjobs_ie.py     # IrishJobs.ie scraper
├── database/
│   ├── schema.sql          # Table definitions
│   └── db.py               # CRUD helpers + dashboard queries
├── analysis/
│   ├── skills.py           # Skill extraction
│   └── stats.py            # Salary stats, trending skills, role categorisation
├── data/
│   └── jobs.db             # SQLite database (auto-created)
└── .github/workflows/
    └── scrape.yml          # Nightly scrape Action
```

## Getting started

```bash
# 1. Clone and install
git clone https://github.com/duinneacha/irish-job-market-analyser
cd irish-job-market-analyser
pip install -r requirements.txt

# 2. Run your first scrape
python run_scraper.py

# 3. Launch the dashboard
streamlit run app.py
```

## Deploying to Streamlit Community Cloud

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect your repo
3. Set main file path to `app.py`
4. Deploy — it's free for public repos

The nightly GitHub Action will keep data fresh automatically.

## Roadmap

- [ ] Phase 2: spaCy NLP for richer skill extraction and job description summarisation
- [ ] Phase 2: Supabase backend (PostgreSQL + PostGIS) to replace SQLite
- [ ] Phase 3: Trend analysis — skills rising/falling over months
- [ ] Phase 3: Salary prediction model (regression on role/location/skills)
- [ ] Phase 3: Job alert subscriptions

---

Built by [Aidan Dennehy](https://www.aidandennehy.ie) · Cork, Ireland
