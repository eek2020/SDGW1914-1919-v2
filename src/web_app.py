#!/usr/bin/env python3
"""
Flask web application for SDGW 1914-1919 Personnel Database
Phase C: Basic UI - Multi-parameter search and record viewing
"""

import sqlite3
from flask import Flask, render_template, request, g, jsonify
from pathlib import Path

app = Flask(__name__)

# Database path
DB_PATH = Path(__file__).parent.parent / "data" / "sd_2011.db"


def get_db():
    """Get database connection for current request"""
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(error):
    """Close database connection at end of request"""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def get_dropdown_data(db):
    """Get data for dropdown filters"""
    # Rank groups
    rank_groups = [row[0] for row in db.execute(
        "SELECT DISTINCT rank_group FROM ranks ORDER BY rank_group"
    )]

    # Ranks - distinct names only (multiple rank_ids map to the same display name)
    ranks = db.execute(
        "SELECT DISTINCT rank_new, rank_group FROM ranks ORDER BY rank_group, rank_new"
    ).fetchall()

    # Battalions
    battalions = db.execute(
        "SELECT battalion_id, name FROM battalions_sd ORDER BY name"
    ).fetchall()

    # Death locations
    death_locations = [row[0] for row in db.execute(
        "SELECT DISTINCT death_location FROM soldiers WHERE death_location IS NOT NULL ORDER BY death_location"
    )]

    return {
        'rank_groups': rank_groups,
        'ranks': ranks,
        'battalions': battalions,
        'death_locations': death_locations
    }


@app.route('/')
def home():
    """Home page with search form"""
    db = get_db()
    dropdown_data = get_dropdown_data(db)
    return render_template('home.html', **dropdown_data)


