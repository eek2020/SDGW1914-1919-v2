#!/usr/bin/env python3
"""
Flask web application for SDGW 1914-1919 Personnel Database
Phase C: Basic UI - Multi-parameter search and record viewing
"""

import csv
import hashlib
import io
import os
import sqlite3
import threading
import time
from datetime import datetime
from flask import Flask, render_template, request, g, jsonify, url_for, Response, redirect, flash, send_file, make_response
from pathlib import Path
import sys

if getattr(sys, 'frozen', False):
    BUNDLE_DIR = Path(getattr(sys, '_MEIPASS', Path(sys.executable).parent / "_internal"))
    INSTALL_DIR = Path(sys.executable).parent
    TEMPLATE_DIR = BUNDLE_DIR / "templates"
    STATIC_DIR = BUNDLE_DIR / "static"
else:
    sys.path.insert(0, str(Path(__file__).parent))
    HERE = Path(__file__).parent
    INSTALL_DIR = HERE.parent
    TEMPLATE_DIR = HERE / "templates"
    STATIC_DIR = HERE / "static"

from annotations import AnnotationManager

app = Flask(__name__, template_folder=str(TEMPLATE_DIR), static_folder=str(STATIC_DIR))
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-only-fallback-key')

WRITE_PASSPHRASE = os.environ.get('SDGW_WRITE_PASSPHRASE', '')


def _check_write_auth():
    """Check write-access passphrase if one is configured."""
    if WRITE_PASSPHRASE and request.form.get('passphrase') != WRITE_PASSPHRASE:
        flash('Incorrect passphrase.', 'error')
        return False
    return True


def _format_date(value, fmt):
    """Shared date formatting helper."""
    if not value:
        return ''
    try:
        return datetime.strptime(str(value), '%Y-%m-%d').strftime(fmt)
    except (ValueError, TypeError):
        return str(value)


@app.template_filter('humandate')
def human_date(value):
    """Convert ISO date to '5 September 1915' format."""
    return _format_date(value, '%-d %B %Y')


@app.template_filter('humandate_short')
def human_date_short(value):
    """Convert ISO date to '5 Sep 1915' format."""
    return _format_date(value, '%-d %b %Y')


# Database path — INSTALL_DIR is the repo root in dev, the install dir (next to SDGW.exe) when frozen
DB_PATH = INSTALL_DIR / "data" / "sd_2011.db"

# Valid sort options: (label, ORDER BY clause for officers, ORDER BY clause for soldiers, ORDER BY for union)
SORT_OPTIONS = {
    'name_asc':  ('Name (A-Z)', '{a}.surname ASC, {a}.christian_names ASC', 'surname ASC, christian_names ASC'),
    'name_desc': ('Name (Z-A)', '{a}.surname DESC, {a}.christian_names DESC', 'surname DESC, christian_names DESC'),
    'date_asc':  ('Death Date (earliest)', '{a}.death_date ASC, {a}.surname ASC', 'death_date ASC, surname ASC'),
    'date_desc': ('Death Date (latest)', '{a}.death_date DESC, {a}.surname ASC', 'death_date DESC, surname ASC'),
    'rank':      ('Rank', 'r.rank_group ASC, r.rank_new ASC, {a}.surname ASC', 'rank_group ASC, rank_new ASC, surname ASC'),
}
DEFAULT_SORT = 'name_asc'

FILTER_ACTIVE_FIELDS = (
    'surname', 'christian_names', 'initials', 'service_number',
    'rank_name', 'battalion_id', 'regiment_id', 'birth_town',
    'birth_region', 'enlistment_loc', 'enlistment_region', 'decoration',
    'death_location', 'theatre_group', 'death_date_from', 'death_date_to'
)

FILTER_TEXT_SUGGEST_FIELDS = (
    'christian_names', 'initials', 'service_number',
    'birth_town', 'enlistment_loc', 'decoration'
)

FILTER_TEXT_SUGGESTION_LIMIT = 60
FILTER_OPTIONS_CACHE_TTL_SECONDS = 20
FILTER_OPTIONS_CACHE_MAX_ENTRIES = 256
FILTER_OPTIONS_SLOW_LOG_MS = 250
_filter_options_cache = {}
_filter_options_cache_lock = threading.Lock()

RESULTS_PER_PAGE = 20


def get_db():
    """Get database connection for current request"""
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.teardown_appcontext
def close_db(error):
    """Close database connection at end of request"""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def get_dropdown_data(db):
    """Get data for dropdown filters — all fields return group info for optgroups."""
    rank_groups = [row[0] for row in db.execute(
        "SELECT DISTINCT rank_group FROM ranks ORDER BY rank_group"
    )]

    ranks = db.execute(
        "SELECT DISTINCT rank_new, rank_group FROM ranks ORDER BY rank_group, rank_new"
    ).fetchall()

    # Battalions grouped by regiment name
    battalions = db.execute(
        "SELECT bs.battalion_id, bs.name, rg.name AS regiment_name "
        "FROM battalions_sd bs "
        "LEFT JOIN regiment_battalion_sd rb ON rb.battalion_id = bs.battalion_id "
        "LEFT JOIN regiments rg ON rg.regiment_id = rb.regiment_id "
        "ORDER BY COALESCE(rg.name, 'Other'), bs.name"
    ).fetchall()
    battalion_groups = sorted(set(
        (b['regiment_name'] or 'Other') for b in battalions
    ))

    # Death locations grouped by theatre_group
    death_locations = db.execute(
        "SELECT DISTINCT s.death_location, COALESCE(t.theatre_group, 'Other') AS theatre_group "
        "FROM soldiers s "
        "LEFT JOIN theatre_of_war t ON t.location = s.death_location "
        "WHERE s.death_location IS NOT NULL "
        "ORDER BY COALESCE(t.theatre_group, 'Other'), s.death_location"
    ).fetchall()
    death_location_groups = sorted(set(
        row['theatre_group'] for row in death_locations
    ))

    # Regiments grouped by regiment_type
    regiments = db.execute(
        "SELECT regiment_id, name, COALESCE(regiment_type, 'Other') AS regiment_type "
        "FROM regiments ORDER BY regiment_type, name"
    ).fetchall()
    regiment_type_order = ['Guards', 'Cavalry', 'Infantry', 'Artillery & Engineers',
                           'Corps & Services', 'Other']
    regiment_groups = [g for g in regiment_type_order
                       if g in set(r['regiment_type'] for r in regiments)]

    # Theatre of war groups (flat)
    theatre_groups = [row[0] for row in db.execute(
        "SELECT DISTINCT theatre_group FROM theatre_of_war ORDER BY theatre_group"
    )]

    # Birth regions
    birth_regions = [row[0] for row in db.execute(
        "SELECT DISTINCT region FROM birth_town_region ORDER BY region"
    )]

    # Enlistment regions
    enlistment_regions = [row[0] for row in db.execute(
        "SELECT DISTINCT region FROM enlistment_region ORDER BY region"
    )]

    return {
        'rank_groups': rank_groups,
        'ranks': ranks,
        'battalions': battalions,
        'battalion_groups': battalion_groups,
        'death_locations': death_locations,
        'death_location_groups': death_location_groups,
        'regiments': regiments,
        'regiment_groups': regiment_groups,
        'theatre_groups': theatre_groups,
        'birth_regions': birth_regions,
        'enlistment_regions': enlistment_regions,
    }


# ── Shared query building ──────────────────────────────────────────────

