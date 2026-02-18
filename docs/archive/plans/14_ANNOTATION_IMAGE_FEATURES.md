# Record Annotation & Image Upload Features

**Date:** 17 February 2026  
**Status:** Backend Complete, UI Templates Pending  
**Database:** Schema extended successfully

---

## Overview

New functionality allows users to contribute supplemental information and images to personnel records while preserving the original historical data as read-only.

---

## Design Decisions (User-Selected)

1. **Edit Level:** Supplemental data only - original records remain immutable
2. **Image Storage:** Embedded as BLOBs in SQLite database
3. **Image Types:** Any supporting materials (photos, documents, maps, clippings, etc.)
4. **History Tracking:** Full audit trail with ability to view/revert changes

---

## Database Schema

### New Tables Created

**`record_annotations`** - User-contributed supplemental data

- 15 optional text fields for additional information
- Links to soldier/officer records via record_type + record_id
- Tracks creator and modifier with timestamps
- Soft delete with `is_active` flag

**`annotation_history`** - Full audit trail

- Tracks every field change with old/new values
- Records who made changes and when
- Optional change reason field

**`record_images`** - Image storage

- Stores images as BLOBs (max 10MB each)
- Rich metadata: title, description, category, date, location, photographer, source, copyright
- Primary image flag for profile photos
- Display ordering support
- Soft delete

**`user_confirmations`** - Action logging

- Records all user confirmations before changes
- Tracks action type, user, timestamp, IP, user agent

### Views Created

- `soldiers_with_annotations` - Joins soldiers with their annotations
- `officers_with_annotations` - Joins officers with their annotations

---

## Backend Implementation

### AnnotationManager Class (`src/annotations.py`)

**Annotation Methods:**

- `get_annotation(record_type, record_id)` - Fetch active annotation
- `create_annotation(record_type, record_id, user, fields)` - Add new annotation
- `update_annotation(annotation_id, user, fields, reason)` - Modify with history tracking
- `get_annotation_history(annotation_id)` - View change history

**Image Methods:**

- `validate_image(image_data)` - Check size/type (JPEG, PNG, GIF, WebP, TIFF)
- `upload_image(record_type, record_id, data, user, metadata)` - Store image
- `get_images(record_type, record_id)` - List all images for record
- `get_image(image_id)` - Retrieve single image with BLOB data
- `delete_image(image_id, user)` - Soft delete
- `set_primary_image(image_id)` - Mark as profile photo

**Statistics:**

- `get_statistics()` - Overall counts and storage usage

---

## Flask Routes Added

### Annotation Routes

**`GET/POST /record/<type>/<id>/annotation`**

- View or edit annotation form
- Requires user confirmation checkbox
- Tracks changes in history table

### Image Routes

**`POST /record/<type>/<id>/upload-image`**

- Upload image with metadata
- Validates file type and size
- Requires user confirmation

**`GET /image/<image_id>`**

- Serve image from database
- Returns proper MIME type

**`POST /image/<image_id>/delete`**

- Soft delete image
- Requires confirmation

**`POST /image/<image_id>/set-primary`**

- Set as profile/primary image

**`GET /api/annotations/stats`**

- JSON statistics endpoint

---

## Supplemental Fields Available

Users can add the following information to any record:

1. **Additional Names** - Alternative spellings, nicknames, maiden names
2. **Birth Date** - If known and not in original data
3. **Birth Place Detail** - More specific location
4. **Family Info** - Parents, siblings, spouse, children
5. **Pre-war Occupation** - Civilian job
6. **Enlistment Details** - Circumstances of joining
7. **Service Notes** - Additional military service information
8. **Casualty Details** - Circumstances of death/injury
9. **Burial/Memorial** - Grave location, inscription
10. **Medals/Honors** - Additional decorations
11. **Personal Effects** - Items returned to family
12. **Newspaper Mentions** - Press references
13. **Family Stories** - Oral history, memories
14. **Research Notes** - General researcher notes
15. **Sources** - References for supplemental data

---

## Image Categories

- Portrait
- Document
- Memorial
- Family
- Location
- Artifact
- Other

---

## User Confirmation Flow

All modifications require explicit user confirmation:

1. User fills out form (annotation or image upload)
2. Must check "I confirm I want to make these changes" checkbox
3. Must provide their name/identifier
4. Action is logged in `user_confirmations` table
5. Flash message confirms success or shows error

---

## Current Status

### ✅ Completed

- Database schema design and implementation
- `AnnotationManager` class with full CRUD operations
- Flask routes for all annotation/image operations
- User confirmation logging
- Image validation (type, size)
- Full audit trail for annotations
- Statistics API endpoint

### 🔄 In Progress

- UI templates for annotation form
- UI integration in detail page
- Image gallery display
- Image upload form

### ⏳ Pending

- Tests for annotation/image functionality
- Documentation updates
- User guide section on contributing data
- Admin interface for reviewing contributions (future)

---

## Next Steps

1. **Create annotation form template** (`templates/annotation_form.html`)
2. **Update detail page** to show:
   - Existing annotations in expandable section
   - Image gallery with thumbnails
   - "Add Supplemental Information" button
   - "Upload Image" button
3. **Add CSS styling** for:
   - Annotation display
   - Image gallery grid
   - Confirmation dialogs
   - Flash messages
4. **Write tests** for new functionality
5. **Update user documentation**

---

## Technical Notes

### Database Size Impact

- Empty tables add ~0.5MB to database
- Each annotation: ~1-5KB depending on content
- Each image: varies (typically 100KB-2MB for photos, 500KB-5MB for documents)
- 10MB maximum per image enforced
- Database currently: 355.42 MB
- Estimated with 1,000 annotations + 5,000 images: ~365-375 MB

### Performance Considerations

- Images served directly from database via `/image/<id>` route
- Consider adding caching headers for image routes
- BLOB storage keeps everything in one file (good for desktop app distribution)
- No external dependencies or file system management needed

### Security Considerations

- No authentication system currently (desktop app for single user)
- User identifier is self-reported (name/email)
- No admin approval workflow (trust-based)
- Image validation prevents code execution attacks
- SQL injection prevented via parameterized queries

---

## Future Enhancements

- **Admin Review Queue** - Approve/reject contributions before publishing
- **User Accounts** - Proper authentication for multi-user scenarios
- **Image Thumbnails** - Generate and cache thumbnails for gallery view
- **Batch Upload** - Multiple images at once
- **Export Annotations** - Include supplemental data in CSV exports
- **Annotation Search** - Search within user-contributed content
- **Image Zoom/Lightbox** - Better image viewing experience
- **OCR Integration** - Extract text from document images
- **Geolocation** - Map view of locations mentioned in annotations

---

**Document Version:** 1.0  
**Related Files:**

- `src/schema_amendments.sql` - Database schema
- `src/annotations.py` - Backend logic
- `src/web_app.py` - Flask routes (lines 802-995)
- `src/scripts/apply_amendments.py` - Migration script
