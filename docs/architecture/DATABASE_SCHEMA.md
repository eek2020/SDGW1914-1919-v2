# Database Schema Reference

**Database:** SQLite — `data/sd_2011.db` (257 MB)
**Schema Sources:** `src/schema.sql`, `src/schema_amendments.sql`, `src/reference_data.sql`

---

## Core Tables (src/schema.sql)

### ranks

Military rank reference data. Maps original rank names to normalised groups.

| Column | Type | Constraints | Description |
| --- | --- | --- | --- |
| rank_id | INTEGER | PRIMARY KEY | Original ID from legacy DB |
| new_rank_id | REAL | | Normalised rank identifier |
| original_rank_id | REAL | | Legacy rank identifier |
| rank_group | TEXT | | Rank category (e.g. "Privates", "Officers") |
| rank_new | TEXT | | Normalised rank name |
| rank_original | TEXT | | Original rank text from legacy data |
| my_rank_id | INTEGER | | Internal rank mapping |

**Row count:** 547

---

### battalions_sd

Scottish Division battalion names.

| Column | Type | Constraints | Description |
| --- | --- | --- | --- |
| battalion_id | INTEGER | PRIMARY KEY | Battalion identifier |
| name | TEXT | NOT NULL | Battalion name |

**Row count:** 721

---

### battalions_od

Other Districts battalion names.

| Column | Type | Constraints | Description |
| --- | --- | --- | --- |
| battalion_id | INTEGER | PRIMARY KEY | Battalion identifier |
| name | TEXT | NOT NULL | Battalion name |

**Row count:** 480

---

### regiment_battalion_sd

Regiment-to-battalion mapping for Scottish Division.

| Column | Type | Constraints | Description |
| --- | --- | --- | --- |
| reg_id | REAL | | Regiment identifier |
| bat_id | REAL | | Battalion identifier |
| sort_order | REAL | | Display sort order |

**Row count:** 1,987

---

### regiment_battalion_od

Regiment-to-battalion mapping for Other Districts.

| Column | Type | Constraints | Description |
| --- | --- | --- | --- |
| reg_id | REAL | | Regiment identifier |
| bat_id | REAL | | Battalion identifier |
| sort_order | REAL | | Display sort order |

**Row count:** 1,662

---

### officers

Commissioned officer personnel records.

| Column | Type | Constraints | Description |
| --- | --- | --- | --- |
| officer_id | INTEGER | PRIMARY KEY | Original O_ID |
| reg_sort | REAL | | Regiment sort order |
| regiment_id | REAL | | Regiment reference |
| battalion_id | INTEGER | NOT NULL, FK → battalions_sd | Battalion assignment |
| surname | TEXT | NOT NULL | Family name (e.g. "ADAMSON") |
| christian_names | TEXT | | Given names (e.g. "W C") |
| initials | TEXT | | Name initials |
| decoration | TEXT | | Military decorations (e.g. "DSO", "MC") |
| rank | TEXT | | Rank text (e.g. "CAPT (TP)") |
| rank_id | REAL | | FK → ranks |
| dc_id | REAL | | Death cause identifier |
| death_date | TEXT | | ISO 8601 date (e.g. "1915-09-05") |
| additional_text | TEXT | | Supplementary notes |
| rnk_id | REAL | | Additional rank reference |

**Row count:** 41,846

---

### soldiers

Enlisted soldier personnel records.

| Column | Type | Constraints | Description |
| --- | --- | --- | --- |
| soldier_id | INTEGER | PRIMARY KEY | Original S_ID |
| reg_sort | REAL | | Regiment sort order |
| regiment_id | REAL | | Regiment reference |
| battalion_id | INTEGER | NOT NULL, FK → battalions_sd | Battalion assignment |
| surname | TEXT | NOT NULL | Family name |
| christian_names | TEXT | | Given names |
| initials | TEXT | | Name initials |
| birth_town | TEXT | | Town of birth |
| enlistment_loc | TEXT | | Enlistment location |
| number_prefix | TEXT | | Service number prefix |
| service_number | TEXT | | Service number |
| rank | TEXT | | Rank text |
| dc_id | REAL | | Death cause identifier |
| death_date | TEXT | | ISO 8601 date |
| additional_text | TEXT | | Supplementary notes |
| num_sort | INTEGER | | Service number sort key |
| death_location | TEXT | | Place of death |
| rank_id | REAL | | FK → ranks |
| rnk_id | INTEGER | | Additional rank reference |

**Row count:** 661,960

---

### surname_lookup

Materialised table of distinct surnames from both officers and soldiers. Used for fast autocomplete.

```sql
CREATE TABLE IF NOT EXISTS surname_lookup AS
    SELECT DISTINCT surname FROM (
        SELECT surname FROM soldiers
        UNION
        SELECT surname FROM officers
    ) ORDER BY surname;
```

**Row count:** 50,323

---

## Indexes (27 total)

Key composite indexes optimise multi-parameter search:

- `idx_soldiers_surname`, `idx_officers_surname` — Surname search
- `idx_soldiers_battalion`, `idx_officers_battalion` — Battalion filter
- `idx_soldiers_rank`, `idx_officers_rank` — Rank filter
- `idx_soldiers_death_date`, `idx_officers_death_date` — Date range queries
- `idx_soldiers_birth_town` — Birth town filter
- `idx_soldiers_enlistment_loc` — Enlistment location filter
- `idx_soldiers_service_number` — Service number lookup
- `idx_soldiers_death_location` — Death location filter
- `idx_surname_lookup` — Autocomplete performance
- Additional composite indexes for common multi-field query patterns

