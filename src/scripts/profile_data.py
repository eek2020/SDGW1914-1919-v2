#!/usr/bin/env python3
"""
Profile exported CSV data to inform multi-parameter search UI design.

Analyzes each field's cardinality, null rates, top values, and value lengths
to determine the best UI control type (dropdown, autocomplete, free text,
date picker) for each searchable parameter.

Usage:
    python src/scripts/profile_data.py [--export-dir DIR] [--output FILE]
"""

import argparse
import csv
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent

# Fields to profile for multi-parameter search, grouped by table
PROFILE_FIELDS = {
    "OFFICERS": [
        "SURNAME", "CHRST_NAME", "INITIALS", "DECORATION",
        "RANK", "RANK_ID", "BAT_ID", "DEATH_DATE", "D_TRUEDATE",
        "ADDNL_TEXT",
    ],
    "SOLDIERS": [
        "SURNAME", "CHRST_NAME", "INITIALS", "NUMBER",
        "RANK", "RANK_ID", "BAT_ID", "BORN_TOWN",
        "ENLST_LOC", "ENLST_PLC", "DEATH_DATE", "D_TRUEDATE",
        "DEATH_LOC", "ADDNL_TEXT",
    ],
    "SD_RANKS": ["Rank Group", "Rank New", "Rank Original"],
    "SD_Battalions": ["Name"],
    "OD_Battalions": ["Name"],
}


def profile_column(values):
    """Profile a single column's values."""
    total = len(values)
    if total == 0:
        return None

    non_empty = [v for v in values if v and v.strip()]
    empty_count = total - len(non_empty)
    null_rate = empty_count / total * 100

    counter = Counter(non_empty)
    unique_count = len(counter)
    cardinality_ratio = unique_count / total * 100 if total > 0 else 0

    lengths = [len(v) for v in non_empty] if non_empty else [0]
    min_len = min(lengths)
    max_len = max(lengths)
    avg_len = sum(lengths) / len(lengths)

    top_20 = counter.most_common(20)

    return {
        "total": total,
        "non_empty": len(non_empty),
        "empty": empty_count,
        "null_rate_pct": null_rate,
        "unique_values": unique_count,
        "cardinality_ratio_pct": cardinality_ratio,
        "min_length": min_len,
        "max_length": max_len,
        "avg_length": avg_len,
        "top_20": top_20,
    }


def suggest_ui_control(field_name, profile):
    """Suggest the best UI control based on field profile."""
    if profile is None:
        return "hidden"

    unique = profile["unique_values"]
    null_rate = profile["null_rate_pct"]
    cardinality = profile["cardinality_ratio_pct"]

    # Date fields
    if "DATE" in field_name.upper() or "TRUEDATE" in field_name.upper():
        return "date_range_picker"

    # Very low cardinality -> dropdown
    if unique <= 50:
        return "dropdown"

    # Low-medium cardinality -> searchable dropdown / autocomplete
    if unique <= 500:
        return "searchable_dropdown"

    # Medium cardinality -> autocomplete with suggestions
    if unique <= 5000:
        return "autocomplete"

    # High cardinality -> free text with search
    return "free_text_search"


def main():
    parser = argparse.ArgumentParser(
        description="Profile SDGW data for multi-parameter search UI"
    )
    parser.add_argument(
        "--export-dir",
        default=str(project_root / "data" / "exports"),
        help="Directory containing CSV exports",
    )
    parser.add_argument(
        "--output",
        default=str(project_root / "data" / "exports" / "DATA_PROFILE.md"),
        help="Output markdown report path",
    )
    args = parser.parse_args()

    export_dir = Path(args.export_dir)

    print("=" * 70)
    print("SDGW 1914-1919 DATA PROFILE FOR MULTI-PARAMETER SEARCH")
    print("=" * 70)

    all_profiles = {}

    for table_name, fields in PROFILE_FIELDS.items():
        csv_file = export_dir / f"{table_name}.csv"
        if not csv_file.exists():
            print(f"\n  SKIP  {table_name} (CSV not found)")
            continue

        print(f"\n  Profiling {table_name}...")

        # Read CSV
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        if not rows:
            print(f"    (empty table)")
            continue

        available_columns = set(rows[0].keys())
        table_profiles = {}

        for field_name in fields:
            if field_name not in available_columns:
                print(f"    SKIP column {field_name} (not in CSV)")
                continue

            values = [row.get(field_name, "") for row in rows]
            profile = profile_column(values)
            table_profiles[field_name] = profile

            if profile:
                ui = suggest_ui_control(field_name, profile)
                print(
                    f"    {field_name:<20s} "
                    f"unique={profile['unique_values']:>8,}  "
                    f"null={profile['null_rate_pct']:>5.1f}%  "
                    f"-> {ui}"
                )

        all_profiles[table_name] = table_profiles

    # Generate markdown report
    report = generate_report(all_profiles)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(f"\nReport written to: {args.output}")
    print("=" * 70)


