#!/usr/bin/env python3
"""
Workflow Crystallizer — Report Generator

Generates a markdown report from analysis clusters and suggestions.
Designed to be read by the agent, who then presents relevant findings
to the user.

Usage:
    # Full pipeline
    python3 analyze_patterns.py | python3 generate_suggestions.py | python3 report.py

    # From files
    python3 report.py --clusters clusters.json --suggestions suggestions.json

    # State-based (reads from state.json for history context)
    python3 report.py --clusters clusters.json --suggestions suggestions.json --state-file state.json
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from state import load_state, get_active_suggestions

EMOJI_MAP = {
    "cron": "🔄",
    "skill": "🛠️",
    "workflow": "⚡",
    "monitor": "👁️",
}


def format_report(clusters: list[dict], suggestions: list[dict],
                  state_path: str = None) -> str:
    """Generate a markdown report from clusters and suggestions."""
    state = load_state(state_path) if state_path else {}
    now = datetime.now()

    # Determine data range
    cached_dates = sorted(state.get("event_cache", {}).keys()) if state else []
    total_events = sum(
        len(v) for v in state.get("event_cache", {}).values()
    ) if state else 0

    date_range = ""
    if cached_dates:
        date_range = f"{cached_dates[0]} to {cached_dates[-1]}"
    
    lines = []
    lines.append(f"# Workflow Crystallizer Report — {now.strftime('%Y-%m-%d')}")
    lines.append("")

    if date_range:
        lines.append(
            f"**Data range:** {date_range} "
            f"({len(cached_dates)} days, {total_events} events)"
        )

    # Analysis metadata
    analysis_log = state.get("analysis_log", [])
    if analysis_log:
        latest = analysis_log[-1]
        lines.append(
            f"**Files analyzed this run:** "
            f"{', '.join(latest.get('files_analyzed', [])) or 'none (cached)'}"
        )
    lines.append("")

    # ── New Suggestions ─────────────────────────────────────────────
    if suggestions:
        lines.append(f"## New Suggestions ({len(suggestions)})")
        lines.append("")

        for i, sugg in enumerate(suggestions, 1):
            emoji = EMOJI_MAP.get(sugg.get("type", ""), "📋")
            title = sugg.get("title", "Untitled")
            conf = sugg.get("confidence", 0)
            stype = sugg.get("type", "unknown")

            lines.append(f"### {i}. {emoji} {title}")
            lines.append(f"**Confidence:** {conf:.0%} | **Type:** {stype}")
            if sugg.get("provisional"):
                lines.append("⚠️ *Provisional — limited data available*")
            lines.append("")
            lines.append(sugg.get("description", ""))
            lines.append("")

            # Evidence
            evidence = sugg.get("evidence", "")
            if evidence:
                lines.append("**Evidence:**")
                lines.append(evidence)
                lines.append("")

            # Implementation details
            impl = sugg.get("implementation", {})
            if stype == "cron":
                cron_def = impl.get("cron_definition", {})
                schedule_desc = impl.get("schedule_description", "")
                lines.append(f"**Suggested schedule:** {schedule_desc}")
                lines.append("")
                lines.append("**Ready-to-approve cron definition:**")
                lines.append("```json")
                lines.append(json.dumps(cron_def, indent=2))
                lines.append("```")

            elif stype == "skill":
                skill_draft = impl.get("skill_draft", "")
                lines.append("**Draft SKILL.md:**")
                lines.append("```markdown")
                lines.append(skill_draft)
                lines.append("```")

            elif stype == "workflow":
                prompt = impl.get("suggested_prompt", "")
                components = impl.get("components", [])
                lines.append(f"**Suggested saved prompt:** `{prompt}`")
                if components:
                    lines.append(f"**Key components:** {', '.join(components)}")

            elif stype == "monitor":
                target = impl.get("monitor_target", "")
                freq = impl.get("suggested_frequency", "")
                cron_def = impl.get("cron_definition", {})
                lines.append(f"**Target:** {target}")
                lines.append(f"**Frequency:** {freq}")
                lines.append("")
                lines.append("**Ready-to-approve cron definition:**")
                lines.append("```json")
                lines.append(json.dumps(cron_def, indent=2))
                lines.append("```")

            lines.append("")
            lines.append(f"**To accept:** Update state with `id: {sugg.get('id')}`")
            lines.append(f"**To snooze:** Mark as snoozed (resurfaces in 30 days)")
            lines.append(f"**To reject:** Mark as rejected (won't reappear)")
            lines.append("")
            lines.append("---")
            lines.append("")

    else:
        lines.append("## No New Suggestions")
        lines.append("")
        lines.append("No patterns reached the confidence threshold this run.")
        lines.append("")

    # ── All Detected Patterns ───────────────────────────────────────
    if clusters:
        # Separate above and below threshold
        config = state.get("config", {})
        min_conf = config.get("min_confidence", 0.6)

        above = [c for c in clusters if c["confidence"] >= min_conf]
        below = [c for c in clusters if c["confidence"] < min_conf and c["confidence"] >= 0.2]

        if above:
            lines.append(f"## All Patterns Above Threshold ({len(above)})")
            lines.append("")
            for c in above:
                status = ""
                if c.get("is_project"):
                    status = " *(classified as project, not pattern)*"
                elif c.get("is_formalized"):
                    status = " *(already formalized)*"

                lines.append(
                    f"- **{c['label']}** — confidence {c['confidence']:.0%}, "
                    f"{c['count']} events across {c['unique_days']} days"
                    f"{status}"
                )
                lines.append(
                    f"  Keywords: {', '.join(c.get('top_keywords', [])[:5])}"
                )
                if c.get("has_time_correlation"):
                    lines.append(f"  ⏰ Time-correlated pattern detected")
                if c.get("is_multi_step"):
                    lines.append(f"  📋 Multi-step workflow detected")
            lines.append("")

        if below:
            lines.append(f"## Patterns Below Threshold ({len(below)})")
            lines.append("")
            lines.append(
                "*These patterns were detected but didn't reach the confidence "
                "threshold. They may mature with more data.*"
            )
            lines.append("")
            for c in below:
                lines.append(
                    f"- **{c['label']}** — confidence {c['confidence']:.0%}, "
                    f"{c['count']} events across {c['unique_days']} days"
                )
            lines.append("")

    # ── Previously Suggested ────────────────────────────────────────
    prev = state.get("suggestions", [])
    if prev:
        accepted = [s for s in prev if s.get("status") == "accepted"]
        rejected = [s for s in prev if s.get("status") == "rejected"]
        snoozed = [s for s in prev if s.get("status") == "snoozed"]

        if accepted or rejected or snoozed:
            lines.append("## Previous Suggestions")
            lines.append("")

            if accepted:
                lines.append(f"### ✅ Accepted ({len(accepted)})")
                for s in accepted:
                    lines.append(f"- {s.get('title', '?')} (since {s.get('first_suggested', '?')[:10]})")
                lines.append("")

            if snoozed:
                lines.append(f"### 💤 Snoozed ({len(snoozed)})")
                for s in snoozed:
                    lines.append(
                        f"- {s.get('title', '?')} "
                        f"(until {s.get('snooze_until', '?')[:10]})"
                    )
                lines.append("")

            if rejected:
                lines.append(f"### ❌ Rejected ({len(rejected)})")
                for s in rejected:
                    reason = s.get("rejection_reason", "no reason given")
                    lines.append(f"- {s.get('title', '?')} — {reason}")
                lines.append("")

    # ── Footer ──────────────────────────────────────────────────────
    lines.append("---")
    lines.append(
        f"*Generated by Workflow Crystallizer at "
        f"{now.strftime('%Y-%m-%d %H:%M ET')}*"
    )

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate markdown report from clusters and suggestions"
    )
    parser.add_argument(
        "--clusters",
        default=None,
        help="Path to clusters JSON (default: read from stdin)"
    )
    parser.add_argument(
        "--suggestions",
        default=None,
        help="Path to suggestions JSON"
    )
    parser.add_argument(
        "--state-file",
        default=None,
        help="Path to state.json"
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Write report to file instead of stdout"
    )
    args = parser.parse_args()

    # Read clusters
    if args.clusters:
        with open(args.clusters) as f:
            clusters = json.load(f)
    else:
        # Try reading both clusters and suggestions from stdin (piped)
        data = json.load(sys.stdin)
        # Heuristic: if the data has "confidence" and "events", it's clusters
        # If it has "type" and "implementation", it's suggestions
        if data and isinstance(data, list):
            if "implementation" in (data[0] if data else {}):
                clusters = []
                suggestions_data = data
            else:
                clusters = data
                suggestions_data = []
        else:
            clusters = []
            suggestions_data = []

        if args.suggestions:
            with open(args.suggestions) as f:
                suggestions_data = json.load(f)
        elif 'suggestions_data' not in locals():
            suggestions_data = []

        report = format_report(clusters, suggestions_data, args.state_file)

        if args.output:
            Path(args.output).write_text(report)
            sys.stderr.write(f"Report written to {args.output}\n")
        else:
            print(report)
        return

    # Read suggestions
    suggestions_data = []
    if args.suggestions:
        with open(args.suggestions) as f:
            suggestions_data = json.load(f)

    report = format_report(clusters, suggestions_data, args.state_file)

    if args.output:
        Path(args.output).write_text(report)
        sys.stderr.write(f"Report written to {args.output}\n")
    else:
        print(report)


if __name__ == "__main__":
    main()
