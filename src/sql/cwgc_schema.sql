-- ════════════════════════════════════════════════════════════════════════════
-- CWGC enrichment schema
-- ────────────────────────────────────────────────────────────────────────────
-- Adds Commonwealth War Graves Commission data alongside the SDGW soldiers
-- and officers tables WITHOUT modifying them. Follows the polymorphic
-- (record_type, record_id) pattern used by record_annotations.
--
-- Two tables + two views:
--   1. cwgc_records  — one row per CWGC casualty (canonical, immutable
--                      after import; refreshed by re-importing).
--   2. cwgc_match    — links a cwgc_records row to a soldiers/officers
--                      row at a given confidence level. Soft-deletes for
--                      audit trail.
--   3. soldiers_with_cwgc  — convenience view that joins through the
--                            highest-confidence active match.
--   4. officers_with_cwgc  — same for officers.
--
-- IDEMPOTENT: every statement is IF NOT EXISTS, so running this file
-- repeatedly is safe.
-- ════════════════════════════════════════════════════════════════════════════

-- ----------------------------------------------------------------------------
-- 1. cwgc_records
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cwgc_records (
    cwgc_id              INTEGER PRIMARY KEY,        -- CWGC's own Id field
    surname              TEXT NOT NULL,
    forename             TEXT,
    initials             TEXT,
    age_at_death         INTEGER,
    honours              TEXT,
    date_of_death        TEXT,                       -- ISO yyyy-mm-dd
    date_of_death2       TEXT,                       -- range-end if any (East African Carrier Corps etc.)
    rank                 TEXT,
    regiment             TEXT,
    secondary_regiment   TEXT,
    unit                 TEXT,
    secondary_unit       TEXT,
    country_of_service   TEXT,
    service_number       TEXT,
    burial               TEXT,                       -- "Buried" / "Commemorated" descriptor
    cemetery             TEXT,
    grave_ref            TEXT,
    additional_info      TEXT,                       -- free-text — often contains next-of-kin
    cwgc_url             TEXT,                       -- deep link: https://www.cwgc.org/find-records/find-war-dead/casualty/<cwgc_id>
    imported_at          TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_cwgc_records_surname           ON cwgc_records(surname);
CREATE INDEX IF NOT EXISTS idx_cwgc_records_surname_initials  ON cwgc_records(surname, initials);
CREATE INDEX IF NOT EXISTS idx_cwgc_records_service_number    ON cwgc_records(service_number);
CREATE INDEX IF NOT EXISTS idx_cwgc_records_date_of_death     ON cwgc_records(date_of_death);
CREATE INDEX IF NOT EXISTS idx_cwgc_records_surname_dod       ON cwgc_records(surname, date_of_death);
CREATE INDEX IF NOT EXISTS idx_cwgc_records_cemetery          ON cwgc_records(cemetery);

-- ----------------------------------------------------------------------------
-- 2. cwgc_match
-- ----------------------------------------------------------------------------
-- Polymorphic link table. One CWGC record may have multiple candidate
-- matches (medium/low confidence) until the operator confirms one;
-- the unique partial index below keeps active matches unique per pair.
-- The convention is to match by (cwgc_id, record_type, record_id) — i.e.,
-- a CWGC record can link to at most one soldier AND at most one officer
-- simultaneously, but in practice 'soldier' and 'officer' are disjoint.
CREATE TABLE IF NOT EXISTS cwgc_match (
    match_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    cwgc_id      INTEGER NOT NULL,
    record_type  TEXT NOT NULL CHECK(record_type IN ('soldier', 'officer')),
    record_id    INTEGER NOT NULL,
    confidence   TEXT NOT NULL CHECK(confidence IN ('exact', 'high', 'medium', 'low', 'manual', 'rejected')),
    match_reason TEXT,                               -- e.g. 'surname+initials+service_number+date'
    matched_at   TEXT NOT NULL DEFAULT (datetime('now')),
    confirmed_by TEXT,                               -- NULL unless operator confirmed
    is_active    INTEGER NOT NULL DEFAULT 1,         -- 0 = soft-deleted / superseded
    FOREIGN KEY (cwgc_id) REFERENCES cwgc_records(cwgc_id)
);

CREATE INDEX IF NOT EXISTS idx_cwgc_match_record      ON cwgc_match(record_type, record_id);
CREATE INDEX IF NOT EXISTS idx_cwgc_match_cwgc        ON cwgc_match(cwgc_id);
CREATE INDEX IF NOT EXISTS idx_cwgc_match_confidence  ON cwgc_match(confidence);
-- Soft-delete semantics: only one active row per (cwgc_id, record_type, record_id).
-- Rejected/superseded history rows have is_active=0 and don't collide.
CREATE UNIQUE INDEX IF NOT EXISTS idx_cwgc_match_one_active
    ON cwgc_match(cwgc_id, record_type, record_id)
    WHERE is_active = 1;

-- ----------------------------------------------------------------------------
-- 3. soldiers_with_cwgc — convenience view
-- ----------------------------------------------------------------------------
-- Joins through the highest-confidence active match (exact/high/manual).
-- 'medium' and 'low' confidence matches are deliberately NOT exposed here —
-- they require operator confirmation first. Use v_cwgc_match_candidates
-- (below) to see those.
DROP VIEW IF EXISTS soldiers_with_cwgc;
CREATE VIEW soldiers_with_cwgc AS
SELECT
    s.*,
    c.cwgc_id,
    c.cemetery            AS cwgc_cemetery,
    c.grave_ref           AS cwgc_grave_ref,
    c.age_at_death        AS cwgc_age_at_death,
    c.burial              AS cwgc_burial,
    c.country_of_service  AS cwgc_country_of_service,
    c.additional_info     AS cwgc_additional_info,
    c.cwgc_url            AS cwgc_url,
    m.confidence          AS cwgc_match_confidence,
    m.match_reason        AS cwgc_match_reason
FROM soldiers s
LEFT JOIN cwgc_match m
       ON m.record_type = 'soldier'
      AND m.record_id   = s.soldier_id
      AND m.is_active   = 1
      AND m.confidence IN ('exact', 'high', 'manual')
LEFT JOIN cwgc_records c ON c.cwgc_id = m.cwgc_id;

-- ----------------------------------------------------------------------------
-- 4. officers_with_cwgc — convenience view
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS officers_with_cwgc;
CREATE VIEW officers_with_cwgc AS
SELECT
    o.*,
    c.cwgc_id,
    c.cemetery            AS cwgc_cemetery,
    c.grave_ref           AS cwgc_grave_ref,
    c.age_at_death        AS cwgc_age_at_death,
    c.burial              AS cwgc_burial,
    c.country_of_service  AS cwgc_country_of_service,
    c.additional_info     AS cwgc_additional_info,
    c.cwgc_url            AS cwgc_url,
    m.confidence          AS cwgc_match_confidence,
    m.match_reason        AS cwgc_match_reason
FROM officers o
LEFT JOIN cwgc_match m
       ON m.record_type = 'officer'
      AND m.record_id   = o.officer_id
      AND m.is_active   = 1
      AND m.confidence IN ('exact', 'high', 'manual')
LEFT JOIN cwgc_records c ON c.cwgc_id = m.cwgc_id;

-- ----------------------------------------------------------------------------
-- 5. v_cwgc_match_candidates — for operator review UI
-- ----------------------------------------------------------------------------
-- Surfaces unconfirmed medium/low-confidence candidate matches so the
-- operator can review and either promote to 'manual' or set 'rejected'.
DROP VIEW IF EXISTS v_cwgc_match_candidates;
CREATE VIEW v_cwgc_match_candidates AS
SELECT
    m.match_id,
    m.cwgc_id,
    m.record_type,
    m.record_id,
    m.confidence,
    m.match_reason,
    c.surname             AS cwgc_surname,
    c.forename            AS cwgc_forename,
    c.initials            AS cwgc_initials,
    c.service_number      AS cwgc_service_number,
    c.date_of_death       AS cwgc_date_of_death,
    c.regiment            AS cwgc_regiment,
    c.cemetery            AS cwgc_cemetery,
    c.grave_ref           AS cwgc_grave_ref,
    c.cwgc_url
FROM cwgc_match m
JOIN cwgc_records c ON c.cwgc_id = m.cwgc_id
WHERE m.is_active = 1
  AND m.confidence IN ('medium', 'low');

-- ----------------------------------------------------------------------------
-- 6. v_cwgc_unmatched — CWGC casualties with no SDGW counterpart
-- ----------------------------------------------------------------------------
-- ~150-200k records: Indian Labour Corps, Newfoundland, South African, etc.
-- Browsable as a third "Other casualties" tab in the UI.
DROP VIEW IF EXISTS v_cwgc_unmatched;
CREATE VIEW v_cwgc_unmatched AS
SELECT c.*
FROM cwgc_records c
LEFT JOIN cwgc_match m
       ON m.cwgc_id = c.cwgc_id
      AND m.is_active = 1
      AND m.confidence IN ('exact', 'high', 'manual')
WHERE m.match_id IS NULL;
