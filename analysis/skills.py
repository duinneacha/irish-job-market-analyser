"""
analysis/skills.py — Keyword-based skill extraction from job descriptions

Phase 1: regex keyword matching against a curated skill list (config.py)
Phase 2 (TODO): replace/augment with spaCy NER for better recall
"""

import re
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import SKILLS


def extract_skills(text: str) -> list[dict]:
    """
    Scan `text` for known tech skills.
    Returns a list of {"skill": str, "category": str} dicts.

    Uses word-boundary matching so e.g. "R" doesn't match inside "React".
    """
    if not text:
        return []

    found = []
    seen = set()

    for category, skill_patterns in SKILLS.items():
        for pattern in skill_patterns:
            # Use word boundaries; handle patterns with special chars (e.g. C++)
            regex = rf"(?<![A-Za-z0-9]){pattern}(?![A-Za-z0-9])"
            try:
                if re.search(regex, text, re.IGNORECASE):
                    # Normalise: remove regex escapes for display
                    skill_name = re.sub(r"\\", "", pattern)
                    if skill_name not in seen:
                        found.append({"skill": skill_name, "category": category})
                        seen.add(skill_name)
            except re.error:
                # If pattern is malformed, fall back to plain substring match
                if pattern.replace("\\", "") in text:
                    skill_name = pattern.replace("\\", "")
                    if skill_name not in seen:
                        found.append({"skill": skill_name, "category": category})
                        seen.add(skill_name)

    return found


def extract_and_store(job_id: int, description: str, title: str = "") -> int:
    """
    Extract skills from job description + title, store in DB.
    Returns number of skills found.
    """
    from database.db import insert_skills

    combined_text = f"{title} {description}"
    skills = extract_skills(combined_text)

    if skills:
        insert_skills(job_id, skills)

    return len(skills)


def skills_summary(jobs: list[dict]) -> dict[str, int]:
    """
    Aggregate skill counts across a list of job dicts (in-memory, for testing).
    Returns {skill_name: count} sorted by count desc.
    """
    counts: dict[str, int] = {}
    for job in jobs:
        combined = f"{job.get('title', '')} {job.get('description', '')}"
        for item in extract_skills(combined):
            skill = item["skill"]
            counts[skill] = counts.get(skill, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))
