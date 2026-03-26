#!/usr/bin/env python3
"""
detect_sources.py — Detect available data sources for morning briefing.
Outputs JSON listing available sources with their data paths.
"""

import json
import os
import sys
import socket
from datetime import datetime, timedelta
from pathlib import Path
from glob import glob

HOME = Path.home()
WORKSPACE = HOME / ".openclaw" / "workspace"


def check_weather() -> dict | None:
    """Check if wttr.in is reachable (free, no API key)."""
    try:
        sock = socket.create_connection(("wttr.in", 80), timeout=3)
        sock.close()
        return {"type": "weather", "url": "https://wttr.in"}
    except (OSError, socket.timeout):
        return None


def check_calendar() -> dict | None:
    """Check for OpenClaw cron jobs file."""
    jobs_path = HOME / ".openclaw" / "cron" / "jobs.json"
    if jobs_path.exists():
        return {"type": "calendar", "path": str(jobs_path)}
    return None


def check_tasks() -> dict | None:
    """Check for task files in common locations."""
    candidates = [
        WORKSPACE / "tasks.json",
        WORKSPACE / "tasks" / "tasks.json",
        HOME / ".openclaw" / "tasks.json",
        HOME / ".openclaw" / "tasks" / "tasks.json",
        WORKSPACE / "todo.json",
    ]
    for p in candidates:
        if p.exists():
            return {"type": "tasks", "path": str(p)}
    return None


def check_habits() -> dict | None:
    """Check for habit-tracker skill data."""
    habit_data_dir = Path(os.environ.get("HABIT_DATA_DIR", str(WORKSPACE / "habits")))
    habits_file = habit_data_dir / "habits.json"
    log_file = habit_data_dir / "log.json"
    if habits_file.exists():
        return {
            "type": "habits",
            "path": str(habits_file),
            "log_path": str(log_file) if log_file.exists() else None,
        }
    return None


def check_rss() -> dict | None:
    """Check for OPML file or recent RSS digest."""
    candidates = [
        WORKSPACE / "feeds.opml",
        WORKSPACE / "rss" / "feeds.opml",
        HOME / ".openclaw" / "feeds.opml",
    ]
    for p in candidates:
        if p.exists():
            return {"type": "rss", "path": str(p), "subtype": "opml"}

    # Check for recent digest files (generated within last 24h)
    digest_patterns = [
        str(WORKSPACE / "rss" / "digest*.md"),
        str(WORKSPACE / "rss" / "digest*.json"),
        str(WORKSPACE / "rss" / "*.digest.md"),
    ]
    cutoff = datetime.now() - timedelta(hours=24)
    for pattern in digest_patterns:
        for f in glob(pattern):
            fp = Path(f)
            if fp.stat().st_mtime > cutoff.timestamp():
                return {"type": "rss", "path": f, "subtype": "digest"}

    return None


def check_git() -> dict | None:
    """Check for git repos with recent commits (last 24h)."""
    search_dirs = [
        WORKSPACE,
        HOME / "code",
        HOME / "projects",
        HOME / "dev",
        HOME / "src",
    ]
    cutoff = datetime.now() - timedelta(hours=24)
    active_repos = []

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        # Find .git directories up to 2 levels deep
        for git_dir in list(search_dir.glob(".git")) + list(search_dir.glob("*/.git")):
            repo_dir = git_dir.parent
            # Check FETCH_HEAD or COMMIT_EDITMSG mtime as proxy for recent activity
            for indicator in ["COMMIT_EDITMSG", "FETCH_HEAD", "HEAD"]:
                indicator_path = git_dir / indicator
                if indicator_path.exists():
                    if indicator_path.stat().st_mtime > cutoff.timestamp():
                        active_repos.append(str(repo_dir))
                        break

    if active_repos:
        return {"type": "git", "repos": list(set(active_repos))[:5]}
    return None


def main():
    sources = {}

    checks = [
        ("weather", check_weather),
        ("calendar", check_calendar),
        ("tasks", check_tasks),
        ("habits", check_habits),
        ("rss", check_rss),
        ("git", check_git),
    ]

    for name, fn in checks:
        try:
            result = fn()
            if result:
                sources[name] = result
        except Exception as e:
            # Never crash on a missing source
            sources[f"{name}_error"] = str(e)

    output = {
        "detected_at": datetime.now().isoformat(),
        "sources": sources,
        "count": len([k for k in sources if not k.endswith("_error")]),
    }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
