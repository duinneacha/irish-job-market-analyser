"""
analysis/stats.py — Statistical summaries used by the dashboard
"""

import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def salary_stats(df: pd.DataFrame) -> dict:
    """
    Given a DataFrame with salary_min/salary_max columns,
    return summary stats.
    """
    if df.empty or "salary_min" not in df.columns:
        return {}

    mid = df["salary_min"].dropna()
    if mid.empty:
        return {}

    return {
        "median": int(mid.median()),
        "mean": int(mid.mean()),
        "p25": int(mid.quantile(0.25)),
        "p75": int(mid.quantile(0.75)),
        "min": int(mid.min()),
        "max": int(mid.max()),
        "count": len(mid),
    }


def trending_skills(df_recent: pd.DataFrame, df_older: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """
    Compare skill frequency in recent vs older data to find trending skills.

    df_recent / df_older: DataFrames with 'skill' and 'count' columns.
    Returns a DataFrame with columns: skill, recent_pct, older_pct, delta, trend.
    """
    if df_recent.empty or df_older.empty:
        return pd.DataFrame()

    total_recent = df_recent["count"].sum()
    total_older = df_older["count"].sum()

    if total_recent == 0 or total_older == 0:
        return pd.DataFrame()

    recent = df_recent.set_index("skill")["count"] / total_recent * 100
    older = df_older.set_index("skill")["count"] / total_older * 100

    combined = pd.DataFrame({"recent_pct": recent, "older_pct": older}).fillna(0)
    combined["delta"] = combined["recent_pct"] - combined["older_pct"]
    combined["trend"] = combined["delta"].apply(
        lambda d: "↑ Rising" if d > 1 else ("↓ Falling" if d < -1 else "→ Stable")
    )
    return combined.sort_values("delta", ascending=False).head(top_n).reset_index()


def role_category(title: str) -> str:
    """
    Bin a job title into a broad role category.
    Used for grouping in the dashboard.
    """
    title_lower = title.lower()

    if any(t in title_lower for t in ["data scientist", "data analyst", "data engineer", "ml engineer", "machine learning", "ai engineer"]):
        return "Data / ML / AI"
    if any(t in title_lower for t in ["frontend", "front-end", "ui developer", "react developer", "vue developer"]):
        return "Frontend"
    if any(t in title_lower for t in ["backend", "back-end", "api developer", "java developer", "python developer", "node developer"]):
        return "Backend"
    if any(t in title_lower for t in ["full stack", "fullstack", "full-stack"]):
        return "Full Stack"
    if any(t in title_lower for t in ["devops", "sre", "platform engineer", "cloud engineer", "infrastructure"]):
        return "DevOps / Cloud"
    if any(t in title_lower for t in ["qa", "test", "quality assurance", "automation engineer"]):
        return "QA / Testing"
    if any(t in title_lower for t in ["product manager", "scrum master", "agile coach", "project manager"]):
        return "Product / PM"
    if any(t in title_lower for t in ["security", "cybersecurity", "soc analyst", "penetration"]):
        return "Cybersecurity"
    if any(t in title_lower for t in ["manager", "head of", "director", "vp ", "chief"]):
        return "Management"

    return "Other / General"


def enrich_with_role_category(df: pd.DataFrame) -> pd.DataFrame:
    """Add a 'role_category' column to a jobs DataFrame."""
    if df.empty or "title" not in df.columns:
        return df
    df = df.copy()
    df["role_category"] = df["title"].apply(role_category)
    return df
