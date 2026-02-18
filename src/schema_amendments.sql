-- Schema amendments for record annotations and image storage
-- Phase C Extension: User-contributed supplemental data
-- Date: 17 February 2026

-- ══════════════════════════════════════════════════════════════════════════════
-- RECORD ANNOTATIONS TABLE
-- ══════════════════════════════════════════════════════════════════════════════
-- Stores user-contributed supplemental information for personnel records
-- Original data in soldiers/officers tables remains immutable

CREATE TABLE IF NOT EXISTS record_annotations (
    annotation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_type TEXT NOT NULL CHECK(record_type IN ('soldier', 'officer')),
    record_id INTEGER NOT NULL,
    
    -- Supplemental fields (all optional)
    additional_names TEXT,           -- Alternative spellings, nicknames, maiden names
    birth_date TEXT,                 -- If known and not in original data
    birth_place_detail TEXT,         -- More specific than birth_town
    family_info TEXT,                -- Parents, siblings, spouse, children
    pre_war_occupation TEXT,         -- Civilian job before enlistment
    enlistment_details TEXT,         -- Circumstances of joining
    service_notes TEXT,              -- Additional service information
    casualty_details TEXT,           -- Circumstances of death/injury
    burial_memorial TEXT,            -- Grave location, memorial inscription
    medals_honors TEXT,              -- Additional decorations not in main record
    personal_effects TEXT,           -- Items returned to family
    newspaper_mentions TEXT,         -- References in press
    family_stories TEXT,             -- Oral history, family memories
    research_notes TEXT,             -- General notes from researchers
    sources TEXT,                    -- References for the supplemental data
    
    -- Metadata
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    created_by TEXT NOT NULL,        -- User identifier (name or email)
    modified_at TEXT NOT NULL DEFAULT (datetime('now')),
    modified_by TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,  -- Soft delete flag
    
    -- Ensure one active annotation per record
    UNIQUE(record_type, record_id, is_active)
);

CREATE INDEX idx_annotations_record ON record_annotations(record_type, record_id);
CREATE INDEX idx_annotations_created ON record_annotations(created_at);

-- ══════════════════════════════════════════════════════════════════════════════
-- ANNOTATION HISTORY TABLE
-- ══════════════════════════════════════════════════════════════════════════════
-- Full audit trail of all changes to annotations

CREATE TABLE IF NOT EXISTS annotation_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    annotation_id INTEGER NOT NULL,
    
    -- Snapshot of changed fields
    field_name TEXT NOT NULL,        -- Which field was changed
    old_value TEXT,                  -- Previous value (NULL if new field)
    new_value TEXT,                  -- New value (NULL if deleted)
    
    -- Metadata
    changed_at TEXT NOT NULL DEFAULT (datetime('now')),
    changed_by TEXT NOT NULL,
    change_reason TEXT,              -- Optional explanation
    
    FOREIGN KEY (annotation_id) REFERENCES record_annotations(annotation_id)
);

CREATE INDEX idx_history_annotation ON annotation_history(annotation_id);
CREATE INDEX idx_history_changed ON annotation_history(changed_at);

-- ══════════════════════════════════════════════════════════════════════════════
-- IMAGES TABLE
-- ══════════════════════════════════════════════════════════════════════════════
-- Stores images as BLOBs with metadata

CREATE TABLE IF NOT EXISTS record_images (
    image_id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_type TEXT NOT NULL CHECK(record_type IN ('soldier', 'officer')),
    record_id INTEGER NOT NULL,
    
    -- Image data
    image_data BLOB NOT NULL,        -- Binary image data
    image_type TEXT NOT NULL,        -- MIME type: image/jpeg, image/png, etc.
    file_size INTEGER NOT NULL,      -- Size in bytes
    
    -- Image metadata
    title TEXT,                      -- Short description
    description TEXT,                -- Detailed caption
    image_category TEXT,             -- 'portrait', 'document', 'memorial', 'family', 'location', 'artifact', 'other'
    date_taken TEXT,                 -- When photo was taken (if known)
    location TEXT,                   -- Where photo was taken
    photographer TEXT,               -- Who took the photo
    source TEXT,                     -- Where image came from
    copyright_info TEXT,             -- Usage rights, attribution
    
    -- Display settings
    is_primary INTEGER NOT NULL DEFAULT 0,  -- Main profile image
    display_order INTEGER NOT NULL DEFAULT 0,
    
    -- Metadata
    uploaded_at TEXT NOT NULL DEFAULT (datetime('now')),
    uploaded_by TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    
    -- Constraints
    CHECK(file_size > 0 AND file_size <= 10485760)  -- Max 10MB per image
);