def generate_report(all_profiles):
    """Generate a markdown report from all profiles."""
    lines = [
        "# SDGW 1914-1919 Data Profile for Multi-Parameter Search",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Purpose",
        "",
        "This report profiles each searchable field to determine the best UI control",
        "for multi-parameter search queries. Fields are analyzed for cardinality,",
        "null rates, and value distributions.",
        "",
        "## UI Control Recommendations",
        "",
        "| UI Control | When to Use | Example Fields |",
        "|---|---|---|",
        "| **dropdown** | <= 50 unique values | Rank Group |",
        "| **searchable_dropdown** | 51-500 unique values | Battalion, Rank |",
        "| **autocomplete** | 501-5000 unique values | Birth Town, Death Location |",
        "| **free_text_search** | > 5000 unique values | Surname, Christian Names |",
        "| **date_range_picker** | Date fields | Death Date |",
        "",
        "---",
        "",
    ]

    # Summary table
    lines.extend([
        "## Field Summary",
        "",
        "| Table | Field | Unique Values | Null Rate | Suggested UI Control |",
        "|---|---|---|---|---|",
    ])

    for table_name, table_profiles in all_profiles.items():
        for field_name, profile in table_profiles.items():
            if profile is None:
                continue
            ui = suggest_ui_control(field_name, profile)
            lines.append(
                f"| {table_name} | {field_name} | "
                f"{profile['unique_values']:,} | "
                f"{profile['null_rate_pct']:.1f}% | "
                f"{ui} |"
            )

    lines.extend(["", "---", ""])

    # Detailed per-table profiles
    for table_name, table_profiles in all_profiles.items():
        lines.extend([f"## {table_name}", ""])

        for field_name, profile in table_profiles.items():
            if profile is None:
                continue

            ui = suggest_ui_control(field_name, profile)
            lines.extend([
                f"### {field_name}",
                "",
                f"- **Total records:** {profile['total']:,}",
                f"- **Non-empty:** {profile['non_empty']:,}",
                f"- **Empty/null:** {profile['empty']:,} ({profile['null_rate_pct']:.1f}%)",
                f"- **Unique values:** {profile['unique_values']:,} "
                f"(cardinality: {profile['cardinality_ratio_pct']:.2f}%)",
                f"- **Value length:** min={profile['min_length']}, "
                f"max={profile['max_length']}, avg={profile['avg_length']:.1f}",
                f"- **Suggested UI control:** `{ui}`",
                "",
            ])

            # Top values
            if profile["top_20"]:
                lines.append("**Top 20 values:**")
                lines.append("")
                lines.append("| Value | Count | % of Total |")
                lines.append("|---|---|---|")
                for val, count in profile["top_20"]:
                    pct = count / profile["total"] * 100
                    display_val = val[:60] + "..." if len(val) > 60 else val
                    display_val = display_val.replace("|", "\\|")
                    lines.append(f"| {display_val} | {count:,} | {pct:.2f}% |")
                lines.append("")

    # Search UI design recommendations
    lines.extend([
        "---",
        "",
        "## Multi-Parameter Search UI Recommendations",
        "",
        "Based on the data profile above, the search UI should include:",
        "",
        "### Primary Search Fields",
        "1. **Surname** (free text) - high cardinality, primary search vector",
        "2. **Christian/First Name** (free text) - high cardinality, refinement",
        "3. **Service Number** (free text) - exact lookup for soldiers",
        "",
        "### Filter Dropdowns",
        "4. **Rank** (searchable dropdown) - medium cardinality from ranks table",
        "5. **Battalion** (searchable dropdown) - medium cardinality from battalions",
        "6. **Rank Group** (dropdown) - low cardinality grouping",
        "",
        "### Location Filters",
        "7. **Birth Town** (autocomplete) - medium-high cardinality",
        "8. **Enlistment Location** (autocomplete) - medium-high cardinality",
        "9. **Death Location** (autocomplete) - medium cardinality",
        "",
        "### Date Filters",
        "10. **Death Date** (date range picker) - allow from/to range",
        "",
        "### Record Type",
        "11. **Officer/Soldier toggle** - binary filter",
        "",
        "### Query Behavior",
        "- All filters are AND-combined (narrowing)",
        "- Empty filters are ignored (show all)",
        "- Case-insensitive text matching",
        "- Partial matching on text fields (LIKE prefix%)",
        "- Exact matching on dropdowns and service number",
        "",
    ])

    return "\n".join(lines)


if __name__ == "__main__":
    main()