OFFICER_SELECT = """
    o.officer_id AS id, 'officer' AS record_type,
    o.surname, o.christian_names, o.initials, o.decoration,
    o.rank_text, o.death_date, o.additional_text,
    NULL AS service_number, NULL AS birth_town,
    NULL AS enlistment_loc, NULL AS death_location,
    b.name AS battalion_name, r.rank_new, r.rank_group,
    rg.name AS regiment_name
"""
SOLDIER_SELECT = """
    s.soldier_id AS id, 'soldier' AS record_type,
    s.surname, s.christian_names, s.initials, NULL AS decoration,
    s.rank_text, s.death_date, s.additional_text,
    s.service_number, s.birth_town,
    s.enlistment_loc, s.death_location,
    b.name AS battalion_name, r.rank_new, r.rank_group,
    rg.name AS regiment_name
"""
OFFICER_FROM = """
    officers o
    LEFT JOIN battalions_sd b ON o.battalion_id = b.battalion_id
    LEFT JOIN ranks r ON o.rank_id = r.rank_id
    LEFT JOIN regiments rg ON CAST(o.regiment_id AS INTEGER) = rg.regiment_id
"""
SOLDIER_FROM = """
    soldiers s
    LEFT JOIN battalions_sd b ON s.battalion_id = b.battalion_id
    LEFT JOIN ranks r ON s.rank_id = r.rank_id
    LEFT JOIN regiments rg ON CAST(s.regiment_id AS INTEGER) = rg.regiment_id
"""


def _parse_search_params(args):
    """Extract search parameters from request args.

    Accepts 'record_type' or 'search_type' (used in detail URLs to avoid
    clashing with the route's record_type parameter).
    """
    return {
        'surname': args.get('surname', '').strip(),
        'christian_names': args.get('christian_names', '').strip(),
        'initials': args.get('initials', '').strip(),
        'service_number': args.get('service_number', '').strip(),
        'rank_name': args.get('rank_name', ''),
        'battalion_id': args.get('battalion_id', ''),
        'regiment_id': args.get('regiment_id', ''),
        'birth_town': args.get('birth_town', '').strip(),
        'birth_region': args.get('birth_region', ''),
        'enlistment_loc': args.get('enlistment_loc', '').strip(),
        'enlistment_region': args.get('enlistment_region', ''),
        'decoration': args.get('decoration', '').strip(),
        'death_location': args.get('death_location', ''),
        'theatre_group': args.get('theatre_group', ''),
        'death_date_from': args.get('death_date_from', ''),
        'death_date_to': args.get('death_date_to', ''),
        'record_type': args.get('search_type', args.get('record_type', 'all')),
        'query_mode': args.get('query_mode', 'and'),
    }


def _build_conditions(params, table_alias, is_soldier):
    """Build WHERE conditions and bound params for a given table.

    Supports query_mode: 'and' (all conditions), 'or' (any condition),
    'not' (exclude matches - inverts the combined condition).
    """
    conds = []
    bound = []
    a = table_alias
    query_mode = params.get('query_mode', 'and')

    if params['surname']:
        conds.append(f"{a}.surname LIKE ?")
        bound.append(f"{params['surname'].upper()}%")
    if params['christian_names']:
        conds.append(f"({a}.christian_names LIKE ? OR {a}.initials LIKE ?)")
        bound.append(f"%{params['christian_names'].upper()}%")
        bound.append(f"%{params['christian_names'].upper()}%")
    if params.get('initials'):
        conds.append(f"{a}.initials LIKE ?")
        bound.append(f"{params['initials'].upper()}%")
    if params['service_number'] and is_soldier:
        conds.append(f"{a}.service_number = ?")
        bound.append(params['service_number'])
    if params['rank_name']:
        conds.append(f"{a}.rank_id IN (SELECT rank_id FROM ranks WHERE rank_new = ?)")
        bound.append(params['rank_name'])
    if params['battalion_id']:
        conds.append(f"{a}.battalion_id = ?")
        bound.append(params['battalion_id'])
    if params.get('regiment_id'):
        conds.append(f"{a}.regiment_id = ?")
        bound.append(params['regiment_id'])
    if params['birth_town'] and is_soldier:
        conds.append(f"{a}.birth_town LIKE ?")
        bound.append(f"%{params['birth_town'].upper()}%")
    if params.get('birth_region') and is_soldier:
        conds.append(f"EXISTS (SELECT 1 FROM birth_town_region _br WHERE _br.birth_town = {a}.birth_town AND _br.region = ?)")
        bound.append(params['birth_region'])
    if params['enlistment_loc'] and is_soldier:
        conds.append(f"{a}.enlistment_loc LIKE ?")
        bound.append(f"%{params['enlistment_loc'].upper()}%")
    if params.get('enlistment_region') and is_soldier:
        conds.append(f"EXISTS (SELECT 1 FROM enlistment_region _er WHERE _er.enlistment_loc = {a}.enlistment_loc AND _er.region = ?)")
        bound.append(params['enlistment_region'])
    if params['decoration'] and not is_soldier:
        conds.append(f"{a}.decoration LIKE ?")
        bound.append(f"%{params['decoration'].upper()}%")
    if params['death_location'] and is_soldier:
        conds.append(f"{a}.death_location = ?")
        bound.append(params['death_location'])
    if params.get('theatre_group') and is_soldier:
        conds.append(f"{a}.death_location IN (SELECT location FROM theatre_of_war WHERE theatre_group = ?)")
        bound.append(params['theatre_group'])
    if params['death_date_from']:
        conds.append(f"{a}.death_date >= ?")
        bound.append(params['death_date_from'])
    if params['death_date_to']:
        conds.append(f"{a}.death_date <= ?")
        bound.append(params['death_date_to'])

    if not conds:
        return "1=1", []

    if query_mode == 'or':
        where = "(" + " OR ".join(conds) + ")"
    elif query_mode == 'not':
        where = "NOT (" + " AND ".join(conds) + ")"
    else:
        where = " AND ".join(conds)

    return where, bound


def _get_order_by(sort_key, alias=None, union=False):
    """Return ORDER BY clause for the given sort key."""
    if sort_key not in SORT_OPTIONS:
        sort_key = DEFAULT_SORT
    _, aliased_order, union_order = SORT_OPTIONS[sort_key]
    if union:
        return union_order
    return aliased_order.format(a=alias or 'x')


def _cache_key_for_params(params):
    """Create a deterministic cache key for filter-option params."""
    return tuple(sorted((k, str(v)) for k, v in params.items() if v))


def _get_cached_filter_payload(cache_key):
    """Return cached filter payload if still fresh."""
    with _filter_options_cache_lock:
        cached = _filter_options_cache.get(cache_key)
        if not cached:
            return None
        cached_at, payload = cached
        if (time.monotonic() - cached_at) > FILTER_OPTIONS_CACHE_TTL_SECONDS:
            _filter_options_cache.pop(cache_key, None)
            return None
        return payload


def _set_cached_filter_payload(cache_key, payload):
    """Store payload in bounded in-memory cache."""
    with _filter_options_cache_lock:
        _filter_options_cache[cache_key] = (time.monotonic(), payload)
        while len(_filter_options_cache) > FILTER_OPTIONS_CACHE_MAX_ENTRIES:
            oldest_key = min(_filter_options_cache, key=lambda k: _filter_options_cache[k][0])
            _filter_options_cache.pop(oldest_key, None)


_SAFE_TEXT_COLUMNS = frozenset(FILTER_TEXT_SUGGEST_FIELDS) | {
    'surname', 'regiment_id', 'battalion_id', 'rank_id'
}


def _collect_distinct_text_values(db, params, field_name, search_officers, search_soldiers,
                                  limit=FILTER_TEXT_SUGGESTION_LIMIT):
    """Collect cascaded distinct values for a text field, excluding that field itself."""
    assert field_name in _SAFE_TEXT_COLUMNS, f"Unsafe column name: {field_name!r}"
    base = dict(params)
    base[field_name] = ''
    values = set()

    if field_name in ('service_number', 'birth_town', 'enlistment_loc'):
        search_officers = False
    if field_name == 'decoration':
        search_soldiers = False

    if search_officers:
        where_o, bound_o = _build_conditions(base, 'o', False)
        rows = db.execute(
            f"SELECT DISTINCT o.{field_name} FROM officers o "
            f"WHERE o.{field_name} IS NOT NULL AND o.{field_name} != '' AND {where_o} "
            f"ORDER BY o.{field_name} LIMIT ?",
            bound_o + [limit]
        ).fetchall()
        values.update(r[0].strip() for r in rows if r[0] and str(r[0]).strip())

    if search_soldiers:
        where_s, bound_s = _build_conditions(base, 's', True)
        rows = db.execute(
            f"SELECT DISTINCT s.{field_name} FROM soldiers s "
            f"WHERE s.{field_name} IS NOT NULL AND s.{field_name} != '' AND {where_s} "
            f"ORDER BY s.{field_name} LIMIT ?",
            bound_s + [limit]
        ).fetchall()
        values.update(r[0].strip() for r in rows if r[0] and str(r[0]).strip())

    return sorted(values, key=lambda v: v.upper())[:limit]


