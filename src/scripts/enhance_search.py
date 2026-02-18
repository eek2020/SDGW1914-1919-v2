#!/usr/bin/env python3
"""
Database enhancement script for SDGW 1914-1919.
Adds: regiments table, theatre_of_war lookup, birth/enlistment region classification.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "data" / "sd_2011.db"
REF_SQL = Path(__file__).parent.parent / "reference_data.sql"


def _seed_reference_tables(cur):
    """Seed reference tables from SQL if they don't yet exist in the database."""
    existing = {row[0] for row in cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )}
    needed = {'ref_regiment_names', 'ref_theatre_groups',
              'ref_region_places', 'ref_place_keywords'}
    if needed.issubset(existing):
        count = cur.execute("SELECT COUNT(*) FROM ref_regiment_names").fetchone()[0]
        if count > 0:
            print("   Reference tables already populated, skipping seed.")
            return

    print(f"   Seeding reference tables from {REF_SQL}")
    with open(REF_SQL, encoding='utf-8') as f:
        cur.executescript(f.read())


def _load_regiment_names(cur):
    """Load regiment_id -> name mapping from ref_regiment_names table."""
    return {row[0]: row[1] for row in cur.execute(
        "SELECT regiment_id, name FROM ref_regiment_names"
    )}


def _load_theatre_groups(cur):
    """Load theatre groupings from ref_theatre_groups table.

    Returns dict of {theatre_group: [locations...]} and a flat
    location->group mapping.
    """
    groups = {}      # group -> [locations]
    loc_map = {}     # location -> group
    for loc, grp in cur.execute(
        "SELECT location, theatre_group FROM ref_theatre_groups"
    ):
        groups.setdefault(grp, []).append(loc)
        loc_map[loc] = grp
    return groups, loc_map


def _load_region_places(cur):
    """Load region classification sets from ref_region_places table.

    Returns dicts keyed by country for counties and cities.
    """
    counties = {}    # country -> set of place names
    cities = {}      # country -> set of place names
    for place, country, ptype in cur.execute(
        "SELECT place_name, country, type FROM ref_region_places"
    ):
        if ptype == 'county':
            counties.setdefault(country, set()).add(place)
        elif ptype == 'city':
            cities.setdefault(country, set()).add(place)
    return counties, cities


def _load_place_keywords(cur):
    """Load keyword -> region mapping from ref_place_keywords table."""
    return [(row[0], row[1]) for row in cur.execute(
        "SELECT keyword, region FROM ref_place_keywords"
    )]


def classify_place(place_name, counties, cities, keywords):
    """Classify a birth/enlistment place into a region.

    Args:
        place_name: Raw place string to classify.
        counties: dict of {country: set(county_names)} from ref_region_places.
        cities: dict of {country: set(city_names)} from ref_region_places.
        keywords: list of (keyword, region) tuples from ref_place_keywords.
    """
    if not place_name:
        return 'Unknown'

    place = place_name.upper().strip()

    # Check for comma-separated county suffix
    parts = [p.strip() for p in place.split(',')]
    suffix = parts[-1].strip().rstrip('.') if len(parts) > 1 else ''

    # Check suffix against known counties/cities by country
    for country in ('Scotland', 'Wales', 'Ireland'):
        if suffix in counties.get(country, set()) or suffix in cities.get(country, set()):
            return country
    if suffix in counties.get('England', set()):
        return 'England'

    # Check the main city name
    city = parts[0].strip()
    for country in ('Scotland', 'Wales', 'Ireland'):
        if city in cities.get(country, set()):
            return country

    # Check for country indicators in the full string
    if any(x in place for x in ['SCOTLAND', 'SCOTTISH']):
        return 'Scotland'
    if any(x in place for x in ['WALES', 'WELSH']):
        return 'Wales'
    if any(x in place for x in ['IRELAND', 'IRISH']):
        return 'Ireland'

    # Check keyword-based classification (overseas, europe, etc.)
    for kw, region in keywords:
        if kw in place:
            return region

    # If suffix matches a known English county abbreviation pattern
    if suffix and len(suffix) <= 15:
        if suffix in counties.get('England', set()):
            return 'England'

    # Default: if it has a county suffix we didn't match, likely England
    if len(parts) > 1 and suffix:
        return 'England'

    # Single-word places - default to England as most records are English
    return 'England'


