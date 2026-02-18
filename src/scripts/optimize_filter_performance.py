#!/usr/bin/env python3
"""Apply performance indexes for cascaded filter queries."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "data" / "sd_2011.db"

INDEX_STATEMENTS = [
    # Core text + equality filters
    "CREATE INDEX IF NOT EXISTS idx_officers_initials_fast ON officers(initials)",
    "CREATE INDEX IF NOT EXISTS idx_soldiers_initials_fast ON soldiers(initials)",
    "CREATE INDEX IF NOT EXISTS idx_officers_regiment_fast ON officers(regiment_id)",
    "CREATE INDEX IF NOT EXISTS idx_soldiers_regiment_fast ON soldiers(regiment_id)",
    # Date range + type filter fanout
    "CREATE INDEX IF NOT EXISTS idx_officers_death_date_rank ON officers(death_date, rank_id)",
    "CREATE INDEX IF NOT EXISTS idx_soldiers_death_date_rank ON soldiers(death_date, rank_id)",
    "CREATE INDEX IF NOT EXISTS idx_soldiers_death_date_location ON soldiers(death_date, death_location)",
    # Region/theatre lookup acceleration
    "CREATE INDEX IF NOT EXISTS idx_theatre_location_group ON theatre_of_war(location, theatre_group)",
    "CREATE INDEX IF NOT EXISTS idx_birth_town_region_pair ON birth_town_region(region, birth_town)",
    "CREATE INDEX IF NOT EXISTS idx_enlistment_region_pair ON enlistment_region(region, enlistment_loc)",
    # Covering indexes for DISTINCT + MIN/MAX on filtered queries
    "CREATE INDEX IF NOT EXISTS idx_soldiers_surname_death_date ON soldiers(surname, death_date)",
    "CREATE INDEX IF NOT EXISTS idx_soldiers_surname_regiment ON soldiers(surname, regiment_id)",
]


def run():
    print(f"Opening database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    print("Creating filter-performance indexes...")
    for stmt in INDEX_STATEMENTS:
        cur.execute(stmt)

    print("Running ANALYZE to refresh query planner stats...")
    cur.execute("ANALYZE")

    conn.commit()
    conn.close()
    print("Done.")


if __name__ == "__main__":
    run()
