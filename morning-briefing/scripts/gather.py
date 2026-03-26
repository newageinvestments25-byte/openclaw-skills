#!/usr/bin/env python3
"""
gather.py — Collect data from available sources, output unified JSON.
Reads detect_sources.py output (or re-runs detection) and fetches each source.
"""

import json
import os
import subprocess
import sys
from datetime import datetime, date, timedelta
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError

SCRIPT_DIR = Path(__file__).parent


def run_detect() -> dict:
    """Run detect_sources.py and return parsed JSON."""
    try:
        result = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "detect_sources.py")],
            capture_output=True, text=True, timeout=10
        )
        return json.loads(result.stdout)
    except Exception as e:
        return {"sources": {}, "count": 0, "error": str(e)}


def gather_weather(source: dict) -> dict | None:
    """Fetch weather from wttr.in JSON API."""
    try:
        req = Request(
            "https://wttr.in/?format=j1",
            headers={"User-Agent": "morning-briefing/1.0"}
        )
        with urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())

        current = data.get("current_condition", [{}])[0]
        area = data.get("nearest_area", [{}])[0]
        area_name = area.get("areaName", [{}])[0].get("value", "Unknown")
        region = area.get("region", [{}])[0].get("value", "")

        weather_desc = current.get("weatherDesc", [{}])[0].get("value", "Unknown")
        temp_f = current.get("temp_F", "?")
        temp_c = current.get("temp_C", "?")
        feels_like_f = current.get("FeelsLikeF", "?")
        humidity = current.get("humidity", "?")
        wind_mph = current.get("windspeedMiles", "?")
        wind_dir = current.get("winddir16Point", "")
        precip = current.get("precipMM", "0")
        uv_index = current.get("uvIndex", "?")

        # Tomorrow's forecast
        forecast = []
        for day_data in data.get("weather", [])[:2]:
            day_date = day_data.get("date", "")
            max_f = day_data.get("maxtempF", "?")
            min_f = day_data.get("mintempF", "?")
            hourly = day_data.get("hourly", [{}])
            desc = hourly[4].get("weatherDesc", [{}])[0].get("value", "Unknown") if len(hourly) > 4 else "Unknown"
            forecast.append({
                "date": day_date,
                "high_f": max_f,
                "low_f": min_f,
                "description": desc,
            })

        return {
            "location": f"{area_name}, {region}".strip(", "),
            "condition": weather_desc,
            "temp_f": temp_f,
            "temp_c": temp_c,
            "feels_like_f": feels_like_f,
            "humidity": humidity,
            "wind_mph": wind_mph,
            "wind_dir": wind_dir,
            "precip_mm": precip,
            "uv_index": uv_index,
            "forecast": forecast,
        }
    except (URLError, OSError, KeyError, json.JSONDecodeError) as e:
        return None  # Gracefully skip if network is down


def gather_calendar(source: dict) -> dict | None:
    """Read OpenClaw cron jobs and return upcoming items."""
    try:
        jobs_path = Path(source["path"])
        with open(jobs_path) as f:
            jobs_data = json.load(f)

        jobs = jobs_data if isinstance(jobs_data, list) else jobs_data.get("jobs", [])
        # Return enabled jobs with basic info
        active = []
        for job in jobs:
            if isinstance(job, dict) and job.get("enabled", True) and not job.get("disabled", False):
                # schedule can be a dict like {"kind": "cron", "expr": "..."} or a plain string
                raw_sched = job.get("schedule", job.get("cron", ""))
                if isinstance(raw_sched, dict):
                    kind = raw_sched.get("kind", "")
                    expr = raw_sched.get("expr", raw_sched.get("everyMs", ""))
                    schedule_str = f"{kind}: {expr}" if expr else kind
                else:
                    schedule_str = str(raw_sched)
                active.append({
                    "name": job.get("name", job.get("label", "Unnamed")),
                    "schedule": schedule_str,
                    "command": str(job.get("command", job.get("cmd", "")))[:80],
                })
        return {"jobs": active, "total": len(active)} if active else None
    except Exception:
        return None