@app.route('/search')
def search():
    """Search results page"""
    db = get_db()
    dropdown_data = get_dropdown_data(db)

    # Get search parameters
    surname = request.args.get('surname', '').strip()
    christian_names = request.args.get('christian_names', '').strip()
    service_number = request.args.get('service_number', '').strip()
    rank_name = request.args.get('rank_name', '')
    battalion_id = request.args.get('battalion_id', '')
    birth_town = request.args.get('birth_town', '').strip()
    death_location = request.args.get('death_location', '')
    death_date_from = request.args.get('death_date_from', '')
    death_date_to = request.args.get('death_date_to', '')
    record_type = request.args.get('record_type', 'all')

    # Pagination
    page = int(request.args.get('page', 1))
    per_page = 50
    offset = (page - 1) * per_page

    # Common columns for display (aliased consistently across both tables)
    OFFICER_SELECT = """
        o.officer_id AS id, 'officer' AS record_type,
        o.surname, o.christian_names, o.initials, o.decoration,
        o.rank_text, o.death_date, o.additional_text,
        NULL AS service_number, NULL AS birth_town,
        NULL AS enlistment_loc, NULL AS death_location,
        b.name AS battalion_name, r.rank_new, r.rank_group
    """
    SOLDIER_SELECT = """
        s.soldier_id AS id, 'soldier' AS record_type,
        s.surname, s.christian_names, s.initials, NULL AS decoration,
        s.rank_text, s.death_date, s.additional_text,
        s.service_number, s.birth_town,
        s.enlistment_loc, s.death_location,
        b.name AS battalion_name, r.rank_new, r.rank_group
    """
    OFFICER_FROM = """
        officers o
        LEFT JOIN battalions_sd b ON o.battalion_id = b.battalion_id
        LEFT JOIN ranks r ON o.rank_id = r.rank_id
    """
    SOLDIER_FROM = """
        soldiers s
        LEFT JOIN battalions_sd b ON s.battalion_id = b.battalion_id
        LEFT JOIN ranks r ON s.rank_id = r.rank_id
    """

    def build_conditions(table_alias, is_soldier):
        """Build WHERE conditions and params for a given table."""
        conds = []
        params = []
        a = table_alias

        if surname:
            conds.append(f"{a}.surname LIKE ?")
            params.append(f"{surname.upper()}%")
        if christian_names:
            conds.append(f"({a}.christian_names LIKE ? OR {a}.initials LIKE ?)")
            params.append(f"%{christian_names.upper()}%")
            params.append(f"%{christian_names.upper()}%")
        if service_number and is_soldier:
            conds.append(f"{a}.service_number = ?")
            params.append(service_number)
        if rank_name:
            conds.append(f"{a}.rank_id IN (SELECT rank_id FROM ranks WHERE rank_new = ?)")
            params.append(rank_name)
        if battalion_id:
            conds.append(f"{a}.battalion_id = ?")
            params.append(battalion_id)
        if birth_town and is_soldier:
            conds.append(f"{a}.birth_town LIKE ?")
            params.append(f"%{birth_town.upper()}%")
        if death_location and is_soldier:
            conds.append(f"{a}.death_location = ?")
            params.append(death_location)
        if death_date_from:
            conds.append(f"{a}.death_date >= ?")
            params.append(death_date_from)
        if death_date_to:
            conds.append(f"{a}.death_date <= ?")
            params.append(death_date_to)

        where = " AND ".join(conds) if conds else "1=1"
        return where, params

    if record_type == 'officers':
        where, params = build_conditions('o', False)
        query = f"SELECT {OFFICER_SELECT} FROM {OFFICER_FROM} WHERE {where} ORDER BY o.surname, o.christian_names LIMIT ? OFFSET ?"
        count_query = f"SELECT COUNT(*) FROM officers o WHERE {where}"
        results = db.execute(query, params + [per_page, offset]).fetchall()
        total = db.execute(count_query, params).fetchone()[0]

    elif record_type == 'soldiers':
        where, params = build_conditions('s', True)
        query = f"SELECT {SOLDIER_SELECT} FROM {SOLDIER_FROM} WHERE {where} ORDER BY s.surname, s.christian_names LIMIT ? OFFSET ?"
        count_query = f"SELECT COUNT(*) FROM soldiers s WHERE {where}"
        results = db.execute(query, params + [per_page, offset]).fetchall()
        total = db.execute(count_query, params).fetchone()[0]

    else:
        # "all" - UNION query with DB-level pagination
        where_o, params_o = build_conditions('o', False)
        where_s, params_s = build_conditions('s', True)

        query = f"""
            SELECT * FROM (
                SELECT {OFFICER_SELECT} FROM {OFFICER_FROM} WHERE {where_o}
                UNION ALL
                SELECT {SOLDIER_SELECT} FROM {SOLDIER_FROM} WHERE {where_s}
            )
            ORDER BY surname, christian_names
            LIMIT ? OFFSET ?
        """
        count_query = f"""
            SELECT
                (SELECT COUNT(*) FROM officers o WHERE {where_o}) +
                (SELECT COUNT(*) FROM soldiers s WHERE {where_s})
        """
        results = db.execute(query, params_o + params_s + [per_page, offset]).fetchall()
        total = db.execute(count_query, params_o + params_s).fetchone()[0]

    # Calculate pagination
    total_pages = (total + per_page - 1) // per_page
    has_prev = page > 1
    has_next = page < total_pages

    # Preserve search filters for pagination links
    search_params = {k: v for k, v in request.args.items() if k != 'page'}

    return render_template(
        'search_results.html',
        results=results,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_prev=has_prev,
        has_next=has_next,
        search_params=search_params,
        **dropdown_data
    )


def _build_where(table, surname, christian_names, service_number,
                 birth_town, death_date_from, death_date_to):
    """Build WHERE clause using only index-friendly conditions for fast DB scan."""
    conditions = ["1=1"]
    params = []

    if surname:
        conditions.append("surname LIKE ?")
        params.append(f"{surname.upper()}%")
    if christian_names:
        conditions.append("(christian_names LIKE ? OR initials LIKE ?)")
        params.append(f"%{christian_names.upper()}%")
        params.append(f"%{christian_names.upper()}%")
    if service_number and table == 'soldiers':
        conditions.append("service_number = ?")
        params.append(service_number)
    if birth_town and table == 'soldiers':
        conditions.append("birth_town LIKE ?")
        params.append(f"%{birth_town.upper()}%")
    if death_date_from:
        conditions.append("death_date >= ?")
        params.append(death_date_from)
    if death_date_to:
        conditions.append("death_date <= ?")
        params.append(death_date_to)

    return " AND ".join(conditions), params


