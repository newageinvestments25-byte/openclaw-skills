#!/usr/bin/env python3
"""
format_obsidian.py — Convert structured meeting JSON to Obsidian-compatible markdown.

Usage:
    python3 extract.py --file notes.txt | python3 format_obsidian.py
    python3 extract.py --file notes.txt | python3 format_obsidian.py --output vault/meetings/2024-03-15.md
    cat meeting.json | python3 format_obsidian.py --title "Q1 Planning" --tags "planning,q1"
"""

import argparse
import json
import os
import sys
from datetime import datetime


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def slugify(text: str) -> str:
    """Convert text to a safe filename slug."""
    import re
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-')


def format_task_line(item: dict) -> str:
    """Format a single action item as an Obsidian task."""
    parts = []
    if item.get('owner'):
        parts.append(f"@{item['owner']}:")
    parts.append(item.get('task', item.get('raw', '(unknown task)')))
    line = ' '.join(parts)
    if item.get('due'):
        line += f" (due: {item['due']})"
    return f'- [ ] {line}'


def build_tags(data: dict, extra_tags: list[str]) -> list[str]:
    tags = ['meeting-notes']
    tags.extend(extra_tags)
    # Auto-tag from topic keywords
    topic_text = ' '.join(data.get('topics', [])).lower()
    keyword_tags = {
        'sprint': 'sprint', 'planning': 'planning', 'retrospective': 'retro',
        'review': 'review', 'budget': 'budget', 'design': 'design',
        'engineering': 'engineering', 'sales': 'sales', 'marketing': 'marketing',
        'onboarding': 'onboarding', 'roadmap': 'roadmap', 'standup': 'standup',
    }
    for keyword, tag in keyword_tags.items():
        if keyword in topic_text and tag not in tags:
            tags.append(tag)
    return tags


# ---------------------------------------------------------------------------
# Markdown builder
# ---------------------------------------------------------------------------

def build_markdown(data: dict, extra_tags: list[str], title_override: str | None) -> str:
    lines = []
    date_str = data.get('date', datetime.today().strftime('%Y-%m-%d'))
    title = title_override or data.get('title') or f'Meeting Notes – {date_str}'
    tags = build_tags(data, extra_tags)

    # --- YAML frontmatter ---
    lines.append('---')
    lines.append(f'date: {date_str}')
    lines.append(f'type: meeting-notes')
    lines.append(f'title: "{title}"')
    tag_list = ', '.join(tags)
    lines.append(f'tags: [{tag_list}]')
    lines.append('---')
    lines.append('')

    # --- Title ---
    lines.append(f'# {title}')
    lines.append('')

    # --- Attendees ---
    attendees = data.get('attendees', [])
    lines.append('## Attendees')
    if attendees:
        for a in attendees:
            lines.append(f'- {a}')
    else:
        lines.append('_No attendees recorded._')
    lines.append('')

    # --- Key Decisions ---
    decisions = data.get('decisions', [])
    lines.append('## Key Decisions')
    if decisions:
        for d in decisions:
            lines.append(f'- {d}')
    else:
        lines.append('_No decisions recorded._')
    lines.append('')

    # --- Action Items ---
    action_items = data.get('action_items', [])
    lines.append('## Action Items')
    if action_items:
        for item in action_items:
            lines.append(format_task_line(item))
    else:
        lines.append('_No action items found._')
    lines.append('')

    # --- Topics Discussed ---
    topics = data.get('topics', [])
    if topics:
        lines.append('## Topics Discussed')
        for t in topics:
            lines.append(f'- {t}')
        lines.append('')

    # --- Raw Notes ---
    raw = data.get('raw', '').strip()
    if raw:
        lines.append('## Raw Notes')
        lines.append('')
        lines.append('```')
        lines.append(raw)
        lines.append('```')
        lines.append('')

    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='Format meeting JSON as Obsidian markdown.')
    parser.add_argument('--output', '-o', help='Output file path (default: stdout)')
    parser.add_argument('--title', help='Override the meeting title')
    parser.add_argument('--tags', help='Comma-separated extra tags to add')
    parser.add_argument('--input', '-i', help='Input JSON file (default: stdin)')
    args = parser.parse_args()

    # Read input
    if args.input:
        try:
            with open(args.input, 'r', encoding='utf-8') as fh:
                raw_json = fh.read()
        except FileNotFoundError:
            print(f'Error: file not found: {args.input}', file=sys.stderr)
            sys.exit(1)
    else:
        raw_json = sys.stdin.read()

    if not raw_json.strip():
        print('Error: no JSON input provided', file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as e:
        print(f'Error: invalid JSON: {e}', file=sys.stderr)
        sys.exit(1)

    extra_tags = [t.strip() for t in args.tags.split(',')] if args.tags else []
    markdown = build_markdown(data, extra_tags, args.title)

    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        try:
            with open(args.output, 'w', encoding='utf-8') as fh:
                fh.write(markdown)
            print(f'Saved: {args.output}', file=sys.stderr)
        except IOError as e:
            print(f'Error writing file: {e}', file=sys.stderr)
            sys.exit(1)
    else:
        print(markdown)


if __name__ == '__main__':
    main()
