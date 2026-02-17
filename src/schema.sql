-- SDGW 1914-1919 Personnel Database Schema
-- Phase B: Data Migration
-- Designed for multi-parameter search queries

PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- ============================================================
-- Reference Tables
-- ============================================================

CREATE TABLE IF NOT EXISTS ranks (
    rank_id       INTEGER PRIMARY KEY,
    new_rank_id   INTEGER,
    rank_group    TEXT NOT NULL,          -- e.g. "Privates", "Officers" (4 values -> dropdown)
    rank_new      TEXT NOT NULL,          -- Normalized name e.g. "Armourer" (114 values -> searchable dropdown)
    rank_original TEXT NOT NULL,          -- Original e.g. "ARMR./PTE." (539 values)
    my_rank_id    INTEGER
);

CREATE TABLE IF NOT EXISTS battalions_sd (
    battalion_id  INTEGER PRIMARY KEY,
    name          TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS battalions_od (
    battalion_id  INTEGER PRIMARY KEY,
    name          TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS regiment_battalion_sd (
    regiment_id   INTEGER NOT NULL,
    battalion_id  INTEGER NOT NULL,
    sort_order    REAL,
    PRIMARY KEY (regiment_id, battalion_id),
    FOREIGN KEY (battalion_id) REFERENCES battalions_sd(battalion_id)
);

CREATE TABLE IF NOT EXISTS regiment_battalion_od (
    regiment_id   INTEGER NOT NULL,
    battalion_id  INTEGER NOT NULL,
    sort_order    REAL,
    PRIMARY KEY (regiment_id, battalion_id),
    FOREIGN KEY (battalion_id) REFERENCES battalions_od(battalion_id)
);

-- ============================================================
-- Personnel Tables
-- ============================================================

CREATE TABLE IF NOT EXISTS officers (
    officer_id      INTEGER PRIMARY KEY,
    reg_sort        REAL,
    regiment_id     REAL,
    battalion_id    INTEGER NOT NULL,
    surname         TEXT NOT NULL,
    christian_names TEXT,
    initials        TEXT,
    decoration      TEXT,
    rank_text       TEXT,                -- Denormalized original rank string
    rank_id         INTEGER,
    dc_id           REAL,
    death_date_raw  TEXT,                -- Original text e.g. "05/09/15"
    death_date      TEXT,                -- Parsed ISO date e.g. "1915-09-05"
    additional_text TEXT,
    rnk_id          INTEGER,
    FOREIGN KEY (battalion_id) REFERENCES battalions_sd(battalion_id),
    FOREIGN KEY (rank_id) REFERENCES ranks(rank_id)
);

CREATE TABLE IF NOT EXISTS soldiers (
    soldier_id       INTEGER PRIMARY KEY,
    reg_sort         REAL,
    regiment_id      REAL,
    battalion_id     INTEGER NOT NULL,
    surname          TEXT NOT NULL,
    christian_names  TEXT,
    initials         TEXT,
    birth_town       TEXT,
    enlistment_loc   TEXT,
    enlistment_place TEXT,
    number_prefix    TEXT,
    service_number   TEXT,
    rank_text        TEXT,                -- Denormalized original rank string
    dc_id            REAL,
    death_date_raw   TEXT,                -- Original text
    death_date       TEXT,                -- Parsed ISO date
    additional_text  TEXT,
    number_sort      INTEGER,
    death_loc_id     REAL,
    death_location   TEXT,               -- 137 unique values -> searchable dropdown
    town_id          REAL,
    rank_id          INTEGER,
    rnk_old          REAL,
    rnk_id           INTEGER,
    FOREIGN KEY (battalion_id) REFERENCES battalions_sd(battalion_id),
    FOREIGN KEY (rank_id) REFERENCES ranks(rank_id)
);

-- ============================================================
-- Indexes for Multi-Parameter Search
-- ============================================================

-- Primary search indexes (free text fields)
CREATE INDEX IF NOT EXISTS idx_officers_surname ON officers(surname);
CREATE INDEX IF NOT EXISTS idx_officers_christian_names ON officers(christian_names);
CREATE INDEX IF NOT EXISTS idx_soldiers_surname ON soldiers(surname);
CREATE INDEX IF NOT EXISTS idx_soldiers_christian_names ON soldiers(christian_names);
CREATE INDEX IF NOT EXISTS idx_soldiers_service_number ON soldiers(service_number);

-- Filter indexes (dropdown/searchable dropdown fields)
CREATE INDEX IF NOT EXISTS idx_officers_battalion ON officers(battalion_id);
CREATE INDEX IF NOT EXISTS idx_officers_rank ON officers(rank_id);
CREATE INDEX IF NOT EXISTS idx_officers_decoration ON officers(decoration);
CREATE INDEX IF NOT EXISTS idx_soldiers_battalion ON soldiers(battalion_id);
CREATE INDEX IF NOT EXISTS idx_soldiers_rank ON soldiers(rank_id);
CREATE INDEX IF NOT EXISTS idx_soldiers_death_location ON soldiers(death_location);

-- Location search indexes (autocomplete fields)
CREATE INDEX IF NOT EXISTS idx_soldiers_birth_town ON soldiers(birth_town);
CREATE INDEX IF NOT EXISTS idx_soldiers_enlistment_loc ON soldiers(enlistment_loc);

-- Date range indexes
CREATE INDEX IF NOT EXISTS idx_officers_death_date ON officers(death_date);
CREATE INDEX IF NOT EXISTS idx_soldiers_death_date ON soldiers(death_date);

-- Composite indexes for common multi-parameter queries
CREATE INDEX IF NOT EXISTS idx_officers_surname_battalion ON officers(surname, battalion_id);
CREATE INDEX IF NOT EXISTS idx_soldiers_surname_battalion ON soldiers(surname, battalion_id);
CREATE INDEX IF NOT EXISTS idx_soldiers_surname_rank ON soldiers(surname, rank_id);
CREATE INDEX IF NOT EXISTS idx_soldiers_battalion_rank ON soldiers(battalion_id, rank_id);
CREATE INDEX IF NOT EXISTS idx_soldiers_battalion_death ON soldiers(battalion_id, death_date);

-- Regiment association indexes
CREATE INDEX IF NOT EXISTS idx_regbat_sd_regiment ON regiment_battalion_sd(regiment_id);
CREATE INDEX IF NOT EXISTS idx_regbat_sd_battalion ON regiment_battalion_sd(battalion_id);
CREATE INDEX IF NOT EXISTS idx_regbat_od_regiment ON regiment_battalion_od(regiment_id);
CREATE INDEX IF NOT EXISTS idx_regbat_od_battalion ON regiment_battalion_od(battalion_id);

-- Rank reference indexes
CREATE INDEX IF NOT EXISTS idx_ranks_group ON ranks(rank_group);
CREATE INDEX IF NOT EXISTS idx_ranks_new ON ranks(rank_new);

-- ============================================================
-- Lookup Tables (Materialised for autocomplete performance)
-- ============================================================

CREATE TABLE IF NOT EXISTS surname_lookup AS
    SELECT DISTINCT surname FROM (
        SELECT surname FROM soldiers
        UNION
        SELECT surname FROM officers
    ) ORDER BY surname;

CREATE INDEX IF NOT EXISTS idx_surname_lookup ON surname_lookup(surname);
