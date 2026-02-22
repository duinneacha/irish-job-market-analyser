"""
Irish Tech Job Market Analyser
================================
A Streamlit dashboard visualising live job posting data from Irish job boards.

Run:  streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timezone
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from database.db import (
    init_db,
    total_jobs,
    jobs_last_n_days,
    top_skills,
    jobs_by_location,
    jobs_over_time,
    top_companies,
    salary_distribution,
    skills_by_category,
    query_df,
)
from analysis.stats import enrich_with_role_category, salary_stats

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Irish Tech Job Market Analyser",
    page_icon="🇮🇪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .metric-card {
        background: #1e2230;
        border: 1px solid #2d3347;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
    }
    .metric-value {
        font-size: 2.4rem;
        font-weight: 700;
        color: #3b82f6;
        line-height: 1;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #94a3b8;
        margin-top: 6px;
    }
    .section-header {
        font-size: 1.3rem;
        font-weight: 600;
        color: #e2e8f0;
        margin: 28px 0 12px 0;
        padding-bottom: 8px;
        border-bottom: 1px solid #2d3347;
    }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Initialise DB on first run ─────────────────────────────────────────────────
init_db()


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://flagcdn.com/w80/ie.png", width=40)
    st.title("🇮🇪 Irish Tech Jobs")
    st.caption("Live data from Irish job boards")

    st.divider()

    # Location filter
    location_options = ["All Ireland", "Cork", "Dublin", "Limerick", "Galway", "Remote"]
    selected_location = st.selectbox("📍 Location", location_options)

    # Time window
    time_window = st.selectbox(
        "📅 Time window",
        [7, 14, 30, 60, 90],
        index=2,
        format_func=lambda x: f"Last {x} days",
    )

    # Skill category filter
    skill_cats = ["All Categories", "Languages", "Frontend", "Backend", "Data & ML", "Cloud & DevOps", "Databases", "Other"]
    selected_category = st.selectbox("🔧 Skill category", skill_cats)

    st.divider()

    # Manual scrape trigger
    st.markdown("**🔄 Data Collection**")
    if st.button("Run Scraper Now", use_container_width=True, type="primary"):
        with st.spinner("Scraping job boards — this may take a minute..."):
            try:
                from run_scraper import run_all
                stats = run_all()
                st.success(f"Done! Added {stats['added']} new jobs.")
            except Exception as e:
                st.error(f"Scraper error: {e}")

    st.caption("Auto-runs nightly via GitHub Actions")

    st.divider()
    st.caption(f"Built by [Aidan Dennehy](https://www.aidandennehy.ie)  \nData: jobs.ie · irishjobs.ie")


# ── Main content ───────────────────────────────────────────────────────────────
st.markdown("## 🇮🇪 Irish Tech Job Market Analyser")
st.caption(f"Last refreshed: {datetime.now(timezone.utc).strftime('%d %b %Y, %H:%M UTC')}")

# ── KPI row ────────────────────────────────────────────────────────────────────
total = total_jobs()
recent_7 = jobs_last_n_days(7)
recent_30 = jobs_last_n_days(30)

# Count unique companies
try:
    companies_count = query_df("SELECT COUNT(DISTINCT company) as n FROM jobs WHERE company != ''").iloc[0]["n"]
except Exception:
    companies_count = 0

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-value">{total:,}</div>
        <div class="metric-label">Total Jobs Indexed</div>
    </div>""", unsafe_allow_html=True)

with col2:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-value">{recent_7:,}</div>
        <div class="metric-label">Added Last 7 Days</div>
    </div>""", unsafe_allow_html=True)

with col3:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-value">{recent_30:,}</div>
        <div class="metric-label">Added Last 30 Days</div>
    </div>""", unsafe_allow_html=True)

