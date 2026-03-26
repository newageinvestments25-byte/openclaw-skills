---
name: morning-briefing
description: "Generate a concise daily morning briefing that adapts to whatever data sources are available — weather, tasks, calendar, habits, git activity. Produces a brief under 300 words. Use when: user says morning briefing, daily brief, what's on today, brief me, start my day, what's up today, give me my brief, or any similar request for a daily summary or morning rundown."
---

# Morning Briefing Skill

Composable briefing that pulls from available local data sources. Gracefully degrades:
if nothing is configured, outputs a minimal brief with just the date and time.

Scripts live in `scripts/` relative to this SKILL.md.
Resolve all script paths as: `/Users/openclaw/.openclaw/workspace/skills/morning-briefing/scripts/<script>`

---

## Generate a Briefing

### Quick (recommended)

```bash
python scripts/briefing.py
```

Runs the full pipeline automatically (detect → gather → format). Prints markdown to stdout.

### Pipeline (explicit)

```bash
python scripts/detect_sources.py | python scripts/gather.py | python scripts/briefing.py
```

### Save to file

```bash
python scripts/briefing.py --output ~/Desktop/brief.md
```

### Plain text output

```bash
python scripts/briefing.py --format text
```

---

## What It Detects

Run `detect_sources.py` alone to see what's available:

```bash
python scripts/detect_sources.py
```

Sources checked (in briefing priority order):
1. **Weather** — wttr.in reachable (no API key needed)
2. **Tasks** — `tasks.json` in common workspace locations
3. **Calendar** — `~/.openclaw/cron/jobs.json`
4. **Habits** — habit-tracker data at `~/.openclaw/workspace/habits/`
5. **Git** — repos with commits in last 24h

See `references/sources.md` for full detection paths and how to add new sources.

---

## Presenting the Briefing

- Print the markdown output directly in the conversation — it formats well in Discord
- Keep any commentary brief: the briefing speaks for itself
- If weather is unavailable (network down), note it only if the user seems to expect it
- If no sources are found, say so and note which sources can be configured

---

## Interpreting User Requests

| User says | Action |
|-----------|--------|
| "Morning briefing" / "Brief me" | `python scripts/briefing.py` |
| "What's on today?" | Same — leads with tasks/calendar |
| "Start my day" | Same — full briefing |
| "What's the weather today?" | Use weather skill instead |
| "Skip weather in my brief" | Run detect, remove weather key, pipe to gather, then briefing |

---

## Troubleshooting

- **No weather:** Network is down or wttr.in unreachable — briefing skips it silently
- **No tasks:** No `tasks.json` found in expected locations
- **No habits:** habit-tracker skill not set up (run `setup_habits.py` from that skill)
- **Empty briefing:** No sources detected — output still includes date/time header
