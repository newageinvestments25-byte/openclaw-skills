# Morning Briefing — Supported Sources

All sources are optional. The briefing degrades gracefully when any source is unavailable.

## Currently Supported

### Weather
- **Provider:** wttr.in (free, no API key)
- **Detection:** TCP reachability check to `wttr.in:80`
- **Data:** Current conditions, temperature, humidity, wind, UV index, tomorrow's forecast
- **Failure mode:** Silently skipped if network is down or request times out

### Tasks
- **Provider:** Local JSON file
- **Detection:** Looks for `tasks.json` in these locations (first match wins):
  - `~/.openclaw/workspace/tasks.json`
  - `~/.openclaw/workspace/tasks/tasks.json`
  - `~/.openclaw/tasks.json`
  - `~/.openclaw/tasks/tasks.json`
  - `~/.openclaw/workspace/todo.json`
- **Expected schema:** Array of task objects, or `{ "tasks": [...] }`
  - Required: `name` or `title` or `text`
  - Optional: `due` (ISO date), `priority`, `done`/`completed`/`status`
- **Output:** Overdue → due today → upcoming (up to 5 items total)

### Calendar
- **Provider:** OpenClaw cron jobs
- **Detection:** `~/.openclaw/cron/jobs.json`
- **Expected schema:** Array of job objects, or `{ "jobs": [...] }`
  - Required: none (graceful on missing fields)
  - Optional: `name`/`label`, `schedule`/`cron`, `command`/`cmd`, `disabled`
- **Output:** Active (non-disabled) jobs with name and schedule

### Habits
- **Provider:** habit-tracker skill data
- **Detection:** `~/.openclaw/workspace/habits/habits.json` (or `$HABIT_DATA_DIR`)
- **Companion file:** `log.json` in same directory (for today's completions)
- **Expected schema:** See habit-tracker skill's `references/data-format.md`
- **Output:** Done/todo split with streak counts

### RSS
- **Provider:** OPML file or recent digest
- **Detection:** Looks for (first match wins):
  - `~/.openclaw/workspace/feeds.opml`
  - `~/.openclaw/workspace/rss/feeds.opml`
  - `~/.openclaw/feeds.opml`
  - Any `digest*.md` or `digest*.json` in `~/.openclaw/workspace/rss/` modified within last 24h
- **Note:** Currently detected but not actively fetched at gather time. Extend `gather.py` to add RSS fetch logic.

### Git
- **Provider:** Local git repositories
- **Detection:** Searches for `.git` dirs (2 levels deep) in:
  - `~/.openclaw/workspace/`
  - `~/code/`, `~/projects/`, `~/dev/`, `~/src/`
  - Repos with `COMMIT_EDITMSG`, `FETCH_HEAD`, or `HEAD` modified in last 24h
- **Data:** Last 5 commits per repo, from the past 24 hours
- **Failure mode:** Silently skips repos where `git log` fails or times out

---

## Adding a New Source

1. **detect_sources.py** — Add a `check_<name>()` function that returns a source dict or `None`. Register it in the `checks` list in `main()`.

2. **gather.py** — Add a `gather_<name>(source: dict)` function that reads the source and returns structured data. Register it in the `gatherers` dict in `main()`.

3. **briefing.py** — Add a `format_<name>(data: dict)` function that returns a list of markdown lines. Register it in `formatters` and `section_order` in `build_briefing()`.

4. **references/sources.md** — Document the new source here.

### Design rules for new sources
- Never raise exceptions — return `None` on any failure
- Respect the "stdlib only" constraint (json, sys, os, datetime, subprocess, pathlib, glob, urllib)
- Keep sections under ~6 lines in the briefing output
- Add the source to `section_order` in briefing.py at the appropriate priority level