---

## Annotation Tables (src/schema_amendments.sql)

### record_annotations

User-contributed supplemental information. Original records remain immutable.

| Column | Type | Constraints | Description |
| --- | --- | --- | --- |
| annotation_id | INTEGER | PRIMARY KEY AUTOINCREMENT | |
| record_type | TEXT | NOT NULL, CHECK('soldier','officer') | |
| record_id | INTEGER | NOT NULL | FK to soldiers/officers |
| additional_names | TEXT | | Alternative spellings, nicknames |
| birth_date | TEXT | | If known |
| birth_place_detail | TEXT | | More specific location |
| family_info | TEXT | | Parents, siblings, spouse, children |
| pre_war_occupation | TEXT | | Civilian job |
| enlistment_details | TEXT | | Circumstances of joining |
| service_notes | TEXT | | Additional service info |
| casualty_details | TEXT | | Circumstances of death/injury |
| burial_memorial | TEXT | | Grave location, inscription |
| medals_honors | TEXT | | Additional decorations |
| personal_effects | TEXT | | Items returned to family |
| newspaper_mentions | TEXT | | Press references |
| family_stories | TEXT | | Oral history |
| research_notes | TEXT | | Researcher notes |
| sources | TEXT | | References |
| created_at | TEXT | NOT NULL, DEFAULT datetime('now') | |
| created_by | TEXT | NOT NULL | User identifier |
| modified_at | TEXT | NOT NULL, DEFAULT datetime('now') | |
| modified_by | TEXT | NOT NULL | |
| is_active | INTEGER | NOT NULL, DEFAULT 1 | Soft delete flag |

**Constraint:** UNIQUE(record_type, record_id, is_active) — one active annotation per record.

---

### annotation_history

Full audit trail of annotation changes.

| Column | Type | Constraints | Description |
| --- | --- | --- | --- |
| history_id | INTEGER | PRIMARY KEY AUTOINCREMENT | |
| annotation_id | INTEGER | NOT NULL, FK → record_annotations | |
| field_name | TEXT | NOT NULL | Which field changed |
| old_value | TEXT | | Previous value |
| new_value | TEXT | | New value |
| changed_at | TEXT | NOT NULL, DEFAULT datetime('now') | |
| changed_by | TEXT | NOT NULL | |
| change_reason | TEXT | | Optional explanation |

---

### record_images

Image storage as BLOBs with metadata.

| Column | Type | Constraints | Description |
| --- | --- | --- | --- |
| image_id | INTEGER | PRIMARY KEY AUTOINCREMENT | |
| record_type | TEXT | NOT NULL, CHECK('soldier','officer') | |
| record_id | INTEGER | NOT NULL | |
| image_data | BLOB | NOT NULL | Binary image data |
| image_type | TEXT | NOT NULL | MIME type |
| file_size | INTEGER | NOT NULL, CHECK(> 0 AND <= 10485760) | Max 10 MB |
| title | TEXT | | Short description |
| description | TEXT | | Detailed caption |
| image_category | TEXT | | portrait/document/memorial/family/location/artifact/other |
| date_taken | TEXT | | When photo was taken |
| location | TEXT | | Where photo was taken |
| photographer | TEXT | | |
| source | TEXT | | Origin |
| copyright_info | TEXT | | Usage rights |
| is_primary | INTEGER | NOT NULL, DEFAULT 0 | Main profile image flag |
| display_order | INTEGER | NOT NULL, DEFAULT 0 | |
| uploaded_at | TEXT | NOT NULL, DEFAULT datetime('now') | |
| uploaded_by | TEXT | NOT NULL | |
| is_active | INTEGER | NOT NULL, DEFAULT 1 | Soft delete |

**Allowed image types:** JPEG, PNG, GIF, WebP, TIFF

---

### user_confirmations

Action logging for all user modifications.

| Column | Type | Constraints | Description |
| --- | --- | --- | --- |
| confirmation_id | INTEGER | PRIMARY KEY AUTOINCREMENT | |
| record_type | TEXT | NOT NULL | |
| record_id | INTEGER | NOT NULL | |
| action_type | TEXT | NOT NULL | add_annotation, edit_annotation, upload_image, delete_image |
| user_identifier | TEXT | NOT NULL | |
| confirmed_at | TEXT | NOT NULL, DEFAULT datetime('now') | |
| ip_address | TEXT | | Optional audit info |
| user_agent | TEXT | | Optional audit info |

---

## Views

- **soldiers_with_annotations** — Joins soldiers with active annotations and image count
- **officers_with_annotations** — Joins officers with active annotations and image count

---

## Reference Tables (src/reference_data.sql)

### ref_regiment_names

Maps regiment_id to human-readable regiment names. 93 entries covering all regiment IDs found in the data.

### ref_theatre_groups

Maps death location strings to theatre of war groups (Western Front, Gallipoli & Dardanelles, Mesopotamia & Persian Gulf, Egypt & Palestine, Salonika & Balkans, Africa, India & Burma, Italy, At Sea, Home, Russia, Far East, Other). 133 entries.

### ref_region_places

Counties and cities for classifying birth/enlistment locations by country (Scotland, Wales, Ireland, England). Used for geographic grouping. 226 entries.

### ref_place_keywords

Keywords indicating overseas or European locations. 48 entries.