def _exists_clause(tables, column, conditions_map):
    """Build an EXISTS-based WHERE clause across soldier/officer tables."""
    parts = []
    params = []
    for tbl in tables:
        alias = tbl[0]
        conds, prms = conditions_map(tbl, alias)
        if conds:
            parts.append(
                f"EXISTS (SELECT 1 FROM {tbl} {alias} WHERE {alias}.{column} = x.{column} AND {' AND '.join(conds)})")
            params.extend(prms)
        else:
            parts.append(
                f"EXISTS (SELECT 1 FROM {tbl} {alias} WHERE {alias}.{column} = x.{column})")
    return ' OR '.join(parts), params


def _dropdown_only_options(db, rank_name, battalion_id, death_location,
                           search_soldiers, search_officers):
    """Fast path: only dropdown filters set, use EXISTS on indexed columns."""
    tables = []
    if search_soldiers:
        tables.append('soldiers')
    if search_officers:
        tables.append('officers')

    sel_bat_id = int(battalion_id) if battalion_id else None
    sel_death_loc = death_location if death_location else None
    sel_rank_ids = None
    if rank_name:
        sel_rank_ids = [r[0] for r in db.execute(
            "SELECT rank_id FROM ranks WHERE rank_new = ?", (rank_name,))]

    def rank_conds(tbl, alias):
        c, p = [], []
        if sel_bat_id is not None:
            c.append(f"{alias}.battalion_id = ?"); p.append(sel_bat_id)
        if sel_death_loc and tbl == 'soldiers':
            c.append(f"{alias}.death_location = ?"); p.append(sel_death_loc)
        return c, p

    def bat_conds(tbl, alias):
        c, p = [], []
        if sel_rank_ids:
            ph = ','.join('?' * len(sel_rank_ids))
            c.append(f"{alias}.rank_id IN ({ph})"); p.extend(sel_rank_ids)
        if sel_death_loc and tbl == 'soldiers':
            c.append(f"{alias}.death_location = ?"); p.append(sel_death_loc)
        return c, p

    def dl_conds(tbl, alias):
        c, p = [], []
        if sel_rank_ids:
            ph = ','.join('?' * len(sel_rank_ids))
            c.append(f"{alias}.rank_id IN ({ph})"); p.extend(sel_rank_ids)
        if sel_bat_id is not None:
            c.append(f"{alias}.battalion_id = ?"); p.append(sel_bat_id)
        return c, p

    # Ranks (exclude rank filter from conditions)
    where, params = _exists_clause(tables, 'rank_id', rank_conds)
    ranks = [{'rank_new': r[0], 'rank_group': r[1]} for r in db.execute(
        f"SELECT DISTINCT rank_new, rank_group FROM ranks x WHERE {where} ORDER BY rank_group, rank_new",
        params)] if where else []

    # Battalions (exclude battalion filter)
    where, params = _exists_clause(tables, 'battalion_id', bat_conds)
    battalions = [{'battalion_id': r[0], 'name': r[1]} for r in db.execute(
        f"SELECT battalion_id, name FROM battalions_sd x WHERE {where} ORDER BY name",
        params)] if where else []

    # Death locations (exclude death_location filter, soldiers only)
    death_locs = []
    if search_soldiers:
        c, p = [], []
        if sel_rank_ids:
            ph = ','.join('?' * len(sel_rank_ids))
            c.append(f"rank_id IN ({ph})"); p.extend(sel_rank_ids)
        if sel_bat_id is not None:
            c.append("battalion_id = ?"); p.append(sel_bat_id)
        where = (" AND " + " AND ".join(c)) if c else ""
        death_locs = [r[0] for r in db.execute(
            f"SELECT DISTINCT death_location FROM soldiers WHERE death_location IS NOT NULL{where} ORDER BY death_location",
            p)]

    return ranks, battalions, death_locs


