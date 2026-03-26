#!/usr/bin/env python3
"""
format_checklist.py — Output meeting action items as a plain checklist.

Usage:
    python3 extract.py --file notes.txt | python3 format_checklist.py
    python3 extract.py --file notes.txt | python3 format_checklist.py --output checklist.md
    python3 extract.py --file notes.txt | python3 format_checklist.py --no-owners
"""

import argparse
import json
import os
import sys


def format_item(item: dict, show_owners: bool, show_due: bool) -> str:
    parts = []
    if show_owners and item.get('owner'):
        parts.append(f"@{item['owner']}:")
    parts.append(item.get('task', item.get('raw', '(unknown task)')))
    line = ' '.join(parts)
    if show_due and item.get('due'):
        line += f" (due: {item['due']})"
    return f'- [ ] {line}'


def main():
    parser = argparse.ArgumentParser(description='Output meeting action items as a plain checklist.')
    parser.add_argument('--output', '-o', help='Output file path (default: stdout)')
    parser.add_argument('--input', '-i', help='Input JSON file (default: stdin)')
    parser.add_argument('--no-owners', action='store_true', help='Omit owner names')
    parser.add_argument('--no-due', action='store_true', help='Omit due dates')
    parser.add_argument('--plain', action='store_true', help='Plain text (- instead of - [ ])')
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

    action_items = data.get('action_items', [])

    if not action_items:
        output = '_No action items found._\n'
    else:
        output_lines = []
        date_str = data.get('date', '')
        title = data.get('title', 'Meeting Action Items')
        if date_str:
            output_lines.append(f'# {title} — {date_str}')
        else:
            output_lines.append(f'# {title}')
        output_lines.append('')

        for item in action_items:
            line = format_item(item, show_owners=not args.no_owners, show_due=not args.no_due)
            if args.plain:
                line = line.replace('- [ ] ', '- ', 1)
            output_lines.append(line)

        output = '\n'.join(output_lines) + '\n'

    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        try:
            with open(args.output, 'w', encoding='utf-8') as fh:
                fh.write(output)
            print(f'Saved: {args.output}', file=sys.stderr)
        except IOError as e:
            print(f'Error writing file: {e}', file=sys.stderr)
            sys.exit(1)
    else:
        print(output, end='')


if __name__ == '__main__':
    main()
