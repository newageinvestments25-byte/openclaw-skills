# OpenClaw Skills by New Age Investments

A collection of high-quality, local-first OpenClaw skills. Every skill works without external API keys and uses only Python standard library — zero dependencies, maximum privacy.

## Skills

| Skill | Description | Install |
|---|---|---|
| [rss-digest](./rss-digest) | RSS/Atom feed aggregator with keyword filtering and cron scheduling | `npx clawhub@latest install nai-rss-digest` |
| [local-budget](./local-budget) | Bank CSV spending analyzer with auto-format detection (Chase, BoA, generic) | `npx clawhub@latest install nai-local-budget` |
| [file-organizer](./file-organizer) | Directory cleanup wizard with duplicate detection — never deletes, only moves | `npx clawhub@latest install nai-file-organizer` |
| [changelog-watcher](./changelog-watcher) | GitHub + npm release monitor with breaking change detection | `npx clawhub@latest install nai-changelog-watcher` |
| [habit-tracker](./habit-tracker) | Local streak tracking with weekly reviews and Obsidian integration | `npx clawhub@latest install nai-habit-tracker` |
| [price-watcher](./price-watcher) | Product URL price monitoring with multi-pass extraction and alerts | `npx clawhub@latest install nai-price-watcher` |
| [meeting-notes](./meeting-notes) | Raw notes → action items, decisions, and attendees for Obsidian | `npx clawhub@latest install nai-meeting-notes` |
| [morning-briefing](./morning-briefing) | Composable daily brief that adapts to your installed skills and data sources | `npx clawhub@latest install nai-morning-briefing` |

## Design Principles

- **Local-first** — All data stays on your machine. No cloud services, no telemetry.
- **Zero dependencies** — Python standard library only. No pip install required.
- **No API keys** — Every skill works out of the box with no configuration.
- **Obsidian-friendly** — Output is clean markdown with frontmatter, perfect for your vault.
- **Cron-ready** — Most skills are designed to run on a schedule via OpenClaw cron.

## Installation

Install any skill directly from ClawHub:

```bash
npx clawhub@latest install nai-<skill-name>
```

Or clone this repo and point OpenClaw at the skill folders directly.

## About

Built by [New Age Investments LLC](https://github.com/newageinvestments25-byte) — an AI-focused company building tools for the agent ecosystem.

Also building [TokenPulse](https://tokenpulse.to) — unified AI usage tracking for local and cloud models.

## License

MIT