def _collect_cascaded_surnames(db, params, q_prefix, search_officers, search_soldiers, limit=50):
    """Collect surnames constrained by all active filters except surname itself."""
    assert 'surname' in _SAFE_TEXT_COLUMNS, "surname not in safe columns"
    base = dict(params)
    base['surname'] = ''
    values = set()

    if search_officers:
        where_o, bound_o = _build_conditions(base, 'o', False)
        rows = db.execute(
            f"SELECT DISTINCT o.surname FROM officers o "
            f"WHERE o.surname LIKE ? AND {where_o} "
            f"ORDER BY o.surname LIMIT ?",
            [f"{q_prefix}%"] + bound_o + [limit]
        ).fetchall()
        values.update(r[0] for r in rows if r[0])

    if search_soldiers:
        where_s, bound_s = _build_conditions(base, 's', True)
        rows = db.execute(
            f"SELECT DISTINCT s.surname FROM soldiers s "
            f"WHERE s.surname LIKE ? AND {where_s} "
            f"ORDER BY s.surname LIMIT ?",
            [f"{q_prefix}%"] + bound_s + [limit]
        ).fetchall()
        values.update(r[0] for r in rows if r[0])

    return sorted(values)[:limit]


def _collect_death_date_bounds(db, params, search_officers, search_soldiers):
    """Get min/max death_date under current filters, excluding date-range inputs."""
    base = dict(params)
    base['death_date_from'] = ''
    base['death_date_to'] = ''

    mins = []
    maxes = []

    if search_officers:
        where_o, bound_o = _build_conditions(base, 'o', False)
        min_o, max_o = db.execute(
            f"SELECT MIN(o.death_date), MAX(o.death_date) FROM officers o WHERE {where_o}",
            bound_o
        ).fetchone()
        if min_o:
            mins.append(min_o)
        if max_o:
            maxes.append(max_o)

    if search_soldiers:
        where_s, bound_s = _build_conditions(base, 's', True)
        min_s, max_s = db.execute(
            f"SELECT MIN(s.death_date), MAX(s.death_date) FROM soldiers s WHERE {where_s}",
            bound_s
        ).fetchone()
        if min_s:
            mins.append(min_s)
        if max_s:
            maxes.append(max_s)

    return {
        'min': min(mins) if mins else '',
        'max': max(maxes) if maxes else ''
    }


def _empty_text_suggestions():
    """Return an empty text suggestion payload for all text fields."""
    return {field: [] for field in FILTER_TEXT_SUGGEST_FIELDS}


def _collect_text_suggestions(db, params, search_officers, search_soldiers, focused_text_field=''):
    """Collect cascaded text suggestions for one field or all configured text fields."""
    suggestions = _empty_text_suggestions()

    if focused_text_field:
        suggestions[focused_text_field] = _collect_distinct_text_values(
            db, params, focused_text_field, search_officers, search_soldiers
        )
        return suggestions

    for field_name in FILTER_TEXT_SUGGEST_FIELDS:
        suggestions[field_name] = _collect_distinct_text_values(
            db, params, field_name, search_officers, search_soldiers
        )
    return suggestions


def _active_filter_labels(params):
    """Return concise list of active filter keys for logging."""
    active = [k for k in FILTER_ACTIVE_FIELDS if params.get(k)]
    record_type = params.get('record_type', 'all')
    query_mode = params.get('query_mode', 'and')
    if record_type != 'all':
        active.append(f"record_type:{record_type}")
    if query_mode != 'and':
        active.append(f"query_mode:{query_mode}")
    return active


def _is_dropdown_only_filter_request(params):
    """Return True when only dropdown/radio filters are active (no free text/date).

    Broader check than _is_simple_dropdown_only_request: includes regiment_id,
    birth_region, enlistment_region, and theatre_group as dropdown keys.
    Used to select the EXISTS-based fast path in /api/filter-options.
    """
    free_text_keys = (
        'surname', 'christian_names', 'initials',
        'service_number', 'birth_town', 'enlistment_loc', 'decoration'
    )
    date_keys = ('death_date_from', 'death_date_to')
    dropdown_keys = (
        'rank_name', 'battalion_id', 'regiment_id',
        'death_location', 'theatre_group', 'birth_region', 'enlistment_region'
    )

    has_free_text = any(params.get(k) for k in free_text_keys)
    has_date = any(params.get(k) for k in date_keys)
    has_dropdown = any(params.get(k) for k in dropdown_keys) or params.get('record_type', 'all') != 'all'
    return has_dropdown and not has_free_text and not has_date and params.get('query_mode', 'and') == 'and'


def _is_simple_dropdown_only_request(params):
    """Return True when only rank/battalion/location/record-type are active.

    Narrower check than _is_dropdown_only_filter_request: only considers
    rank_name, battalion_id, and death_location as simple keys.
    Used to skip expensive faceting when only basic dropdowns are set.
    """
    simple_keys = {'rank_name', 'battalion_id', 'death_location'}
    for key in FILTER_ACTIVE_FIELDS:
        if key in simple_keys:
            continue
        if params.get(key):
            return False
    return params.get('query_mode', 'and') == 'and'


def _lookup_battalions_by_ids(db, battalion_ids):
    """Shared helper: look up battalion display info by a set of IDs."""
    if not battalion_ids:
        return []
    ph = ','.join('?' * len(battalion_ids))
    return [{'battalion_id': r[0], 'name': r[1], 'regiment_name': r[2] or 'Other'} for r in db.execute(
        f"SELECT bs.battalion_id, bs.name, rg.name AS regiment_name "
        f"FROM battalions_sd bs "
        f"LEFT JOIN regiment_battalion_sd rb ON rb.battalion_id = bs.battalion_id "
        f"LEFT JOIN regiments rg ON rg.regiment_id = rb.regiment_id "
        f"WHERE bs.battalion_id IN ({ph}) "
        f"ORDER BY COALESCE(rg.name, 'Other'), bs.name",
        list(battalion_ids)
    )]


def _collect_distinct_ids(db, params, target_column, clear_keys, search_officers, search_soldiers):
    """Collect distinct IDs for a target column across officer/soldier sets."""
    assert target_column in _SAFE_TEXT_COLUMNS, f"Unsafe column name: {target_column!r}"
    base = dict(params)
    for key in clear_keys:
        base[key] = ''

    values = set()
    if search_officers:
        where_o, bound_o = _build_conditions(base, 'o', False)
        values.update(
            r[0] for r in db.execute(
                f"SELECT DISTINCT o.{target_column} FROM officers o WHERE {where_o}",
                bound_o
            )
            if r[0] is not None
        )
    if search_soldiers:
        where_s, bound_s = _build_conditions(base, 's', True)
        values.update(
            r[0] for r in db.execute(
                f"SELECT DISTINCT s.{target_column} FROM soldiers s WHERE {where_s}",
                bound_s
            )
            if r[0] is not None
        )

    return values


