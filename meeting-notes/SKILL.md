---
name: meeting-notes
description: Extract structured action items, decisions, and attendees from raw meeting notes. Use when: (1) user pastes or provides meeting notes and wants action items extracted, (2) asks for a meeting summary, (3) wants tasks formatted as a checklist, (4) wants notes saved to Obsidian, (5) says "process meeting", "extract tasks from notes", "meeting summary", "action items", or "summarize this meeting". Outputs Obsidian-compatible markdown, plain checklist, or raw JSON. No API key required. Scripts location: skills/meeting-notes/scripts/
---

# Meeting Notes

Extract action items, decisions, and attendees from raw notes. Format for Obsidian or plain checklist.

## Workflow

### 1. Get the raw notes
Accept input as:
- Pasted text in the conversation → write to a temp file (`/tmp/meeting_notes.txt`)
- An existing file path provided by the user

### 2. Choose output format
| User wants | Command |
|---|---|
| Obsidian vault entry | `extract.py` → `format_obsidian.py --output <vault path>` |
| Plain checklist | `extract.py` → `format_checklist.py` |
| Raw JSON (further processing) | `extract.py --pretty` |

### 3. Run the pipeline

**Save to Obsidian vault:**
```bash
python3 skills/meeting-notes/scripts/extract.py --file /tmp/meeting_notes.txt \
  | python3 skills/meeting-notes/scripts/format_obsidian.py \
      --title "Meeting Title" \
      --tags "tag1,tag2" \
      --output /Users/openclaw/.openclaw/workspace/vault/meetings/YYYY-MM-DD-title.md
```

**Checklist to stdout (show user):**
```bash
python3 skills/meeting-notes/scripts/extract.py --file /tmp/meeting_notes.txt \
  | python3 skills/meeting-notes/scripts/format_checklist.py
```

**JSON only:**
```bash
python3 skills/meeting-notes/scripts/extract.py --file /tmp/meeting_notes.txt --pretty
```

### 4. Present results
- Show the action items list to the user in the conversation
- Confirm file path if saved to Obsidian
- If nothing was found, say so clearly and offer to show the raw extraction

## Key Flags

**extract.py**
- `--file` / `-f` — input file path (default: stdin)
- `--pretty` — pretty-print JSON

**format_obsidian.py**
- `--output` / `-o` — save to file path (default: stdout)
- `--title` — override meeting title
- `--tags` — comma-separated extra tags

**format_checklist.py**
- `--output` / `-o` — save to file path (default: stdout)
- `--no-owners` — omit @owner prefixes
- `--no-due` — omit due dates
- `--plain` — plain dashes instead of `- [ ]` checkboxes

## Edge Cases
- **No action items found**: scripts output `_No action items found._` — tell user and show decisions/attendees if any
- **No dates on tasks**: task appears without `(due: ...)`, still included
- **No attendees line**: skips attendees section gracefully; @mentions in text are captured as fallback
- **Messy formatting**: patterns are regex-based, works on mixed indentation and bullet styles
- **Multi-format dates**: recognizes `by Friday`, `by March 15`, `03/15`, `EOW`, `next week`, etc.

## Obsidian Save Rule
Only save to vault if the user explicitly asks. Trigger phrases: "save to Obsidian", "put this in my vault", "log this meeting". Otherwise, output to stdout and show the user inline. See SOUL.md.

## Output Format Reference
See `references/templates.md` for full format examples and all pipeline command patterns.
