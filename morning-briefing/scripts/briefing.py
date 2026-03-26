#!/usr/bin/env python3
"""
briefing.py — Format gathered data into a concise morning briefing.
Reads gathered JSON from stdin or a file, outputs markdown or plain text.

Usage:
  python briefing.py [--output FILE] [--format markdown|text] [GATHERED_JSON]
  python gather.py | python briefing.py
  python briefing.py gathered.json --output brief.md --format markdown
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


def format_weather(data: dict) -> list[str]:
    lines = []
    loc = data.get("location", "")
    cond = data.get("condition", "")
    temp_f = data.get("temp_f", "?")
    feels = data.get("feels_like_f", "?")
    humidity = data.get("humidity", "?")
    wind = data.get("wind_mph", "?")
    wind_dir = data.get("wind_dir", "")
    uv = data.get("uv_index", "?")

    header = f"## 🌤 Weather"
    if loc:
        header += f" — {loc}"
    lines.append(header)

    summary = f"**{cond}**, {temp_f}°F (feels like {feels}°F)"
    lines.append(summary)
    lines.append(f"Humidity {humidity}% · Wind {wind} mph {wind_dir} · UV {uv}")

    forecast = data.get("forecast", [])
    if len(forecast) >= 2:
        tomorrow = forecast[1]
        lines.append(
            f"Tomorrow: {tomorrow.get('description', '?')} · "
            f"High {tomorrow.get('high_f', '?')}°F / Low {tomorrow.get('low_f', '?')}°F"
        )

    return lines


def format_tasks(data: dict) -> list[str]:
    lines = ["## ✅ Tasks"]
    total = data.get("total_pending", 0)
    overdue = data.get("overdue", [])
    due_today = data.get("due_today", [])
    pending = data.get("pending", [])

    if overdue:
        lines.append(f"**⚠️ Overdue ({len(overdue)})**")
        for t in overdue:
            lines.append(f"  - {t['name']}")

    if due_today:
        lines.append(f"**Due today ({len(due_today)})**")
        for t in due_today:
            lines.append(f"  - {t['name']}")

    if pending and not (overdue or due_today):
        # Show a few upcoming if nothing urgent
        lines.append(f"**Upcoming**")
        for t in pending[:3]:
            lines.append(f"  - {t['name']}" + (f" (due {t['due']})" if t.get('due') else ""))

    if total > (len(overdue) + len(due_today) + len(pending[:3])):
        extra = total - len(overdue) - len(due_today) - len(pending[:3])
        if extra > 0:
            lines.append(f"  _{extra} more task(s) in queue_")

    return lines


def format_calendar(data: dict) -> list[str]:
    jobs = data.get("jobs", [])
    if not jobs:
        return []
    lines = ["## 📅 Scheduled Jobs"]
    for job in jobs[:5]:
        name = job.get("name", "Unnamed")
        schedule = job.get("schedule", "")
        lines.append(f"  - **{name}**" + (f" `{schedule}`" if schedule else ""))
    if len(jobs) > 5:
        lines.append(f"  _{len(jobs) - 5} more scheduled jobs_")
    return lines


def format_habits(data: dict) -> list[str]:
    done = data.get("done", [])
    todo = data.get("todo", [])
    total = data.get("total", 0)
    completed = data.get("completed_count", 0)

    lines = [f"## 🔥 Habits — {completed}/{total} done today"]

    if todo:
        lines.append("**Still to do:**")
        for h in todo:
            streak_info = f" (streak: {h['streak']})" if h.get("streak") else ""
            lines.append(f"  - {h['name']}{streak_info}")

    if done:
        lines.append("**Completed:**")
        for h in done:
            streak_info = f" (streak: {h['streak']})" if h.get("streak") else ""
            lines.append(f"  - ~~{h['name']}~~{streak_info}")

    return lines


def format_git(data: dict) -> list[str]:
    repos = data.get("repos", [])
    if not repos:
        return []
    lines = ["## 💻 Recent Git Activity"]
    for repo in repos:
        count = repo.get("count", 0)
        commits = repo.get("commits", [])
        name = repo.get("repo", "unknown")
        lines.append(f"**{name}** — {count} commit(s) in last 24h")
        for c in commits[:2]:
            lines.append(f"  - `{c}`")
    return lines


def to_plain_text(markdown_lines: list[str]) -> list[str]:
    """Strip markdown formatting for plain text output."""
    result = []
    for line in markdown_lines:
        # Strip headers
        stripped = line.lstrip("#").strip()
        # Strip bold/italic
        for marker in ["**", "__", "*", "_", "~~"]:
            stripped = stripped.replace(marker, "")
        # Strip inline code
        stripped = stripped.replace("`", "")
        result.append(stripped)
    return result


def build_briefing(gathered: dict, fmt: str = "markdown") -> str:
    data = gathered.get("data", {})
    day = gathered.get("day_of_week", "")
    date_str = gathered.get("date", "")
    gathered_at = gathered.get("gathered_at", "")

    # Parse time from gathered_at
    time_str = ""
    if gathered_at:
        try:
            dt = datetime.fromisoformat(gathered_at)
            time_str = dt.strftime("%I:%M %p").lstrip("0")
        except ValueError:
            pass

    sections = []

    # Header
    date_display = f"{day}, {date_str}" if day else date_str
    header = f"# 🌅 Morning Briefing — {date_display}"
    if time_str:
        header += f"  \n_{time_str}_"
    sections.append([header])

    if not data:
        sections.append(["_No data sources available. Have a great day!_"])
    else:
        # Priority order: weather → tasks → calendar → habits → git
        section_order = ["weather", "tasks", "calendar", "habits", "git"]
        formatters = {
            "weather": format_weather,
            "tasks": format_tasks,
            "calendar": format_calendar,
            "habits": format_habits,
            "git": format_git,
        }

        for key in section_order:
            if key in data:
                try:
                    section_lines = formatters[key](data[key])
                    if section_lines:
                        sections.append(section_lines)
                except Exception:
                    pass

    all_lines = []
    for i, section in enumerate(sections):
        if i > 0:
            all_lines.append("")
        all_lines.extend(section)

    if fmt == "text":
        all_lines = to_plain_text(all_lines)

    return "\n".join(all_lines)


def main():
    parser = argparse.ArgumentParser(description="Generate morning briefing from gathered data")
    parser.add_argument("input", nargs="?", help="Path to gathered JSON (default: stdin)")
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    parser.add_argument("--format", "-f", choices=["markdown", "text"], default="markdown",
                        help="Output format (default: markdown)")
    args = parser.parse_args()

    # Read input — try file arg first, then piped stdin, then run full pipeline
    gathered = None

    if args.input:
        try:
            with open(args.input) as f:
                gathered = json.load(f)
        except Exception:
            gathered = None
    elif not sys.stdin.isatty():
        # stdin may be piped JSON OR a terminal pseudo-pipe (heredoc, etc.)
        try:
            raw = sys.stdin.read().strip()
            if raw and raw.startswith("{"):
                gathered = json.loads(raw)
        except Exception:
            gathered = None

    if gathered is None:
        # Run full pipeline automatically: detect → gather → briefing
        import subprocess
        try:
            script_dir = Path(__file__).parent
            detect_result = subprocess.run(
                [sys.executable, str(script_dir / "detect_sources.py")],
                capture_output=True, text=True, timeout=10
            )
            gather_result = subprocess.run(
                [sys.executable, str(script_dir / "gather.py")],
                input=detect_result.stdout,
                capture_output=True, text=True, timeout=20
            )
            if gather_result.stdout.strip():
                gathered = json.loads(gather_result.stdout)
        except Exception:
            pass

    if gathered is None:
        # Absolute fallback: just date/time, no data
        from datetime import date as _date
        gathered = {
            "date": _date.today().isoformat(),
            "day_of_week": datetime.now().strftime("%A"),
            "gathered_at": datetime.now().isoformat(),
            "data": {},
        }

    briefing = build_briefing(gathered, fmt=args.format)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(briefing)
        print(f"Briefing saved to {args.output}", file=sys.stderr)
    else:
        print(briefing)


if __name__ == "__main__":
    main()