def gather_tasks(source: dict) -> dict | None:
    """Read task JSON file."""
    try:
        tasks_path = Path(source["path"])
        with open(tasks_path) as f:
            tasks_data = json.load(f)

        tasks = tasks_data if isinstance(tasks_data, list) else tasks_data.get("tasks", [])

        today_str = date.today().isoformat()
        pending = []
        due_today = []
        overdue = []

        for task in tasks:
            if not isinstance(task, dict):
                continue
            if task.get("done") or task.get("completed") or task.get("status") == "done":
                continue

            due = task.get("due") or task.get("due_date") or task.get("dueDate")
            name = task.get("name") or task.get("title") or task.get("text") or "Unnamed task"
            priority = task.get("priority", "normal")

            item = {"name": name, "priority": priority, "due": due}
            if due:
                if due < today_str:
                    overdue.append(item)
                elif due == today_str:
                    due_today.append(item)
                else:
                    pending.append(item)
            else:
                pending.append(item)

        total_pending = len(pending) + len(due_today) + len(overdue)
        if total_pending == 0:
            return None

        return {
            "due_today": due_today[:5],
            "overdue": overdue[:3],
            "pending": pending[:3],
            "total_pending": total_pending,
        }
    except Exception:
        return None


def gather_habits(source: dict) -> dict | None:
    """Read habit-tracker data and return today's status."""
    try:
        habits_path = Path(source["path"])
        log_path = Path(source["log_path"]) if source.get("log_path") else None

        with open(habits_path) as f:
            habits_raw = json.load(f)

        habits = habits_raw if isinstance(habits_raw, list) else habits_raw.get("habits", [])
        active_habits = [h for h in habits if isinstance(h, dict) and not h.get("archived", False)]

        if not active_habits:
            return None

        today_str = date.today().isoformat()
        completed_today = set()

        if log_path and log_path.exists():
            with open(log_path) as f:
                log_raw = json.load(f)
            log = log_raw if isinstance(log_raw, list) else log_raw.get("entries", log_raw.get("log", []))
            for entry in log:
                if not isinstance(entry, dict):
                    continue
                entry_date = entry.get("date", "")
                if entry_date == today_str:
                    hid = entry.get("habit_id") or entry.get("id") or entry.get("habit")
                    hname = entry.get("habit_name") or entry.get("name") or entry.get("habit")
                    if hid:
                        completed_today.add(str(hid))
                    if hname:
                        completed_today.add(str(hname))

        done = []
        todo = []
        for h in active_habits:
            hid = str(h.get("id", ""))
            hname = h.get("name", "")
            emoji = h.get("emoji", "")
            label = f"{emoji} {hname}".strip() if emoji else hname
            streak = h.get("streak", h.get("current_streak", 0))

            if hid in completed_today or hname in completed_today:
                done.append({"name": label, "streak": streak})
            else:
                todo.append({"name": label, "streak": streak})

        return {
            "done": done,
            "todo": todo,
            "total": len(active_habits),
            "completed_count": len(done),
        }
    except Exception:
        return None


def gather_git(source: dict) -> dict | None:
    """Get recent git activity from detected repos."""
    repos = source.get("repos", [])
    if not repos:
        return None

    since = (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M")
    summaries = []
    seen_paths = set()

    for repo_path in repos[:5]:
        # Resolve real path to avoid duplicate symlinked/case-variant repos
        try:
            real_path = str(Path(repo_path).resolve()).lower()
        except OSError:
            real_path = repo_path.lower()
        if real_path in seen_paths:
            continue
        seen_paths.add(real_path)

        try:
            result = subprocess.run(
                ["git", "-C", repo_path, "log", "--oneline",
                 f"--since={since}", "--all", "--max-count=5"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                commits = result.stdout.strip().split("\n")
                name_result = subprocess.run(
                    ["git", "-C", repo_path, "rev-parse", "--show-toplevel"],
                    capture_output=True, text=True, timeout=5
                )
                repo_name = Path(name_result.stdout.strip()).name if name_result.returncode == 0 else Path(repo_path).name
                summaries.append({
                    "repo": repo_name,
                    "commits": commits[:3],
                    "count": len(commits),
                })
        except (subprocess.TimeoutExpired, OSError):
            continue

    return {"repos": summaries, "total_repos": len(summaries)} if summaries else None


def main():
    # Read sources from stdin if piped, otherwise detect
    if not sys.stdin.isatty():
        try:
            detection = json.load(sys.stdin)
        except Exception:
            detection = run_detect()
    else:
        detection = run_detect()

    sources = detection.get("sources", {})
    gathered = {
        "gathered_at": datetime.now().isoformat(),
        "date": date.today().isoformat(),
        "day_of_week": datetime.now().strftime("%A"),
        "data": {},
    }

    gatherers = {
        "weather": gather_weather,
        "calendar": gather_calendar,
        "tasks": gather_tasks,
        "habits": gather_habits,
        "git": gather_git,
    }

    for source_name, fn in gatherers.items():
        if source_name in sources:
            try:
                result = fn(sources[source_name])
                if result:
                    gathered["data"][source_name] = result
            except Exception as e:
                # Never crash on gather failure
                pass

    print(json.dumps(gathered, indent=2))


if __name__ == "__main__":
    main()