@app.route('/api/surname-suggest')
def surname_suggest():
    """Return distinct surnames matching a prefix for autocomplete."""
    db = get_db()
    q = request.args.get('q', '').strip().upper()
    if len(q) < 2:
        return jsonify([])

    results = db.execute(
        "SELECT surname FROM surname_lookup WHERE surname LIKE ? LIMIT 50",
        (f"{q}%",)
    ).fetchall()

    return jsonify([row[0] for row in results])


@app.route('/api/filter-options')
def filter_options():
    """Return available dropdown options based on current filter selections.

    Two strategies depending on filter type:
    - Text/date filters present: collect distinct combos in one scan, then
      derive dropdown options via Python set operations (fast on narrowed sets).
    - Dropdown-only filters: use EXISTS queries on indexed columns (fast).
    """
    db = get_db()

    surname = request.args.get('surname', '').strip()
    christian_names = request.args.get('christian_names', '').strip()
    service_number = request.args.get('service_number', '').strip()
    rank_name = request.args.get('rank_name', '')
    battalion_id = request.args.get('battalion_id', '')
    birth_town = request.args.get('birth_town', '').strip()
    death_location = request.args.get('death_location', '')
    death_date_from = request.args.get('death_date_from', '')
    death_date_to = request.args.get('death_date_to', '')
    record_type = request.args.get('record_type', 'all')

    has_any_filter = any([surname, christian_names, service_number,
                          rank_name, battalion_id, birth_town,
                          death_location, death_date_from, death_date_to])

    if not has_any_filter:
        return jsonify({'unfiltered': True})

    search_soldiers = record_type in ('all', 'soldiers')
    search_officers = record_type in ('all', 'officers')

    has_text_filter = any([surname, christian_names, service_number,
                           birth_town, death_date_from, death_date_to])

    if not has_text_filter:
        # --- Fast path: dropdown-only filters, use EXISTS on indexed columns ---
        ranks, battalions, death_locs = _dropdown_only_options(
            db, rank_name, battalion_id, death_location,
            search_soldiers, search_officers)
    else:
        # --- Combo-collection path: text filters narrow the set first ---
        combos = []

        if search_soldiers:
            where_s, params_s = _build_where('soldiers', surname, christian_names,
                                              service_number, birth_town,
                                              death_date_from, death_date_to)
            combos.extend(db.execute(
                f"SELECT DISTINCT rank_id, battalion_id, death_location FROM soldiers WHERE {where_s}",
                params_s).fetchall())

        if search_officers:
            where_o, params_o = _build_where('officers', surname, christian_names,
                                              service_number, birth_town,
                                              death_date_from, death_date_to)
            combos.extend(
                (r[0], r[1], None) for r in db.execute(
                    f"SELECT DISTINCT rank_id, battalion_id FROM officers WHERE {where_o}",
                    params_o).fetchall())

        # Pre-resolve selected dropdown values to IDs
        sel_rank_ids = None
        if rank_name:
            sel_rank_ids = set(r[0] for r in db.execute(
                "SELECT rank_id FROM ranks WHERE rank_new = ?", (rank_name,)))

        sel_bat_id = int(battalion_id) if battalion_id else None
        sel_death_loc = death_location if death_location else None

        # Derive each dropdown's options with exclude-self logic
        rank_ids_set = set()
        bat_ids_set = set()
        dlocs_set = set()

        for rid, bid, dl in combos:
            bat_ok = (sel_bat_id is None or bid == sel_bat_id)
            dl_ok = (sel_death_loc is None or dl == sel_death_loc)
            rank_ok = (sel_rank_ids is None or rid in sel_rank_ids)

            if bat_ok and dl_ok and rid is not None:
                rank_ids_set.add(rid)
            if rank_ok and dl_ok and bid is not None:
                bat_ids_set.add(bid)
            if rank_ok and bat_ok and dl is not None:
                dlocs_set.add(dl)

        # Resolve IDs to display names
        ranks = []
        if rank_ids_set:
            ph = ','.join('?' * len(rank_ids_set))
            ranks = [{'rank_new': r[0], 'rank_group': r[1]} for r in db.execute(
                f"SELECT DISTINCT rank_new, rank_group FROM ranks WHERE rank_id IN ({ph}) ORDER BY rank_group, rank_new",
                list(rank_ids_set))]

        battalions = []
        if bat_ids_set:
            ph = ','.join('?' * len(bat_ids_set))
            battalions = [{'battalion_id': r[0], 'name': r[1]} for r in db.execute(
                f"SELECT battalion_id, name FROM battalions_sd WHERE battalion_id IN ({ph}) ORDER BY name",
                list(bat_ids_set))]

        death_locs = sorted(dlocs_set)

    rank_groups = sorted(set(r['rank_group'] for r in ranks))

    return jsonify({
        'unfiltered': False,
        'rank_groups': rank_groups,
        'ranks': ranks,
        'battalions': battalions,
        'death_locations': death_locs
    })