with col4:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-value">{companies_count:,}</div>
        <div class="metric-label">Unique Employers</div>
    </div>""", unsafe_allow_html=True)

# ── Check for data ─────────────────────────────────────────────────────────────
if total == 0:
    st.info(
        "📭 No data yet. Click **Run Scraper Now** in the sidebar to collect your first batch of jobs, "
        "or push to GitHub to trigger the nightly Action.",
        icon="ℹ️",
    )
    st.stop()

# ── Row 1: Top skills + Jobs by location ──────────────────────────────────────
st.markdown('<div class="section-header">🔧 Most In-Demand Skills</div>', unsafe_allow_html=True)

col_skills, col_location = st.columns([3, 2])

with col_skills:
    loc_filter = selected_location if selected_location != "All Ireland" else None
    df_skills = top_skills(limit=20, location=loc_filter, days=time_window)

    if not df_skills.empty:
        # Optionally filter by category
        if selected_category != "All Categories":
            df_skills = df_skills[df_skills["category"] == selected_category]

        if not df_skills.empty:
            fig = px.bar(
                df_skills,
                x="count",
                y="skill",
                orientation="h",
                color="category",
                color_discrete_sequence=px.colors.qualitative.Set2,
                labels={"count": "Job Postings", "skill": "Skill"},
                title=f"Top Skills — {selected_location} · Last {time_window} days",
            )
            fig.update_layout(
                yaxis={"categoryorder": "total ascending"},
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#e2e8f0",
                legend_title="Category",
                height=500,
                margin=dict(l=0, r=0, t=40, b=0),
            )
            fig.update_xaxes(gridcolor="#2d3347")
            fig.update_yaxes(gridcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No skills data for this filter combination.")
    else:
        st.info("No skills data available yet.")

with col_location:
    df_loc = jobs_by_location()
    if not df_loc.empty:
        fig2 = px.pie(
            df_loc,
            values="count",
            names="location_norm",
            title="Jobs by Location",
            color_discrete_sequence=px.colors.qualitative.Set2,
            hole=0.45,
        )
        fig2.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#e2e8f0",
            height=500,
            margin=dict(l=0, r=0, t=40, b=0),
            legend=dict(orientation="v", x=1, y=0.5),
        )
        st.plotly_chart(fig2, use_container_width=True)

# ── Row 2: Jobs over time ──────────────────────────────────────────────────────
st.markdown('<div class="section-header">📈 Job Posting Volume Over Time</div>', unsafe_allow_html=True)

df_time = jobs_over_time(days=time_window)
if not df_time.empty:
    df_time["date"] = pd.to_datetime(df_time["date"])
    # 7-day rolling average
    df_time["rolling_avg"] = df_time["count"].rolling(7, min_periods=1).mean()

    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        x=df_time["date"],
        y=df_time["count"],
        name="Daily posts",
        marker_color="#3b82f6",
        opacity=0.5,
    ))
    fig3.add_trace(go.Scatter(
        x=df_time["date"],
        y=df_time["rolling_avg"],
        name="7-day rolling avg",
        line=dict(color="#f59e0b", width=2),
        mode="lines",
    ))
    fig3.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#e2e8f0",
        xaxis_title="Date",
        yaxis_title="New Job Postings",
        height=320,
        margin=dict(l=0, r=0, t=20, b=0),
        legend=dict(orientation="h", y=1.1),
    )
    fig3.update_xaxes(gridcolor="#2d3347")
    fig3.update_yaxes(gridcolor="#2d3347")
    st.plotly_chart(fig3, use_container_width=True)

# ── Row 3: Top companies + Skills by category ─────────────────────────────────
col_co, col_cat = st.columns(2)

with col_co:
    st.markdown('<div class="section-header">🏢 Top Hiring Companies</div>', unsafe_allow_html=True)
    loc_filter = selected_location if selected_location != "All Ireland" else None
    df_co = top_companies(limit=15, location=loc_filter)
    if not df_co.empty:
        fig4 = px.bar(
            df_co,
            x="job_count",
            y="company",
            orientation="h",
            color="job_count",
            color_continuous_scale="Blues",
            labels={"job_count": "Open Roles", "company": ""},
        )
        fig4.update_layout(
            yaxis={"categoryorder": "total ascending"},
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#e2e8f0",
            coloraxis_showscale=False,
            height=420,
            margin=dict(l=0, r=0, t=10, b=0),
        )
        fig4.update_xaxes(gridcolor="#2d3347")
        st.plotly_chart(fig4, use_container_width=True)

with col_cat:
    st.markdown('<div class="section-header">🗂 Skills by Category</div>', unsafe_allow_html=True)
    df_cat = skills_by_category()
    if not df_cat.empty:
        cat_totals = df_cat.groupby("category")["count"].sum().reset_index()
        fig5 = px.bar(
            cat_totals,
            x="count",
            y="category",
            orientation="h",
            color="category",
            color_discrete_sequence=px.colors.qualitative.Set2,
            labels={"count": "Skill Mentions", "category": ""},
        )
        fig5.update_layout(
            yaxis={"categoryorder": "total ascending"},
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#e2e8f0",
            showlegend=False,
            height=420,
            margin=dict(l=0, r=0, t=10, b=0),
        )
        fig5.update_xaxes(gridcolor="#2d3347")
        st.plotly_chart(fig5, use_container_width=True)

# ── Row 4: Salary distribution ────────────────────────────────────────────────
st.markdown('<div class="section-header">💶 Salary Distribution (where advertised)</div>', unsafe_allow_html=True)

df_sal = salary_distribution()
if not df_sal.empty and len(df_sal) >= 5:
    stats = salary_stats(df_sal)
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Median Salary", f"€{stats.get('median', 0):,}")
    s2.metric("Average Salary", f"€{stats.get('mean', 0):,}")
    s3.metric("25th Percentile", f"€{stats.get('p25', 0):,}")
    s4.metric("75th Percentile", f"€{stats.get('p75', 0):,}")

    fig6 = px.histogram(
        df_sal,
        x="salary_min",
        nbins=30,
        color="location_norm",
        barmode="overlay",
        opacity=0.75,
        color_discrete_sequence=px.colors.qualitative.Set2,
        labels={"salary_min": "Salary (€)", "location_norm": "Location"},
        title=f"Salary Distribution — {stats.get('count', 0)} roles with salary data",
    )
    fig6.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#e2e8f0",
        height=320,
        margin=dict(l=0, r=0, t=40, b=0),
    )
    fig6.update_xaxes(gridcolor="#2d3347", tickprefix="€", tickformat=",")
    fig6.update_yaxes(gridcolor="#2d3347")
    st.plotly_chart(fig6, use_container_width=True)
else:
    st.info("Not enough salary data yet — this will improve as more jobs are collected.")

# ── Row 5: Role type breakdown ────────────────────────────────────────────────
st.markdown('<div class="section-header">👤 Jobs by Role Type</div>', unsafe_allow_html=True)

try:
    df_jobs_all = query_df("SELECT title, location_norm, company, url, posted_date FROM jobs ORDER BY scraped_at DESC LIMIT 2000")
    if not df_jobs_all.empty:
        df_jobs_all = enrich_with_role_category(df_jobs_all)
        role_counts = df_jobs_all["role_category"].value_counts().reset_index()
        role_counts.columns = ["role_category", "count"]

        fig7 = px.bar(
            role_counts,
            x="role_category",
            y="count",
            color="role_category",
            color_discrete_sequence=px.colors.qualitative.Set2,
            labels={"role_category": "Role Type", "count": "Job Count"},
        )
        fig7.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#e2e8f0",
            showlegend=False,
            height=320,
            margin=dict(l=0, r=0, t=10, b=0),
        )
        fig7.update_xaxes(tickangle=-20, gridcolor="rgba(0,0,0,0)")
        fig7.update_yaxes(gridcolor="#2d3347")
        st.plotly_chart(fig7, use_container_width=True)
except Exception as e:
    st.warning(f"Role breakdown unavailable: {e}")

# ── Row 6: Recent jobs table ───────────────────────────────────────────────────
st.markdown('<div class="section-header">📋 Recently Added Jobs</div>', unsafe_allow_html=True)

try:
    df_recent = query_df("""
        SELECT title, company, location_norm as location, salary_raw as salary,
               posted_date, source, url
        FROM jobs
        ORDER BY scraped_at DESC
        LIMIT 50
    """)

    if not df_recent.empty:
        # Make title a clickable link
        df_recent["title"] = df_recent.apply(
            lambda r: f"[{r['title']}]({r['url']})" if r["url"] else r["title"],
            axis=1,
        )
        df_recent = df_recent.drop(columns=["url"])
        st.dataframe(
            df_recent,
            use_container_width=True,
            hide_index=True,
            column_config={
                "title": st.column_config.LinkColumn("Job Title"),
                "salary": st.column_config.TextColumn("Salary"),
            },
        )
except Exception as e:
    st.warning(f"Could not load recent jobs: {e}")

# ── Footer ─────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "Data sourced from Jobs.ie and IrishJobs.ie · Built by [Aidan Dennehy](https://www.aidandennehy.ie) "
    "as part of an Irish open data portfolio · "
    "[View on GitHub](https://github.com/duinneacha)"
)