def _run_search(db, params, sort='name_asc', limit=50, offset=0):
    """Execute search and return (results, total, sort_key)."""
    record_type = params['record_type']
    sort_key = sort if sort in SORT_OPTIONS else DEFAULT_SORT

    if record_type == 'officers':
        where, bound = _build_conditions(params, 'o', False)
        order = _get_order_by(sort_key, 'o')
        query = f"SELECT {OFFICER_SELECT} FROM {OFFICER_FROM} WHERE {where} ORDER BY {order} LIMIT ? OFFSET ?"
        count_query = f"SELECT COUNT(*) FROM officers o WHERE {where}"
        results = db.execute(query, bound + [limit, offset]).fetchall()
        total = db.execute(count_query, bound).fetchone()[0]

    elif record_type == 'soldiers':
        where, bound = _build_conditions(params, 's', True)
        order = _get_order_by(sort_key, 's')
        query = f"SELECT {SOLDIER_SELECT} FROM {SOLDIER_FROM} WHERE {where} ORDER BY {order} LIMIT ? OFFSET ?"
        count_query = f"SELECT COUNT(*) FROM soldiers s WHERE {where}"
        results = db.execute(query, bound + [limit, offset]).fetchall()
        total = db.execute(count_query, bound).fetchone()[0]

    else:
        where_o, bound_o = _build_conditions(params, 'o', False)
        where_s, bound_s = _build_conditions(params, 's', True)
        union_order = _get_order_by(sort_key, union=True)

        query = f"""
            SELECT * FROM (
                SELECT {OFFICER_SELECT} FROM {OFFICER_FROM} WHERE {where_o}
                UNION ALL
                SELECT {SOLDIER_SELECT} FROM {SOLDIER_FROM} WHERE {where_s}
            )
            ORDER BY {union_order}
            LIMIT ? OFFSET ?
        """
        count_query = f"""
            SELECT
                (SELECT COUNT(*) FROM officers o WHERE {where_o}) +
                (SELECT COUNT(*) FROM soldiers s WHERE {where_s})
        """
        results = db.execute(query, bound_o + bound_s + [limit, offset]).fetchall()
        total = db.execute(count_query, bound_o + bound_s).fetchone()[0]

    return results, total, sort_key


def _results_filter_options(db, params):
    """Return cascaded options for results quick filters (rank/battalion/regiment)."""
    base = dict(params)
    base['rank_name'] = ''
    base['battalion_id'] = ''
    base['regiment_id'] = ''

    combos = []
    record_type = params.get('record_type', 'all')

    if record_type in ('all', 'officers'):
        where_o, bound_o = _build_conditions(base, 'o', False)
        combos.extend(db.execute(
            f"SELECT DISTINCT o.rank_id, o.battalion_id, CAST(o.regiment_id AS INTEGER) "
            f"FROM officers o WHERE {where_o}",
            bound_o
        ).fetchall())

    if record_type in ('all', 'soldiers'):
        where_s, bound_s = _build_conditions(base, 's', True)
        combos.extend(db.execute(
            f"SELECT DISTINCT s.rank_id, s.battalion_id, CAST(s.regiment_id AS INTEGER) "
            f"FROM soldiers s WHERE {where_s}",
            bound_s
        ).fetchall())

    sel_rank_ids = None
    if params.get('rank_name'):
        sel_rank_ids = set(r[0] for r in db.execute(
            "SELECT rank_id FROM ranks WHERE rank_new = ?", (params['rank_name'],)
        ))

    sel_bat_id = int(params['battalion_id']) if params.get('battalion_id') else None
    sel_reg_id = int(params['regiment_id']) if params.get('regiment_id') else None

    rank_ids_set = set()
    bat_ids_set = set()
    reg_ids_set = set()

    for rid, bid, rgid in combos:
        bat_ok = (sel_bat_id is None or bid == sel_bat_id)
        reg_ok = (sel_reg_id is None or rgid == sel_reg_id)
        rank_ok = (sel_rank_ids is None or rid in sel_rank_ids)

        if bat_ok and reg_ok and rid is not None:
            rank_ids_set.add(rid)
        if rank_ok and reg_ok and bid is not None:
            bat_ids_set.add(bid)
        if rank_ok and bat_ok and rgid is not None:
            reg_ids_set.add(rgid)

    ranks = []
    if rank_ids_set:
        ph = ','.join('?' * len(rank_ids_set))
        ranks = [{'rank_new': r[0], 'rank_group': r[1]} for r in db.execute(
            f"SELECT DISTINCT rank_new, rank_group FROM ranks "
            f"WHERE rank_id IN ({ph}) ORDER BY rank_group, rank_new",
            list(rank_ids_set)
        )]

    battalions = []
    if bat_ids_set:
        ph = ','.join('?' * len(bat_ids_set))
        battalions = [{'battalion_id': r[0], 'name': r[1]} for r in db.execute(
            f"SELECT battalion_id, name FROM battalions_sd "
            f"WHERE battalion_id IN ({ph}) ORDER BY name",
            list(bat_ids_set)
        )]

    regiments = []
    if reg_ids_set:
        ph = ','.join('?' * len(reg_ids_set))
        regiments = [{'regiment_id': r[0], 'name': r[1]} for r in db.execute(
            f"SELECT regiment_id, name FROM regiments "
            f"WHERE regiment_id IN ({ph}) ORDER BY name",
            list(reg_ids_set)
        )]

    return {
        'rank_groups': sorted(set(r['rank_group'] for r in ranks)),
        'ranks': ranks,
        'battalions': battalions,
        'regiments': regiments,
    }


# ── Routes ──────────────────────────────────────────────────────────────

@app.route('/')
def home():
    """Home page with search form"""
    db = get_db()
    dropdown_data = get_dropdown_data(db)
    # Empty search params for form value binding
    q = {k: '' for k in ('surname', 'christian_names', 'initials', 'service_number',
         'rank_name', 'battalion_id', 'regiment_id', 'birth_town', 'birth_region',
         'enlistment_loc', 'enlistment_region', 'decoration', 'death_location',
         'theatre_group', 'death_date_from', 'death_date_to', 'record_type',
         'query_mode')}
    q['record_type'] = 'all'
    q['query_mode'] = 'and'
    return render_template('home.html', q=q, **dropdown_data)


@app.route('/about')
def about():
    """About page with project history and original Access database information"""
    return render_template('about.html')


@app.route('/settings')
def settings():
    """Display settings page for user preferences"""
    return render_template('settings.html')


@app.route('/search')
def search():
    """Search results page"""
    db = get_db()
    dropdown_data = get_dropdown_data(db)

    params = _parse_search_params(request.args)
    sort = request.args.get('sort', DEFAULT_SORT)
    page = max(1, int(request.args.get('page', 1)))
    per_page = RESULTS_PER_PAGE
    offset = (page - 1) * per_page

    results, total, sort_key = _run_search(db, params, sort, per_page, offset)

    total_pages = max(1, (total + per_page - 1) // per_page)
    has_prev = page > 1
    has_next = page < total_pages

    # Preserve search filters for pagination/sort links
    search_params = {k: v for k, v in request.args.items() if k not in ('page', 'sort')}
    # For detail links, rename record_type to avoid clash with url_for route param
    detail_params = {}
    for k, v in search_params.items():
        if k == 'record_type':
            detail_params['search_type'] = v
        else:
            detail_params[k] = v

    # Build human-readable filter summary with remove URLs
    filter_labels = _build_filter_labels(params, db, search_params, sort_key)

    # Build CSV export URL preserving search params
    export_csv_url = url_for('export_csv', sort=sort_key, **search_params)

    quick_filter_data = _results_filter_options(db, params)

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
        detail_params=detail_params,
        q=params,
        sort=sort_key,
        sort_options=SORT_OPTIONS,
        filter_labels=filter_labels,
        export_csv_url=export_csv_url,
        quick_filter_data=quick_filter_data,
        **dropdown_data
    )