@app.route('/record/<record_type>/<int:record_id>')
def detail(record_type, record_id):
    """Detail view for a single record"""
    db = get_db()

    if record_type == 'officer':
        record = db.execute(
            "SELECT o.*, b.name as battalion_name, r.rank_new, r.rank_group "
            "FROM officers o "
            "LEFT JOIN battalions_sd b ON o.battalion_id = b.battalion_id "
            "LEFT JOIN ranks r ON o.rank_id = r.rank_id "
            "WHERE o.officer_id = ?",
            (record_id,)
        ).fetchone()
    else:
        record = db.execute(
            "SELECT s.*, b.name as battalion_name, r.rank_new, r.rank_group "
            "FROM soldiers s "
            "LEFT JOIN battalions_sd b ON s.battalion_id = b.battalion_id "
            "LEFT JOIN ranks r ON s.rank_id = r.rank_id "
            "WHERE s.soldier_id = ?",
            (record_id,)
        ).fetchone()

    if record is None:
        return "Record not found", 404

    # Related records: same battalion, same death date, same birthplace
    related = {}
    battalion_id = record['battalion_id']
    death_date = record['death_date']
    id_col = 'officer_id' if record_type == 'officer' else 'soldier_id'
    table = 'officers' if record_type == 'officer' else 'soldiers'

    # Same battalion (limit 5)
    if battalion_id:
        related['battalion'] = db.execute(
            f"SELECT {id_col} AS id, surname, christian_names, rank_text, "
            f"'{record_type}' AS record_type "
            f"FROM {table} WHERE battalion_id = ? AND {id_col} != ? "
            f"ORDER BY surname, christian_names LIMIT 5",
            (battalion_id, record_id)
        ).fetchall()

    # Same death date (from both tables, limit 5)
    if death_date:
        same_date = []
        same_date.extend(db.execute(
            "SELECT officer_id AS id, surname, christian_names, rank_text, "
            "'officer' AS record_type FROM officers "
            "WHERE death_date = ? AND NOT (? = 'officer' AND officer_id = ?) "
            "ORDER BY surname LIMIT 5",
            (death_date, record_type, record_id)
        ).fetchall())
        same_date.extend(db.execute(
            "SELECT soldier_id AS id, surname, christian_names, rank_text, "
            "'soldier' AS record_type FROM soldiers "
            "WHERE death_date = ? AND NOT (? = 'soldier' AND soldier_id = ?) "
            "ORDER BY surname LIMIT 5",
            (death_date, record_type, record_id)
        ).fetchall())
        related['death_date'] = same_date[:5]

    # Same birthplace (soldiers only)
    if record_type == 'soldier' and record['birth_town']:
        related['birthplace'] = db.execute(
            "SELECT soldier_id AS id, surname, christian_names, rank_text, "
            "'soldier' AS record_type FROM soldiers "
            "WHERE birth_town = ? AND soldier_id != ? "
            "ORDER BY surname, christian_names LIMIT 5",
            (record['birth_town'], record_id)
        ).fetchall()

    return render_template('detail.html', record=record, record_type=record_type, related=related)


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
