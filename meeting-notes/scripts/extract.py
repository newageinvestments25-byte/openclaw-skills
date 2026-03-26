#!/usr/bin/env python3
"""
extract.py — Parse raw meeting notes and output structured JSON.

Usage:
    python3 extract.py --file notes.txt
    cat notes.txt | python3 extract.py
    python3 extract.py  # reads from stdin interactively
"""

import argparse
import json
import re
import sys
from datetime import datetime, date


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Action item patterns
ACTION_PATTERNS = [
    r'^\s*(?:TODO|ACTION ITEM|ACTION|TASK)[:\s-]+(.+)',           # TODO: / ACTION: / TASK: / ACTION ITEM:
    r'^\s*[-*]\s+(?:TODO|ACTION ITEM|ACTION|TASK)[:\s-]+(.+)',   # - TODO: ...
    r'^\s*[-*]\s+(.+?)\s+will\s+(.+)',                            # - Alice will prepare the deck
    r'^\s*[-*]\s+(.+?)\s+(?:needs? to|should|must|is going to)\s+(.+)',  # - Bob needs to review
    r'^\s*[-*•]\s+@(\w+)[:\s]+(.+)',                              # - @alice: fix the bug
    r'^\s*[-*•]\s+(.+?)\bby\b\s+(\w.*)',                          # - finish report by Friday
    r'^\s*[-*]?\s*\[\s*\]\s+(.+)',                                  # [ ] or - [ ] unchecked checkbox
    r'^\s*(?:\d+\.)\s+(.+?)\bby\b\s+(\w.*)',                      # 1. submit form by Monday
]

# Decision patterns
DECISION_PATTERNS = [
    # Must be at start of line or after a bullet to avoid mid-sentence false positives
    r'(?i)^[-*\s]*(?:decided|agreed|decision[:\s]|we will|team will|resolved to)[:\s-]+(.+)',
    r'(?i)^[-*\s]*(?:decision|agreed|resolved)[:\s]+(.+)',
]

# Attendee patterns
ATTENDEE_PATTERNS = [
    r'(?i)^(?:attendees?|present|participants?|attendees?)[:\s]+(.+)',
    r'(?i)^(?:in attendance)[:\s]+(.+)',
]

# Header/topic patterns (markdown headers or ALL-CAPS lines)
TOPIC_PATTERNS = [
    r'^#{1,3}\s+(.+)',       # ## Agenda
    r'^([A-Z][A-Z\s]{4,}):?\s*$',  # BUDGET REVIEW
]

# Inline date patterns used for extraction
DATE_PATTERN = re.compile(
    r'\b(?:by\s+)?'
    r'(?:'
    r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|'
    r'Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'
    r'\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s+\d{4})?'
    r'|\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?'
    r'|(?:next\s+)?(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)'
    r'|(?:next\s+week|end\s+of\s+(?:week|month|day)|EOW|EOM|EOD)'
    r'|today|tomorrow'
    r')\b',
    re.IGNORECASE,
)

# Owner from @mention or "Name will / Name needs to"
OWNER_PATTERN = re.compile(r'@(\w+)', re.IGNORECASE)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def extract_date(text: str) -> str | None:
    m = DATE_PATTERN.search(text)
    return m.group(0).strip() if m else None


def extract_owner(text: str) -> str | None:
    m = OWNER_PATTERN.search(text)
    if m:
        return m.group(1)
    return None


def clean(text: str) -> str:
    return text.strip().rstrip('.,;')


# ---------------------------------------------------------------------------
# Section extractors
# ---------------------------------------------------------------------------

def extract_action_items(lines: list[str]) -> list[dict]:
    items = []
    seen = set()

    for line in lines:
        for pattern in ACTION_PATTERNS:
            m = re.match(pattern, line, re.IGNORECASE)
            if not m:
                continue

            groups = [g for g in m.groups() if g]
            owner = None
            raw_task = ''

            if len(groups) == 2:
                g0, g1 = groups[0].strip(), groups[1].strip()
                # Case 1: first group is an @mention handle → owner
                at_m = re.match(r'^@?(\w+)$', g0)
                if at_m and g0.startswith('') and re.match(r'^@?\w+$', g0):
                    owner = g0.lstrip('@')
                    raw_task = clean(g1)
                # Case 2: first group is a capitalized name (1–3 words)
                elif re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}$', g0):
                    owner = g0
                    raw_task = clean(g1)
                else:
                    raw_task = clean(g0 + ' ' + g1)
            else:
                raw_task = clean(' '.join(groups))

            # Fallback: extract @mention from the original line
            if not owner:
                owner = extract_owner(line)
                # Remove the @mention from task text if it appears there
                if owner:
                    raw_task = re.sub(r'@' + re.escape(owner) + r'[:\s]*', '', raw_task).strip()

            # Check for "Name will/needs to X" pattern within a single-group task
            if not owner:
                name_will = re.match(
                    r'^(.+?)\s+(?:will|needs? to|should|must|is going to)\s+(.+)',
                    raw_task, re.IGNORECASE
                )
                if name_will:
                    candidate = name_will.group(1).strip()
                    if 1 <= len(candidate.split()) <= 3 and candidate[0].isupper():
                        owner = candidate
                        raw_task = clean(name_will.group(2))

            # Normalize whitespace in task
            raw_task = re.sub(r'\s+', ' ', raw_task).strip()

            if not raw_task or raw_task.lower() in seen:
                continue
            seen.add(raw_task.lower())

            due = extract_date(line)

            items.append({
                'task': raw_task,
                'owner': owner,
                'due': due,
                'raw': line.strip(),
            })
            break  # first matching pattern wins

    return items