def _build_filter_labels(params, db, search_params, sort_key):
    """Return list of (label, value, remove_url) tuples for active search filters."""
    labels = []
    
    def _remove_url(param_to_remove):
        """Build URL with all params except the one to remove."""
        filtered = {k: v for k, v in search_params.items() if k != param_to_remove}
        return url_for('search', **filtered, sort=sort_key, page=1)
    
    if params['surname']:
        labels.append(('Surname', params['surname'], _remove_url('surname')))
    if params['christian_names']:
        labels.append(('First Name', params['christian_names'], _remove_url('christian_names')))
    if params.get('initials'):
        labels.append(('Initials', params['initials'], _remove_url('initials')))
    if params['service_number']:
        labels.append(('Service No.', params['service_number'], _remove_url('service_number')))
    if params['rank_name']:
        labels.append(('Rank', params['rank_name'], _remove_url('rank_name')))
    if params['battalion_id']:
        row = db.execute("SELECT name FROM battalions_sd WHERE battalion_id = ?",
                         (params['battalion_id'],)).fetchone()
        labels.append(('Battalion', row['name'] if row else params['battalion_id'], _remove_url('battalion_id')))
    if params.get('regiment_id'):
        row = db.execute("SELECT name FROM regiments WHERE regiment_id = ?",
                         (params['regiment_id'],)).fetchone()
        labels.append(('Regiment', row['name'] if row else params['regiment_id'], _remove_url('regiment_id')))
    if params['birth_town']:
        labels.append(('Birth Town', params['birth_town'], _remove_url('birth_town')))
    if params.get('birth_region'):
        labels.append(('Born Region', params['birth_region'], _remove_url('birth_region')))
    if params['enlistment_loc']:
        labels.append(('Residence', params['enlistment_loc'], _remove_url('enlistment_loc')))
    if params.get('enlistment_region'):
        labels.append(('Residence Region', params['enlistment_region'], _remove_url('enlistment_region')))
    if params['decoration']:
        labels.append(('Decoration', params['decoration'], _remove_url('decoration')))
    if params['death_location']:
        labels.append(('Theatre of War', params['death_location'], _remove_url('death_location')))
    if params.get('theatre_group'):
        labels.append(('Theatre Group', params['theatre_group'], _remove_url('theatre_group')))
    if params['death_date_from']:
        labels.append(('From', params['death_date_from'], _remove_url('death_date_from')))
    if params['death_date_to']:
        labels.append(('To', params['death_date_to'], _remove_url('death_date_to')))
    if params['record_type'] != 'all':
        labels.append(('Type', params['record_type'].capitalize(), _remove_url('record_type')))
    if params.get('query_mode') and params['query_mode'] != 'and':
        labels.append(('Query', params['query_mode'].upper(), _remove_url('query_mode')))
    return labels


