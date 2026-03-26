# Meeting Notes Templates & Customization

## Obsidian Output Format

```markdown
---
date: YYYY-MM-DD
type: meeting-notes
title: "Meeting Title"
tags: [meeting-notes, planning]
---

# Meeting Title

## Attendees
- Alice
- Bob

## Key Decisions
- Decided to postpone launch to Q2.
- Agreed on a weekly sync cadence.

## Action Items
- [ ] @alice: Prepare the revised proposal (due: Friday)
- [ ] @bob: Schedule follow-up call (due: next Monday)
- [ ] Update roadmap document

## Topics Discussed
- Q2 Roadmap
- Budget Review

## Raw Notes

\`\`\`
<original notes preserved verbatim>
\`\`\`
```

## Checklist-Only Output

```markdown
# Sprint Planning — 2024-03-15

- [ ] @alice: Prepare sprint backlog (due: Monday)
- [ ] @bob: Review capacity estimates
- [ ] Update Jira board
```

## Pipeline Commands

### Full pipeline: file → Obsidian vault
```bash
python3 scripts/extract.py --file notes.txt \
  | python3 scripts/format_obsidian.py \
      --title "Sprint Planning" \
      --tags "sprint,engineering" \
      --output ~/vault/meetings/2024-03-15-sprint-planning.md
```

### Quick checklist to stdout
```bash
python3 scripts/extract.py --file notes.txt | python3 scripts/format_checklist.py
```

### Pretty-print extracted JSON (for debugging)
```bash
python3 scripts/extract.py --file notes.txt --pretty
```

### Checklist without owner names
```bash
python3 scripts/extract.py --file notes.txt | python3 scripts/format_checklist.py --no-owners
```

### JSON from stdin (pasted text)
```bash
pbpaste | python3 scripts/extract.py | python3 scripts/format_obsidian.py
```

## Recognized Input Patterns

### Action Items — Triggers
| Pattern | Example |
|---|---|
| `TODO:` / `ACTION:` / `TASK:` | `TODO: Update documentation` |
| `@person: task` | `@alice: Send meeting invite` |
| `Name will task` | `Bob will prepare the slides` |
| `Name needs to task` | `Sarah needs to review the contract` |
| `- task by date` | `- Submit report by Friday` |
| `[ ] task` | `[ ] Follow up with client` |

### Decisions — Triggers
`decided`, `agreed`, `decision:`, `we will`, `team will`, `resolved`

### Attendees — Triggers
Lines starting with: `Attendees:`, `Present:`, `Participants:`, `In Attendance:`

### Due Dates — Recognized formats
- `by Friday`, `by Monday`
- `by March 15` / `by March 15, 2024`
- `by 03/15/2024` or `by 03-15`
- `next week`, `end of week` (EOW), `end of month` (EOM)
- `today`, `tomorrow`

## Customization Notes

- **Extra tags**: Pass `--tags "tag1,tag2"` to `format_obsidian.py`
- **Title override**: Pass `--title "Custom Title"` to either formatter
- **No due dates in checklist**: Use `--no-due` flag
- **Plain text output** (no checkboxes): Use `--plain` flag on `format_checklist.py`
- **JSON passthrough**: Use `extract.py` output with your own processing pipeline