def extract_decisions(lines: list[str]) -> list[str]:
    decisions = []
    seen = set()
    for line in lines:
        for pattern in DECISION_PATTERNS:
            m = re.search(pattern, line, re.IGNORECASE)
            if m:
                text = clean(m.group(1))
                if text and text.lower() not in seen:
                    decisions.append(text)
                    seen.add(text.lower())
                break
    return decisions


def extract_attendees(lines: list[str]) -> list[str]:
    attendees = []
    for line in lines:
        for pattern in ATTENDEE_PATTERNS:
            m = re.match(pattern, line, re.IGNORECASE)
            if m:
                raw = m.group(1)
                # Split on commas, semicolons, or "and"
                parts = re.split(r'[,;]|\band\b', raw, flags=re.IGNORECASE)
                for p in parts:
                    p = p.strip().lstrip('@')
                    if p:
                        attendees.append(p)
                break
    # Also collect standalone @mentions as potential attendees
    all_mentions = set()
    for line in lines:
        for m in OWNER_PATTERN.finditer(line):
            all_mentions.add(m.group(1))
    # Only add @mentions not already captured
    existing = {a.lower() for a in attendees}
    for mention in sorted(all_mentions):
        if mention.lower() not in existing:
            attendees.append(mention)
    return attendees


def extract_topics(lines: list[str]) -> list[str]:
    topics = []
    seen = set()
    for line in lines:
        for pattern in TOPIC_PATTERNS:
            m = re.match(pattern, line)
            if m:
                text = clean(m.group(1))
                if text and text.lower() not in seen:
                    topics.append(text)
                    seen.add(text.lower())
                break
    return topics


def extract_meeting_date(lines: list[str]) -> str | None:
    """Look for an explicit meeting date in the first 10 lines."""
    for line in lines[:10]:
        # Date: 2024-03-15 or Date: March 15, 2024
        m = re.search(r'(?i)date[:\s]+(.+)', line)
        if m:
            return clean(m.group(1))
        # ISO date anywhere in a short line
        m = re.search(r'\b(\d{4}-\d{2}-\d{2})\b', line)
        if m:
            return m.group(1)
    return None


def extract_title(lines: list[str]) -> str | None:
    for line in lines[:5]:
        m = re.match(r'^#{1,2}\s+(.+)', line)
        if m:
            return clean(m.group(1))
        # First non-empty, non-metadata line that looks like a title
        stripped = line.strip()
        if stripped and not re.match(r'(?i)^(date|attendees?|present|time)[:\s]', stripped):
            if len(stripped) < 120:
                return stripped
    return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_notes(text: str) -> dict:
    lines = text.splitlines()
    non_empty = [l for l in lines if l.strip()]

    result = {
        'title': extract_title(non_empty),
        'date': extract_meeting_date(non_empty) or date.today().isoformat(),
        'attendees': extract_attendees(non_empty),
        'topics': extract_topics(non_empty),
        'decisions': extract_decisions(non_empty),
        'action_items': extract_action_items(lines),
        'raw': text,
    }
    return result


def main():
    parser = argparse.ArgumentParser(description='Extract structured data from raw meeting notes.')
    parser.add_argument('--file', '-f', help='Path to meeting notes file (default: stdin)')
    parser.add_argument('--pretty', action='store_true', help='Pretty-print JSON output')
    args = parser.parse_args()

    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as fh:
                text = fh.read()
        except FileNotFoundError:
            print(f'Error: file not found: {args.file}', file=sys.stderr)
            sys.exit(1)
        except IOError as e:
            print(f'Error reading file: {e}', file=sys.stderr)
            sys.exit(1)
    else:
        text = sys.stdin.read()

    if not text.strip():
        print('Error: no input provided', file=sys.stderr)
        sys.exit(1)

    data = parse_notes(text)
    indent = 2 if args.pretty else None
    print(json.dumps(data, indent=indent, ensure_ascii=False))


if __name__ == '__main__':
    main()