@app.route('/record/<record_type>/<int:record_id>')
def detail(record_type, record_id):
    """Detail view for a single record"""
    db = get_db()

    if record_type == 'officer':
        record = db.execute(
            "SELECT o.*, b.name as battalion_name, r.rank_new, r.rank_group, "
            "rg.name as regiment_name "
            "FROM officers o "
            "LEFT JOIN battalions_sd b ON o.battalion_id = b.battalion_id "
            "LEFT JOIN ranks r ON o.rank_id = r.rank_id "
            "LEFT JOIN regiments rg ON CAST(o.regiment_id AS INTEGER) = rg.regiment_id "
            "WHERE o.officer_id = ?",
            (record_id,)
        ).fetchone()
    else:
        record = db.execute(
            "SELECT s.*, b.name as battalion_name, r.rank_new, r.rank_group, "
            "rg.name as regiment_name "
            "FROM soldiers s "
            "LEFT JOIN battalions_sd b ON s.battalion_id = b.battalion_id "
            "LEFT JOIN ranks r ON s.rank_id = r.rank_id "
            "LEFT JOIN regiments rg ON CAST(s.regiment_id AS INTEGER) = rg.regiment_id "
            "WHERE s.soldier_id = ?",
            (record_id,)
        ).fetchone()

    if record is None:
        return render_template('404.html'), 404

    # Record-by-record navigation within search results
    nav = {}
    pos = request.args.get('pos')
    has_search = any(request.args.get(k) for k in
                     ('surname', 'christian_names', 'initials', 'service_number',
                      'rank_name', 'battalion_id', 'regiment_id', 'birth_town',
                      'birth_region', 'enlistment_loc', 'enlistment_region',
                      'decoration', 'death_location', 'theatre_group',
                      'death_date_from', 'death_date_to', 'search_type'))

    if pos is not None and has_search:
        pos = int(pos)
        search_p = _parse_search_params(request.args)
        sort = request.args.get('sort', DEFAULT_SORT)

        # Get total count
        _, total, _ = _run_search(db, search_p, sort, limit=0, offset=0)
        # We need just the count; re-run with limit 0 won't fetch rows
        # Actually limit=0 returns nothing; get total from count query
        total_for_count = total  # _run_search already gives total

        # Fetch first record (pos = 0)
        if pos > 0:
            first_results, _, _ = _run_search(db, search_p, sort, limit=1, offset=0)
            if first_results:
                r = first_results[0]
                nav['first'] = _detail_url_with_search(r['record_type'], r['id'], 0, request.args)

        # Fetch prev record (pos - 1)
        if pos > 0:
            prev_results, _, _ = _run_search(db, search_p, sort, limit=1, offset=pos - 1)
            if prev_results:
                r = prev_results[0]
                nav['prev'] = _detail_url_with_search(r['record_type'], r['id'], pos - 1, request.args)

        # Fetch next record (pos + 1)
        if pos + 1 < total_for_count:
            next_results, _, _ = _run_search(db, search_p, sort, limit=1, offset=pos + 1)
            if next_results:
                r = next_results[0]
                nav['next'] = _detail_url_with_search(r['record_type'], r['id'], pos + 1, request.args)

        # Fetch last record (pos = total - 1)
        if pos + 1 < total_for_count:
            last_results, _, _ = _run_search(db, search_p, sort, limit=1, offset=total_for_count - 1)
            if last_results:
                r = last_results[0]
                nav['last'] = _detail_url_with_search(r['record_type'], r['id'], total_for_count - 1, request.args)

        nav['pos'] = pos + 1  # 1-based for display
        nav['total'] = total_for_count

    # Build back-to-results URL preserving search params
    back_params = {}
    for k, v in request.args.items():
        if k == 'pos':
            continue
        # Convert search_type back to record_type for the search route
        if k == 'search_type':
            back_params['record_type'] = v
        else:
            back_params[k] = v
    # Determine which results page this record is on
    if pos is not None:
        results_page = (int(pos) // RESULTS_PER_PAGE) + 1
        back_params['page'] = str(results_page)
    nav['back_to_results'] = url_for('search', **back_params) if has_search else None

    # Related records
    related = {}
    bat_id = record['battalion_id']
    death_date = record['death_date']
    id_col = 'officer_id' if record_type == 'officer' else 'soldier_id'
    table = 'officers' if record_type == 'officer' else 'soldiers'

    if bat_id:
        related['battalion'] = db.execute(
            f"SELECT {id_col} AS id, surname, christian_names, rank_text, "
            f"'{record_type}' AS record_type "
            f"FROM {table} WHERE battalion_id = ? AND {id_col} != ? "
            f"ORDER BY surname, christian_names LIMIT 5",
            (bat_id, record_id)
        ).fetchall()

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

    if record_type == 'soldier' and record['birth_town']:
        related['birthplace'] = db.execute(
            "SELECT soldier_id AS id, surname, christian_names, rank_text, "
            "'soldier' AS record_type FROM soldiers "
            "WHERE birth_town = ? AND soldier_id != ? "
            "ORDER BY surname, christian_names LIMIT 5",
            (record['birth_town'], record_id)
        ).fetchall()

    # Get annotations and images
    manager = get_annotation_manager()
    annotation = manager.get_annotation(record_type, record_id)
    images = manager.get_images(record_type, record_id, include_data=False)

    return render_template('detail.html', record=record, record_type=record_type,
                           related=related, nav=nav, annotation=annotation, images=images)


def _detail_url_with_search(rec_type, rec_id, pos, args):
    """Build a detail URL preserving search params and position."""
    params = {}
    for k, v in args.items():
        if k in ('pos', 'page'):
            continue
        # Rename record_type to search_type to avoid route param clash
        if k == 'record_type':
            params['search_type'] = v
        else:
            params[k] = v
    params['pos'] = str(pos)
    return url_for('detail', record_type=rec_type, record_id=rec_id, **params)


# ── CSV Export ──────────────────────────────────────────────────────────

@app.route('/export-csv')
def export_csv():
    """Export current search results as a CSV file (max 10,000 rows)."""
    db = get_db()
    params = _parse_search_params(request.args)
    sort = request.args.get('sort', DEFAULT_SORT)
    max_rows = 10000

    results, total, _ = _run_search(db, params, sort, limit=max_rows, offset=0)

    output = io.StringIO()
    output.write('\ufeff')  # UTF-8 BOM for Excel compatibility
    writer = csv.writer(output)

    writer.writerow([
        'Surname', 'Christian Names', 'Type', 'Rank', 'Battalion',
        'Service Number', 'Date of Death', 'Death Location', 'Birth Town'
    ])

    for r in results:
        death_date = human_date_short(r['death_date']) if r['death_date'] else ''
        writer.writerow([
            r['surname'] or '',
            r['christian_names'] or '',
            r['record_type'].capitalize() if r['record_type'] else '',
            r['rank_new'] or '',
            r['battalion_name'] or '',
            r['service_number'] or '',
            death_date,
            r['death_location'] or '',
            r['birth_town'] or '',
        ])

    filename = f"sdgw_results_{datetime.now().strftime('%Y%m%d')}.csv"
    return Response(
        output.getvalue(),
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )


# ── API endpoints ───────────────────────────────────────────────────────

@app.route('/api/surname-suggest')
def surname_suggest():
    """Return distinct surnames matching a prefix for autocomplete."""
    db = get_db()
    q = request.args.get('q', '').strip().upper()
    if len(q) < 2:
        return jsonify([])

    params = _parse_search_params(request.args)
    record_type = params.get('record_type', 'all')
    search_officers = record_type in ('all', 'officers')
    search_soldiers = record_type in ('all', 'soldiers')

    has_other_filters = any(params[k] for k in FILTER_ACTIVE_FIELDS if k != 'surname') or record_type != 'all'

    if not has_other_filters:
        results = db.execute(
            "SELECT surname FROM surname_lookup WHERE surname LIKE ? LIMIT 50",
            (f"{q}%",)
        ).fetchall()
        return jsonify([row[0] for row in results])

    return jsonify(_collect_cascaded_surnames(db, params, q, search_officers, search_soldiers, limit=50))


@app.route('/api/filter-options')
def filter_options():
    """Return fully cascaded options for all filter dropdowns."""
    db = get_db()
    params = _parse_search_params(request.args)
    request_started = time.perf_counter()
    timing_breakdown = {}

    focused_text_field = request.args.get('focused_text_field', '').strip()
    if focused_text_field not in FILTER_TEXT_SUGGEST_FIELDS:
        focused_text_field = ''

    has_any_filter = any(params[k] for k in FILTER_ACTIVE_FIELDS) or params.get('record_type', 'all') != 'all'

    if not has_any_filter:
        return jsonify({
            'unfiltered': True,
            'text_suggestions': _empty_text_suggestions(),
            'death_date_bounds': {'min': '', 'max': ''}
        })

    cache_params = dict(params)
    if focused_text_field:
        cache_params['focused_text_field'] = focused_text_field
    cache_key = _cache_key_for_params(cache_params)
    cached_payload = _get_cached_filter_payload(cache_key)
    if cached_payload is not None:
        return jsonify(cached_payload)

    record_type = params.get('record_type', 'all')
    search_officers = record_type in ('all', 'officers')
    search_soldiers = record_type in ('all', 'soldiers')
    dropdown_only_request = _is_dropdown_only_filter_request(params)

    def _base_with_cleared(*keys):
        base = dict(params)
        for key in keys:
            base[key] = ''
        return base

    death_locations = []
    theatre_groups = []
    birth_regions = []
    enlistment_regions = []

    facet_started = time.perf_counter()
    if _is_simple_dropdown_only_request(params):
        ranks, battalions, death_locations = _dropdown_only_options(
            db,
            params.get('rank_name', ''),
            params.get('battalion_id', ''),
            params.get('death_location', ''),
            search_soldiers,
            search_officers,
        )
        rank_groups = sorted(set(r['rank_group'] for r in ranks))

        regiment_ids = _collect_distinct_ids(
            db, params, 'regiment_id', ['regiment_id'], search_officers, search_soldiers
        )
        regiments = []
        if regiment_ids:
            normalized_regiment_ids = sorted({int(rid) for rid in regiment_ids if str(rid).strip()})
            if normalized_regiment_ids:
                ph = ','.join('?' * len(normalized_regiment_ids))
                regiments = [{'regiment_id': r[0], 'name': r[1], 'regiment_type': r[2] or 'Other'} for r in db.execute(
                    f"SELECT regiment_id, name, COALESCE(regiment_type, 'Other') AS regiment_type FROM regiments WHERE regiment_id IN ({ph}) ORDER BY regiment_type, name",
                    normalized_regiment_ids
                )]
    else:
        rank_ids = _collect_distinct_ids(
            db, params, 'rank_id', ['rank_name'], search_officers, search_soldiers
        )
        battalion_ids = _collect_distinct_ids(
            db, params, 'battalion_id', ['battalion_id'], search_officers, search_soldiers
        )
        regiment_ids = _collect_distinct_ids(
            db, params, 'regiment_id', ['regiment_id'], search_officers, search_soldiers
        )

        ranks = []
        if rank_ids:
            ph = ','.join('?' * len(rank_ids))
            ranks = [{'rank_new': r[0], 'rank_group': r[1]} for r in db.execute(
                f"SELECT DISTINCT rank_new, rank_group FROM ranks WHERE rank_id IN ({ph}) ORDER BY rank_group, rank_new",
                list(rank_ids)
            )]

        battalions = _lookup_battalions_by_ids(db, battalion_ids)

        regiments = []
        if regiment_ids:
            normalized_regiment_ids = sorted({int(rid) for rid in regiment_ids if str(rid).strip()})
            if normalized_regiment_ids:
                ph = ','.join('?' * len(normalized_regiment_ids))
                regiments = [{'regiment_id': r[0], 'name': r[1], 'regiment_type': r[2] or 'Other'} for r in db.execute(
                    f"SELECT regiment_id, name, COALESCE(regiment_type, 'Other') AS regiment_type FROM regiments WHERE regiment_id IN ({ph}) ORDER BY regiment_type, name",
                    normalized_regiment_ids
                )]

        rank_groups = sorted(set(r['rank_group'] for r in ranks))
    timing_breakdown['rank_bat_reg_ms'] = round((time.perf_counter() - facet_started) * 1000, 1)

    if search_soldiers:
        soldier_facet_started = time.perf_counter()
        if not death_locations:
            base_dl = _base_with_cleared('death_location')
            where_dl, bound_dl = _build_conditions(base_dl, 's', True)
            death_locations = [{'location': r[0], 'theatre_group': r[1] or 'Other'} for r in db.execute(
                f"SELECT t.location, COALESCE(t.theatre_group, 'Other') AS theatre_group "
                f"FROM theatre_of_war t "
                f"WHERE EXISTS ("
                f"  SELECT 1 FROM soldiers s WHERE s.death_location = t.location AND {where_dl}"
                f") ORDER BY COALESCE(t.theatre_group, 'Other'), t.location",
                bound_dl
            )]

        base_tg = _base_with_cleared('theatre_group')
        where_tg, bound_tg = _build_conditions(base_tg, 's', True)
        theatre_groups = [r[0] for r in db.execute(
            f"SELECT DISTINCT t.theatre_group FROM theatre_of_war t "
            f"WHERE t.theatre_group IS NOT NULL AND EXISTS ("
            f"  SELECT 1 FROM soldiers s WHERE s.death_location = t.location AND {where_tg}"
            f") ORDER BY t.theatre_group",
            bound_tg
        )]

        # Regions have only 5 values and ~99% of records match, so skip
        # expensive cascading — always show all regions.
        birth_regions = [r[0] for r in db.execute(
            "SELECT DISTINCT region FROM birth_town_region ORDER BY region"
        )]
        enlistment_regions = [r[0] for r in db.execute(
            "SELECT DISTINCT region FROM enlistment_region ORDER BY region"
        )]
        timing_breakdown['soldier_facets_ms'] = round((time.perf_counter() - soldier_facet_started) * 1000, 1)

    text_started = time.perf_counter()
    if focused_text_field:
        text_suggestions = _collect_text_suggestions(
            db, params, search_officers, search_soldiers, focused_text_field
        )
    else:
        text_suggestions = _empty_text_suggestions()
    timing_breakdown['text_suggestions_ms'] = round((time.perf_counter() - text_started) * 1000, 1)

    date_started = time.perf_counter()
    death_date_bounds = _collect_death_date_bounds(db, params, search_officers, search_soldiers)
    timing_breakdown['date_bounds_ms'] = round((time.perf_counter() - date_started) * 1000, 1)

    # Compute group lists from filtered data
    battalion_groups = sorted(set(b.get('regiment_name', 'Other') for b in battalions)) if battalions and isinstance(battalions[0], dict) else []
    death_location_groups = sorted(set(d.get('theatre_group', 'Other') for d in death_locations)) if death_locations and isinstance(death_locations[0], dict) else []
    _rtype_order = ['Guards', 'Cavalry', 'Infantry', 'Artillery & Engineers', 'Corps & Services', 'Other']
    regiment_type_set = set(r.get('regiment_type', 'Other') for r in regiments) if regiments and isinstance(regiments[0], dict) else set()
    regiment_groups = [g for g in _rtype_order if g in regiment_type_set]

    payload = {
        'unfiltered': False,
        'rank_groups': rank_groups,
        'ranks': ranks,
        'battalions': battalions,
        'battalion_groups': battalion_groups,
        'regiments': regiments,
        'regiment_groups': regiment_groups,
        'death_locations': death_locations,
        'death_location_groups': death_location_groups,
        'theatre_groups': theatre_groups,
        'birth_regions': birth_regions,
        'enlistment_regions': enlistment_regions,
        'text_suggestions': text_suggestions,
        'death_date_bounds': death_date_bounds,
    }

    total_ms = round((time.perf_counter() - request_started) * 1000, 1)
    timing_breakdown['total_ms'] = total_ms
    if total_ms >= FILTER_OPTIONS_SLOW_LOG_MS:
        app.logger.info(
            "slow /api/filter-options %.1fms active=%s focused=%s dropdown_only=%s breakdown=%s",
            total_ms,
            ','.join(_active_filter_labels(params)) or 'none',
            focused_text_field or '-',
            dropdown_only_request,
            timing_breakdown,
        )

    _set_cached_filter_payload(cache_key, payload)
    return jsonify(payload)


@app.route('/api/results-filter-options')
def results_filter_options():
    """Return cascaded quick-filter options for the search results page."""
    db = get_db()
    params = _parse_search_params(request.args)
    return jsonify(_results_filter_options(db, params))


@app.route('/api/fuzzy-suggest')
def fuzzy_suggest():
    """Return fuzzy / approximate matches for a text field when exact prefix fails.

    Query params:
      field  – one of the supported text fields
      q      – user query (min 2 chars)
      limit  – max results (default 30)

    Returns JSON: { exact: [...], fuzzy: [...] }
    Each item is { value, group? }
    """
    db = get_db()
    field = request.args.get('field', '').strip()
    q = request.args.get('q', '').strip().upper()
    limit = min(int(request.args.get('limit', 30)), 100)

    ALLOWED_FIELDS = {
        'surname': ('soldiers', 'officers'),
        'christian_names': ('soldiers', 'officers'),
        'initials': ('soldiers', 'officers'),
        'service_number': ('soldiers',),
        'birth_town': ('soldiers',),
        'enlistment_loc': ('soldiers',),
        'decoration': ('officers',),
    }

    if field not in ALLOWED_FIELDS or len(q) < 2:
        return jsonify({'exact': [], 'fuzzy': []})

    tables = ALLOWED_FIELDS[field]
    exact = set()
    fuzzy = set()

    # Exact prefix match
    for tbl in tables:
        rows = db.execute(
            f"SELECT DISTINCT {field} FROM {tbl} "
            f"WHERE {field} LIKE ? AND {field} IS NOT NULL AND {field} != '' "
            f"ORDER BY {field} LIMIT ?",
            (f"{q}%", limit)
        ).fetchall()
        exact.update(r[0].strip() for r in rows if r[0] and r[0].strip())

    # If exact matches are few, try fuzzy strategies
    if len(exact) < limit:
        remaining = limit - len(exact)

        # Strategy 1: Contains match (not just prefix)
        for tbl in tables:
            rows = db.execute(
                f"SELECT DISTINCT {field} FROM {tbl} "
                f"WHERE {field} LIKE ? AND {field} NOT LIKE ? "
                f"AND {field} IS NOT NULL AND {field} != '' "
                f"ORDER BY {field} LIMIT ?",
                (f"%{q}%", f"{q}%", remaining)
            ).fetchall()
            fuzzy.update(r[0].strip() for r in rows if r[0] and r[0].strip())

        # Strategy 2: Character transposition / off-by-one
        if len(q) >= 3 and len(exact) + len(fuzzy) < 5:
            for i in range(len(q) - 1):
                swapped = q[:i] + q[i+1] + q[i] + q[i+2:]
                for tbl in tables:
                    rows = db.execute(
                        f"SELECT DISTINCT {field} FROM {tbl} "
                        f"WHERE {field} LIKE ? AND {field} IS NOT NULL AND {field} != '' "
                        f"ORDER BY {field} LIMIT ?",
                        (f"{swapped}%", remaining)
                    ).fetchall()
                    fuzzy.update(r[0].strip() for r in rows if r[0] and r[0].strip())

        # Strategy 3: Wildcard per character (handles single-char typos)
        if len(q) >= 3 and len(exact) + len(fuzzy) < 5:
            for i in range(len(q)):
                pattern = q[:i] + '_' + q[i+1:] + '%'
                for tbl in tables:
                    rows = db.execute(
                        f"SELECT DISTINCT {field} FROM {tbl} "
                        f"WHERE {field} LIKE ? AND {field} IS NOT NULL AND {field} != '' "
                        f"ORDER BY {field} LIMIT ?",
                        (pattern, remaining)
                    ).fetchall()
                    fuzzy.update(r[0].strip() for r in rows if r[0] and r[0].strip())

    # Remove exact matches from fuzzy set
    fuzzy -= exact

    # Add group info for fields that have it
    def _with_group(values, field_name):
        if field_name == 'birth_town':
            sorted_vals = sorted(values)
            if not sorted_vals:
                return []
            ph = ','.join('?' * len(sorted_vals))
            region_map = {
                r[0]: r[1] for r in db.execute(
                    f"SELECT birth_town, region FROM birth_town_region WHERE birth_town IN ({ph})",
                    sorted_vals
                )
            }
            return [{'value': v, 'group': region_map.get(v, 'Other')} for v in sorted_vals]
        elif field_name == 'enlistment_loc':
            sorted_vals = sorted(values)
            if not sorted_vals:
                return []
            ph = ','.join('?' * len(sorted_vals))
            region_map = {
                r[0]: r[1] for r in db.execute(
                    f"SELECT enlistment_loc, region FROM enlistment_region WHERE enlistment_loc IN ({ph})",
                    sorted_vals
                )
            }
            return [{'value': v, 'group': region_map.get(v, 'Other')} for v in sorted_vals]
        return [{'value': v} for v in sorted(values)]

    return jsonify({
        'exact': _with_group(exact, field)[:limit],
        'fuzzy': _with_group(fuzzy, field)[:limit],
    })


# ── Internal helpers for filter-options ─────────────────────────────────


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

    where, params = _exists_clause(tables, 'rank_id', rank_conds)
    ranks = [{'rank_new': r[0], 'rank_group': r[1]} for r in db.execute(
        f"SELECT DISTINCT rank_new, rank_group FROM ranks x WHERE {where} ORDER BY rank_group, rank_new",
        params)] if where else []

    where, params = _exists_clause(tables, 'battalion_id', bat_conds)
    battalions = [{'battalion_id': r[0], 'name': r[1], 'regiment_name': r[2] or 'Other'} for r in db.execute(
        f"SELECT x.battalion_id, x.name, rg.name AS regiment_name "
        f"FROM battalions_sd x "
        f"LEFT JOIN regiment_battalion_sd rb ON rb.battalion_id = x.battalion_id "
        f"LEFT JOIN regiments rg ON rg.regiment_id = rb.regiment_id "
        f"WHERE {where} ORDER BY COALESCE(rg.name, 'Other'), x.name",
        params)] if where else []

    death_locs = []
    if search_soldiers:
        c, p = [], []
        if sel_rank_ids:
            ph = ','.join('?' * len(sel_rank_ids))
            c.append(f"rank_id IN ({ph})"); p.extend(sel_rank_ids)
        if sel_bat_id is not None:
            c.append("battalion_id = ?"); p.append(sel_bat_id)
        where = (" AND " + " AND ".join(c)) if c else ""
        death_locs = [{'location': r[0], 'theatre_group': r[1] or 'Other'} for r in db.execute(
            f"SELECT DISTINCT s.death_location, COALESCE(t.theatre_group, 'Other') AS theatre_group "
            f"FROM soldiers s "
            f"LEFT JOIN theatre_of_war t ON t.location = s.death_location "
            f"WHERE s.death_location IS NOT NULL{where} "
            f"ORDER BY COALESCE(t.theatre_group, 'Other'), s.death_location",
            p)]

    return ranks, battalions, death_locs


# ── Annotation & Image Management Routes ────────────────────────────────────

def get_annotation_manager():
    """Get AnnotationManager instance."""
    if 'annotation_manager' not in g:
        g.annotation_manager = AnnotationManager(DB_PATH)
    return g.annotation_manager


ANNOTATION_FORM_FIELDS = (
    'additional_names', 'birth_date', 'birth_place_detail', 'family_info',
    'pre_war_occupation', 'enlistment_details', 'service_notes',
    'casualty_details', 'burial_memorial', 'medals_honors',
    'personal_effects', 'newspaper_mentions', 'family_stories',
    'research_notes', 'sources',
)


def _annotation_fields_from_form():
    """Extract annotation fields from the current request form."""
    return {f: request.form.get(f) for f in ANNOTATION_FORM_FIELDS}


@app.route('/record/<record_type>/<int:record_id>/annotation', methods=['GET', 'POST'])
def manage_annotation(record_type, record_id):
    """View or edit annotation for a record."""
    manager = get_annotation_manager()
    
    if request.method == 'POST':
        if not _check_write_auth():
            return redirect(url_for('detail', record_type=record_type, record_id=record_id))
        
        # User confirmation check
        confirmed = request.form.get('confirmed')
        if confirmed != 'yes':
            flash('You must confirm before making changes.', 'error')
            return redirect(url_for('detail', record_type=record_type, record_id=record_id))
        
        user_name = request.form.get('user_name', 'Anonymous')
        action = request.form.get('action')
        
        try:
            if action == 'create':
                fields = _annotation_fields_from_form()
                
                annotation_id = manager.create_annotation(record_type, record_id, user_name, fields)
                flash(f'Annotation created successfully! (ID: {annotation_id})', 'success')
                
            elif action == 'update':
                annotation_id = int(request.form.get('annotation_id'))
                change_reason = request.form.get('change_reason')
                fields = _annotation_fields_from_form()
                
                manager.update_annotation(annotation_id, user_name, fields, change_reason)
                flash('Annotation updated successfully!', 'success')
                
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
        
        return redirect(url_for('detail', record_type=record_type, record_id=record_id))
    
    # GET request - show annotation form
    annotation = manager.get_annotation(record_type, record_id)
    history = manager.get_annotation_history(annotation['annotation_id']) if annotation else []
    
    return render_template('annotation_form.html', 
                         record_type=record_type, 
                         record_id=record_id,
                         annotation=annotation,
                         history=history)


@app.route('/record/<record_type>/<int:record_id>/upload-image', methods=['POST'])
def upload_image(record_type, record_id):
    """Upload image for a record."""
    manager = get_annotation_manager()
    
    if not _check_write_auth():
        return redirect(url_for('detail', record_type=record_type, record_id=record_id))
    
    # User confirmation check
    confirmed = request.form.get('confirmed')
    if confirmed != 'yes':
        flash('You must confirm before uploading images.', 'error')
        return redirect(url_for('detail', record_type=record_type, record_id=record_id))
    
    user_name = request.form.get('user_name', 'Anonymous')
    
    if 'image_file' not in request.files:
        flash('No image file provided.', 'error')
        return redirect(url_for('detail', record_type=record_type, record_id=record_id))
    
    file = request.files['image_file']
    if file.filename == '':
        flash('No file selected.', 'error')
        return redirect(url_for('detail', record_type=record_type, record_id=record_id))
    
    try:
        image_data = file.read()
        
        metadata = {
            'title': request.form.get('image_title'),
            'description': request.form.get('image_description'),
            'image_category': request.form.get('image_category', 'other'),
            'date_taken': request.form.get('date_taken'),
            'location': request.form.get('image_location'),
            'photographer': request.form.get('photographer'),
            'source': request.form.get('image_source'),
            'copyright_info': request.form.get('copyright_info'),
        }
        
        image_id = manager.upload_image(record_type, record_id, image_data, user_name, metadata)
        flash(f'Image uploaded successfully! (ID: {image_id})', 'success')
        
    except Exception as e:
        flash(f'Error uploading image: {str(e)}', 'error')
    
    return redirect(url_for('detail', record_type=record_type, record_id=record_id))


@app.route('/image/<int:image_id>')
def serve_image(image_id):
    """Serve an image by ID."""
    manager = get_annotation_manager()
    
    try:
        image = manager.get_image(image_id)
        if not image:
            return "Image not found", 404
        
        etag = hashlib.md5(image['image_data']).hexdigest()
        if request.headers.get('If-None-Match') == etag:
            return '', 304
        resp = make_response(image['image_data'])
        resp.headers['Content-Type'] = image['image_type']
        resp.headers['ETag'] = etag
        resp.headers['Cache-Control'] = 'public, max-age=86400'
        return resp
    except Exception as e:
        return f"Error: {str(e)}", 500


@app.route('/image/<int:image_id>/delete', methods=['POST'])
def delete_image(image_id):
    """Delete an image."""
    manager = get_annotation_manager()
    
    if not _check_write_auth():
        return redirect(request.referrer or url_for('home'))
    
    confirmed = request.form.get('confirmed')
    if confirmed != 'yes':
        flash('You must confirm before deleting images.', 'error')
        return redirect(request.referrer or url_for('home'))
    
    user_name = request.form.get('user_name', 'Anonymous')
    
    try:
        manager.delete_image(image_id, user_name)
        flash('Image deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting image: {str(e)}', 'error')
    
    return redirect(request.referrer or url_for('home'))


@app.route('/image/<int:image_id>/set-primary', methods=['POST'])
def set_primary_image(image_id):
    """Set image as primary for the record."""
    manager = get_annotation_manager()
    
    try:
        manager.set_primary_image(image_id)
        flash('Primary image updated!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(request.referrer or url_for('home'))


@app.route('/api/annotations/stats')
def annotation_stats():
    """Get annotation and image statistics."""
    manager = get_annotation_manager()
    stats = manager.get_statistics()
    return jsonify(stats)


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5001)
