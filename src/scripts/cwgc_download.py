"""
CWGC Batch Downloader (v4 — date x surname, depth-safe)

Why v4 exists
-------------
v1 used Playwright + direct exports. CWGC tightened things in mid-2026:

    * Exports now require a per-session ``v=<32-hex>`` token harvested from
      the search-results page first.
    * The export response is hard-capped at ~1,000 rows; ``Page`` is ignored.
    * The ``Surname=`` parameter is a strict prefix only up to length 2.
      At length 3 it becomes typo-tolerant; at length 4+ it is purely
      fuzzy, returning the same fallback set of "nearest" surnames for
      any unrecognised string. Recursing beyond depth 2 produces
      duplicate-laden garbage files.

Strategy
~~~~~~~~
This version slices on two dimensions and never lets the surname prefix
exceed length 2:

    1. Outer loop: iterate the configured date range in **monthly buckets**.
    2. For each month, try ``Surname=""``.
    3. If the response is capped (>= 1,000 rows), recurse on each of
       A-Z. Depth 1 captures most. Anywhere capped at depth 1, recurse
       to depth 2 (AA-AZ, BA-BZ ...). Anywhere capped at depth 2,
       split that (month, prefix) pair into **daily buckets** and retry.
    4. Save each leaf result as ``cwgc_<YYYYMM>_<prefix or ALL>.csv``
       (or ``cwgc_<YYYYMMDD>_<prefix>.csv`` when day-split).
    5. Final merge step deduplicates by ``Id`` and writes
       ``data/cwgc_all.csv``.

Filenames don't collide and runs are resumable: existing files are
skipped.

Usage
-----
::

    pip3 install requests
    # full run:
    python3 src/scripts/cwgc_download.py
    # bounded test:
    python3 src/scripts/cwgc_download.py --from 1914-08-01 --to 1914-12-31
    # probe one date range only:
    python3 src/scripts/cwgc_download.py --probe --from 1916-07-01 --to 1916-07-31
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CAP_THRESHOLD = 1000      # exports return at most ~1002 rows; treat >=1000 as capped
MAX_SAFE_PREFIX = 2       # surname prefix length above which CWGC turns fuzzy
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

START_DATE = date(1914, 8, 1)
END_DATE = date(1921, 8, 31)

BASE_URL = "https://www.cwgc.org"
SEARCH_RESULTS_PATH = "/find-records/find-war-dead/search-results/"
EXPORT_PATH = "/ExportCasualtySearch"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

BASE_PARAMS = {
    "Surname": "",
    "Forename": "",
    "Initials": "",
    "ServiceNum": "",
    "Regiment": "",
    "ServedIn": "Army",
    "WarSelect": "1",
    "CountryCommemoratedIn": "null",
    "Cemetery": "",
    "Unit": "",
    "Rank": "",
    "SecondaryRegiment": "",
    "SecondaryUnit": "",
    "AgeOfDeath": "0",
    "DateOfDeath": "",
    "Honours": "null",
    "AdditionalInfo": "",
    "Tab": "all",
    "Size": "100",
    "Sort": "surname",
    "Page": "1",
}

TOKEN_REGEX = re.compile(r"v=([a-f0-9]{32})", re.IGNORECASE)
CHALLENGE_MARKERS = ("recaptcha/api2", "challenge-platform", "Just a moment", "Are you human")


# ---------------------------------------------------------------------------
# HTTP layer
# ---------------------------------------------------------------------------


@dataclass
class Throttle:
    base_seconds: float

    def wait(self):
        if self.base_seconds > 0:
            time.sleep(self.base_seconds)


def fresh_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": USER_AGENT,
        "Accept-Language": "en-GB,en;q=0.9",
    })
    return s


def looks_like_challenge(text: str) -> bool:
    body = text[:5000]
    return any(m in body for m in CHALLENGE_MARKERS)


def build_search_params(from_date: date, to_date: date, surname: str) -> dict[str, str]:
    p = dict(BASE_PARAMS)
    p["DateDeathFromDay"] = str(from_date.day)
    p["DateDeathFromMonth"] = MONTHS[from_date.month - 1]
    p["DateDeathFromYear"] = str(from_date.year)
    p["DateDeathToDay"] = str(to_date.day)
    p["DateDeathToMonth"] = MONTHS[to_date.month - 1]
    p["DateDeathToYear"] = str(to_date.year)
    p["Surname"] = surname
    return p


def resilient_get(
    session: requests.Session,
    url: str,
    log,
    *,
    params: dict | None = None,
    timeout: int = 30,
    max_attempts: int = 4,
    initial_backoff: float = 5.0,
) -> requests.Response | None:
    """GET wrapper with retry on transient network errors.

    Retries on ReadTimeout, ConnectionError, ChunkedEncodingError and 5xx
    responses other than 500 (500 has business meaning for the export
    endpoint: empty bucket).
    """
    backoff = initial_backoff
    last_err: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            resp = session.get(url, params=params, timeout=timeout, allow_redirects=True)
            # 500 is meaningful (empty bucket); pass it back to the caller.
            # 502/503/504 are transient gateway issues; retry.
            if resp.status_code in (502, 503, 504):
                log(f"    transient HTTP {resp.status_code} (attempt {attempt}/{max_attempts})")
                last_err = RuntimeError(f"HTTP {resp.status_code}")
            else:
                return resp
        except (requests.exceptions.ReadTimeout,
                requests.exceptions.ConnectionError,
                requests.exceptions.ChunkedEncodingError) as e:
            last_err = e
            log(f"    transient {type(e).__name__} (attempt {attempt}/{max_attempts}): {e}")
        if attempt < max_attempts:
            time.sleep(backoff)
            backoff *= 2
    log(f"    GIVING UP after {max_attempts} attempts: {last_err}")
    return None


def fetch_token(session: requests.Session, params: dict[str, str], log) -> str | None:
    resp = resilient_get(session, BASE_URL + SEARCH_RESULTS_PATH, log, params=params, timeout=30)
    if resp is None:
        return None
    if resp.status_code != 200:
        log(f"    token fetch HTTP {resp.status_code}")
        return None
    if looks_like_challenge(resp.text):
        log("    challenge/captcha page on search-results")
        return None
    m = TOKEN_REGEX.search(resp.text)
    return m.group(1) if m else None


def download_export(
    session: requests.Session,
    params: dict[str, str],
    out_file: Path,
    log,
) -> int:
    """Return row count. -1 on error. -2 on captcha/challenge.

    Behaviours observed in the wild (May 2026):
      * HTTP 500 from /ExportCasualtySearch == zero exact matches for the
        Surname prefix in the given date range. CWGC's search UI shows a
        "DID YOU MEAN..." suggestion in this case; the export endpoint
        simply fails. We treat this as 0 rows and move on.
      * Token fetch + CSV response succeeded with fuzzy fallback content
        at prefix depth >=3. validate_prefix_match() catches that.
    """
    token = fetch_token(session, params, log)
    if token is None:
        log("    rotating session and retrying token fetch")
        session.cookies.clear()
        token = fetch_token(session, params, log)
        if token is None:
            return -1

    p = dict(params); p["v"] = token
    resp = resilient_get(session, BASE_URL + EXPORT_PATH, log, params=p, timeout=120)
    if resp is None:
        return -1
    if resp.status_code == 500:
        # CWGC returns 500 when the search has zero exact matches. Confirmed
        # via UI: the "NO SEARCH RESULTS" page is shown with a fuzzy hint.
        log(f"    export HTTP 500 -> empty bucket (0 rows)")
        return 0
    if resp.status_code != 200:
        log(f"    export HTTP {resp.status_code}")
        return -1
    ct = resp.headers.get("content-type", "").lower()
    if "csv" not in ct:
        if looks_like_challenge(resp.text):
            log("    challenge page returned in place of CSV")
            return -2
        log(f"    unexpected content-type {ct!r}")
        return -1

    out_file.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_file.with_suffix(".csv.part")
    tmp.write_bytes(resp.content)
    rows = count_csv_rows(tmp)

    # Defensive: reject fuzzy fallback content. At surname-prefix depth 1-2
    # CWGC is a clean prefix matcher; if the surnames we got back don't
    # actually start with our prefix, the CSV is fuzzy garbage.
    prefix = params.get("Surname", "").strip().upper()
    if rows > 0 and 0 < len(prefix) <= MAX_SAFE_PREFIX:
        if not validate_prefix_match(tmp, prefix):
            log(f"    REJECTED fuzzy fallback for prefix {prefix!r} ({rows} non-matching rows)")
            tmp.unlink(missing_ok=True)
            return 0

    tmp.replace(out_file)
    return rows


def validate_prefix_match(csv_path: Path, prefix: str, sample: int = 10) -> bool:
    """Return True if at least one surname in the first ``sample`` rows
    starts with ``prefix``. CWGC returns sorted results so if even the
    sample doesn't contain the prefix we know it's a fuzzy fallback.
    """
    try:
        with csv_path.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i >= sample:
                    break
                surname = (row.get("Surname") or "").strip().upper()
                if surname.startswith(prefix):
                    return True
    except Exception:
        return False
    return False


def count_csv_rows(path: Path) -> int:
    try:
        with path.open(newline="", encoding="utf-8-sig") as f:
            return sum(1 for _ in csv.reader(f)) - 1
    except Exception:
        return 0


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------


def month_ranges(start: date, end: date):
    cur = date(start.year, start.month, 1)
    while cur <= end:
        if cur.month == 12:
            nxt = date(cur.year + 1, 1, 1)
        else:
            nxt = date(cur.year, cur.month + 1, 1)
        m_end = min(nxt - timedelta(days=1), end)
        yield max(cur, start), m_end
        cur = nxt


def day_ranges(start: date, end: date):
    d = start
    while d <= end:
        yield d, d
        d += timedelta(days=1)


def label_range(from_date: date, to_date: date) -> str:
    if from_date == to_date:
        return from_date.strftime("%Y%m%d")
    if from_date.day == 1 and (to_date + timedelta(days=1)).month != to_date.month:
        return from_date.strftime("%Y%m")
    return f"{from_date.strftime('%Y%m%d')}-{to_date.strftime('%Y%m%d')}"


# ---------------------------------------------------------------------------
# Slicer
# ---------------------------------------------------------------------------


def slice_filename(date_label: str, prefix: str) -> str:
    return f"cwgc_{date_label}_{prefix or 'ALL'}.csv"


def fetch_one(
    session: requests.Session,
    from_date: date,
    to_date: date,
    prefix: str,
    output_dir: Path,
    throttle: Throttle,
    log,
    state: dict,
) -> int:
    """Download (or skip if exists) a single (date-range, prefix) combo.

    Returns the row count, or -1 on error, or -2 on captcha.
    """
    d_label = label_range(from_date, to_date)
    fn = slice_filename(d_label, prefix)
    out_file = output_dir / fn
    if out_file.exists():
        rows = count_csv_rows(out_file)
        log(f"  SKIP exists ({rows:,} rows): {fn}")
        state["skipped"] += 1
        return rows

    log(f"  Exporting {d_label} prefix={prefix!r} ...")
    params = build_search_params(from_date, to_date, prefix)
    rows = download_export(session, params, out_file, log)
    throttle.wait()
    if rows == -2:
        state["challenges"] += 1
        log("  CHALLENGE — pausing 60s and rotating session")
        time.sleep(60)
        session.cookies.clear()
        return rows
    if rows == -1:
        state["errors"] += 1
        state["failed"].append(fn)
        return rows
    if rows == 0:
        state["empty"] += 1
        log(f"  -> 0 rows (empty bucket)")
        return rows
    state["downloads"] += 1
    state["rows"] += rows
    log(f"  -> {rows:,} rows  [{fn}]")
    return rows


def slice_date_range(
    session: requests.Session,
    from_date: date,
    to_date: date,
    output_dir: Path,
    throttle: Throttle,
    log,
    state: dict,
) -> None:
    """Cover one date range using safe-depth surname slicing.

    Algorithm:
      1. Try empty surname.
      2. If capped, fan out to depth-1 (A-Z) on the same date range.
      3. Any depth-1 still capped -> fan out to depth-2 on the same range.
      4. Any depth-2 still capped -> recursively slice by day on the same prefix.
    """
    # 1. Empty surname
    rows = fetch_one(session, from_date, to_date, "", output_dir, throttle, log, state)
    if rows < CAP_THRESHOLD:
        return

    # 2. depth-1
    capped_d1: list[str] = []
    for ch in ALPHABET:
        rows = fetch_one(session, from_date, to_date, ch, output_dir, throttle, log, state)
        if rows >= CAP_THRESHOLD:
            capped_d1.append(ch)
    if not capped_d1:
        return

    # 3. depth-2 for every capped depth-1
    capped_d2: list[str] = []
    for p1 in capped_d1:
        log(f"  Depth-1 {p1!r} capped; fanning to depth-2...")
        for ch in ALPHABET:
            p2 = p1 + ch
            rows = fetch_one(session, from_date, to_date, p2, output_dir, throttle, log, state)
            if rows >= CAP_THRESHOLD:
                capped_d2.append(p2)
    if not capped_d2:
        return

    # 4. Day-split fallback for any depth-2 still capped.
    #    For each capped prefix, walk days and re-issue the depth-2 query.
    for p2 in capped_d2:
        log(f"  Depth-2 {p2!r} still capped; splitting by day on this prefix...")
        for day_from, day_to in day_ranges(from_date, to_date):
            rows = fetch_one(session, day_from, day_to, p2, output_dir, throttle, log, state)
            if rows >= CAP_THRESHOLD:
                log(f"    WARNING: day {day_from.isoformat()} prefix {p2!r} STILL capped — manual review needed")
                state["uncovered"].append(f"{day_from.isoformat()}|{p2}")


# ---------------------------------------------------------------------------
# Merge
# ---------------------------------------------------------------------------


def merge_csvs(input_dir: Path, output_file: Path, log) -> int:
    log(f"\nMerging CSVs from {input_dir} -> {output_file}")
    seen_ids: set[str] = set()
    total = 0
    csv_files = sorted(input_dir.glob("cwgc_*.csv"))
    log(f"  Found {len(csv_files)} batch files")

    output_file.parent.mkdir(parents=True, exist_ok=True)
    writer = None
    with output_file.open("w", newline="", encoding="utf-8") as out_f:
        for csv_file in csv_files:
            try:
                with csv_file.open(newline="", encoding="utf-8-sig") as in_f:
                    reader = csv.DictReader(in_f)
                    if writer is None:
                        header = [h for h in (reader.fieldnames or []) if h is not None]
                        writer = csv.DictWriter(out_f, fieldnames=header)
                        writer.writeheader()
                    for row in reader:
                        row = {k: v for k, v in row.items() if k is not None}
                        rec_id = row.get("Id", "")
                        if rec_id and rec_id in seen_ids:
                            continue
                        seen_ids.add(rec_id)
                        writer.writerow(row)
                        total += 1
            except Exception as e:
                log(f"  WARNING: could not read {csv_file.name}: {e}")
    log(f"  Merged {total:,} unique records -> {output_file}")
    return total


# ---------------------------------------------------------------------------
# Probe
# ---------------------------------------------------------------------------


def probe(start_date: date, end_date: date, log) -> None:
    s = fresh_session()
    params = build_search_params(start_date, end_date, "")
    log(f"Probing {start_date} -> {end_date} (empty surname)...")
    token = fetch_token(s, params, log)
    if not token:
        log("  no token"); return
    p = dict(params); p["v"] = token
    ex = s.get(BASE_URL + EXPORT_PATH, params=p, timeout=60)
    log(f"  export HTTP {ex.status_code}, content-type={ex.headers.get('content-type','?')}, body={len(ex.content)} bytes")
    if "csv" in ex.headers.get("content-type", "").lower():
        rows = ex.text.count("\n") - 1
        log(f"  rows in single export: {rows}  (cap is ~{CAP_THRESHOLD})")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_iso_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def main():
    parser = argparse.ArgumentParser(description="CWGC downloader (date x surname, depth-safe)")
    parser.add_argument("--output-dir", default="data/cwgc_batches")
    parser.add_argument("--merge-output", default="data/cwgc_all.csv")
    parser.add_argument("--from", dest="from_date", default=START_DATE.isoformat())
    parser.add_argument("--to", dest="to_date", default=END_DATE.isoformat())
    parser.add_argument("--throttle", type=float, default=2.0)
    parser.add_argument("--skip-merge", action="store_true")
    parser.add_argument("--probe", action="store_true")
    args = parser.parse_args()

    start_date = parse_iso_date(args.from_date)
    end_date = parse_iso_date(args.to_date)
    if start_date > end_date:
        sys.exit("--from must be on or before --to")

    project_root = Path(__file__).parent.parent.parent
    output_dir = project_root / args.output_dir
    merge_output = project_root / args.merge_output

    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "cwgc_download.log"

    def log(msg: str):
        stamped = f"[{datetime.now().isoformat(timespec='seconds')}] {msg}"
        print(stamped)
        with log_file.open("a", encoding="utf-8") as f:
            f.write(stamped + "\n")

    log("=" * 60)
    log("=== CWGC Download (v4 date x surname) started ===")
    log(f"Date range: {start_date} -> {end_date}")
    log(f"Throttle: {args.throttle}s")
    log(f"Output: {output_dir}")

    if args.probe:
        probe(start_date, end_date, log)
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    session = fresh_session()
    state: dict = {
        "downloads": 0, "skipped": 0, "empty": 0, "errors": 0, "challenges": 0,
        "rows": 0, "failed": [], "uncovered": [],
    }

    months = list(month_ranges(start_date, end_date))
    log(f"Iterating {len(months)} month-buckets")
    for i, (m_start, m_end) in enumerate(months, 1):
        log(f"\n[{i}/{len(months)}] Month {m_start.strftime('%Y-%m')} ({m_start} -> {m_end})")
        try:
            slice_date_range(session, m_start, m_end, output_dir,
                             Throttle(args.throttle), log, state)
        except Exception as e:
            log(f"  UNCAUGHT exception while processing month {m_start.strftime('%Y-%m')}: {type(e).__name__}: {e}")
            log("  continuing with next month; this one will be re-attempted on next run")
            state["errors"] += 1
            # try to recover the session
            try:
                session.cookies.clear()
            except Exception:
                pass

    log("\n=== Run summary ===")
    log(f"  downloads : {state['downloads']:,}")
    log(f"  empty     : {state['empty']:,}  (HTTP 500 = no records for prefix in range)")
    log(f"  skipped   : {state['skipped']:,}")
    log(f"  errors    : {state['errors']:,}")
    log(f"  challenges: {state['challenges']:,}")
    log(f"  rows raw  : {state['rows']:,}  (before dedupe)")
    if state["failed"]:
        log("  failed files:")
        for fn in state["failed"]:
            log(f"    - {fn}")
    if state["uncovered"]:
        log("  uncovered (day+prefix still capped at depth 2):")
        for u in state["uncovered"]:
            log(f"    - {u}")

    if not args.skip_merge:
        merge_csvs(output_dir, merge_output, log)

    log("=== Done ===")
    sys.exit(0 if not state["errors"] else 2)


if __name__ == "__main__":
    main()