def run_migration():
    """Run the database enhancement migration."""
    print(f"Opening database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    cur = conn.cursor()

    # Seed reference tables if not already present
    print("\n0. Checking reference tables...")
    _seed_reference_tables(cur)
    conn.commit()

    # Load all reference data from database tables
    regiment_names = _load_regiment_names(cur)
    theatre_groups, theatre_loc_map = _load_theatre_groups(cur)
    counties, cities = _load_region_places(cur)
    keywords = _load_place_keywords(cur)
    print(f"   Loaded {len(regiment_names)} regiment names")
    print(f"   Loaded {len(theatre_loc_map)} theatre locations in {len(theatre_groups)} groups")
    print(f"   Loaded {sum(len(v) for v in counties.values())} counties, "
          f"{sum(len(v) for v in cities.values())} cities across "
          f"{len(set(list(counties.keys()) + list(cities.keys())))} countries")
    print(f"   Loaded {len(keywords)} place keywords")

    # ── 1. Create regiments table ──
    print("\n1. Creating regiments table...")
    cur.execute("DROP TABLE IF EXISTS regiments")
    cur.execute("""
        CREATE TABLE regiments (
            regiment_id INTEGER PRIMARY KEY,
            name        TEXT NOT NULL
        )
    """)

    # Get all distinct regiment_ids from the data
    all_reg_ids = set()
    for row in cur.execute("SELECT DISTINCT regiment_id FROM regiment_battalion_sd"):
        if row[0] is not None:
            all_reg_ids.add(int(row[0]))
    for row in cur.execute("SELECT DISTINCT regiment_id FROM soldiers WHERE regiment_id IS NOT NULL"):
        all_reg_ids.add(int(row[0]))
    for row in cur.execute("SELECT DISTINCT regiment_id FROM officers WHERE regiment_id IS NOT NULL"):
        all_reg_ids.add(int(row[0]))

    inserted = 0
    for rid in sorted(all_reg_ids):
        name = regiment_names.get(rid, f"Regiment {rid}")
        cur.execute("INSERT OR IGNORE INTO regiments (regiment_id, name) VALUES (?, ?)",
                     (rid, name))
        inserted += 1
    print(f"   Inserted {inserted} regiment records")

    # ── 2. Create theatre_of_war lookup ──
    print("\n2. Creating theatre_of_war lookup table...")
    cur.execute("DROP TABLE IF EXISTS theatre_of_war")
    cur.execute("""
        CREATE TABLE theatre_of_war (
            location    TEXT PRIMARY KEY,
            theatre_group TEXT NOT NULL
        )
    """)

    inserted = 0
    mapped = set()
    for group, locations in theatre_groups.items():
        for loc in locations:
            cur.execute("INSERT OR IGNORE INTO theatre_of_war (location, theatre_group) VALUES (?, ?)",
                         (loc, group))
            mapped.add(loc)
            inserted += 1

    # Check for unmapped death_locations
    all_locs = [row[0] for row in cur.execute(
        "SELECT DISTINCT death_location FROM soldiers WHERE death_location IS NOT NULL")]
    unmapped = [loc for loc in all_locs if loc not in mapped]
    for loc in unmapped:
        cur.execute("INSERT OR IGNORE INTO theatre_of_war (location, theatre_group) VALUES (?, ?)",
                     (loc, "Other"))
        inserted += 1
        print(f"   WARNING: Unmapped location '{loc}' -> Other")

    print(f"   Inserted {inserted} theatre records")

    # ── 3. Classify birth towns into regions ──
    print("\n3. Creating birth_town_region classification...")
    cur.execute("DROP TABLE IF EXISTS birth_town_region")
    cur.execute("""
        CREATE TABLE birth_town_region (
            birth_town  TEXT PRIMARY KEY,
            region      TEXT NOT NULL
        )
    """)

    towns = cur.execute(
        "SELECT DISTINCT birth_town FROM soldiers WHERE birth_town IS NOT NULL"
    ).fetchall()

    batch = []
    region_counts = {}
    for (town,) in towns:
        region = classify_place(town, counties, cities, keywords)
        batch.append((town, region))
        region_counts[region] = region_counts.get(region, 0) + 1

    cur.executemany("INSERT OR IGNORE INTO birth_town_region (birth_town, region) VALUES (?, ?)", batch)
    print(f"   Classified {len(batch)} birth towns:")
    for r, c in sorted(region_counts.items(), key=lambda x: -x[1]):
        print(f"      {r}: {c:,}")

    # ── 4. Classify enlistment locations into regions ──
    print("\n4. Creating enlistment_region classification...")
    cur.execute("DROP TABLE IF EXISTS enlistment_region")
    cur.execute("""
        CREATE TABLE enlistment_region (
            enlistment_loc TEXT PRIMARY KEY,
            region         TEXT NOT NULL
        )
    """)

    locs = cur.execute(
        "SELECT DISTINCT enlistment_loc FROM soldiers WHERE enlistment_loc IS NOT NULL"
    ).fetchall()

    batch = []
    region_counts = {}
    for (loc,) in locs:
        region = classify_place(loc, counties, cities, keywords)
        batch.append((loc, region))
        region_counts[region] = region_counts.get(region, 0) + 1

    cur.executemany("INSERT OR IGNORE INTO enlistment_region (enlistment_loc, region) VALUES (?, ?)", batch)
    print(f"   Classified {len(batch)} enlistment locations:")
    for r, c in sorted(region_counts.items(), key=lambda x: -x[1]):
        print(f"      {r}: {c:,}")

    # ── 5. Create indexes ──
    print("\n5. Creating indexes...")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_soldiers_regiment ON soldiers(regiment_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_officers_regiment ON officers(regiment_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_soldiers_initials ON soldiers(initials)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_officers_initials ON officers(initials)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_birth_region ON birth_town_region(region)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_enlistment_region ON enlistment_region(region)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_theatre_group ON theatre_of_war(theatre_group)")
    print("   Done")

    conn.commit()
    conn.close()
    print("\nMigration complete!")


if __name__ == "__main__":
    run_migration()