CREATE INDEX idx_images_record ON record_images(record_type, record_id);
CREATE INDEX idx_images_primary ON record_images(record_type, record_id, is_primary);
CREATE INDEX idx_images_uploaded ON record_images(uploaded_at);

-- ══════════════════════════════════════════════════════════════════════════════
-- USER CONFIRMATION LOG
-- ══════════════════════════════════════════════════════════════════════════════
-- Tracks user confirmations before making changes (per requirement)

CREATE TABLE IF NOT EXISTS user_confirmations (
    confirmation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_type TEXT NOT NULL,
    record_id INTEGER NOT NULL,
    action_type TEXT NOT NULL,       -- 'add_annotation', 'edit_annotation', 'upload_image', 'delete_image'
    user_identifier TEXT NOT NULL,
    confirmed_at TEXT NOT NULL DEFAULT (datetime('now')),
    ip_address TEXT,                 -- Optional for audit
    user_agent TEXT                  -- Optional for audit
);

CREATE INDEX idx_confirmations_record ON user_confirmations(record_type, record_id);
CREATE INDEX idx_confirmations_user ON user_confirmations(user_identifier);
CREATE INDEX idx_confirmations_date ON user_confirmations(confirmed_at);

-- ══════════════════════════════════════════════════════════════════════════════
-- VIEWS FOR EASY ACCESS
-- ══════════════════════════════════════════════════════════════════════════════

-- Combined view of soldier records with annotations
CREATE VIEW IF NOT EXISTS soldiers_with_annotations AS
SELECT 
    s.*,
    a.annotation_id,
    a.additional_names,
    a.birth_date AS annotation_birth_date,
    a.birth_place_detail,
    a.family_info,
    a.pre_war_occupation,
    a.enlistment_details,
    a.service_notes,
    a.casualty_details,
    a.burial_memorial,
    a.medals_honors,
    a.personal_effects,
    a.newspaper_mentions,
    a.family_stories,
    a.research_notes,
    a.sources,
    a.created_at AS annotation_created,
    a.created_by AS annotation_author,
    a.modified_at AS annotation_modified,
    (SELECT COUNT(*) FROM record_images WHERE record_type='soldier' AND record_id=s.soldier_id AND is_active=1) AS image_count
FROM soldiers s
LEFT JOIN record_annotations a ON a.record_type='soldier' AND a.record_id=s.soldier_id AND a.is_active=1;

-- Combined view of officer records with annotations
CREATE VIEW IF NOT EXISTS officers_with_annotations AS
SELECT 
    o.*,
    a.annotation_id,
    a.additional_names,
    a.birth_date AS annotation_birth_date,
    a.birth_place_detail,
    a.family_info,
    a.pre_war_occupation,
    a.enlistment_details,
    a.service_notes,
    a.casualty_details,
    a.burial_memorial,
    a.medals_honors,
    a.personal_effects,
    a.newspaper_mentions,
    a.family_stories,
    a.research_notes,
    a.sources,
    a.created_at AS annotation_created,
    a.created_by AS annotation_author,
    a.modified_at AS annotation_modified,
    (SELECT COUNT(*) FROM record_images WHERE record_type='officer' AND record_id=o.officer_id AND is_active=1) AS image_count
FROM officers o
LEFT JOIN record_annotations a ON a.record_type='officer' AND a.record_id=o.officer_id AND a.is_active=1;
