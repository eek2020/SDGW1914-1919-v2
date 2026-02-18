#!/usr/bin/env python3
"""
Annotation and image management module
Handles user-contributed supplemental data for personnel records
"""

import sqlite3
from datetime import datetime
from pathlib import Path
import base64
from io import BytesIO


class AnnotationManager:
    """Manages record annotations and images."""
    
    ALLOWED_IMAGE_TYPES = {'jpeg', 'jpg', 'png', 'gif', 'webp', 'tiff'}
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
    
    def __init__(self, db_path):
        self.db_path = db_path
    
    def _get_connection(self):
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    # ── Annotation Methods ──────────────────────────────────────────────────
    
    def get_annotation(self, record_type, record_id):
        """Get active annotation for a record."""
        conn = self._get_connection()
        try:
            result = conn.execute(
                "SELECT * FROM record_annotations WHERE record_type=? AND record_id=? AND is_active=1",
                (record_type, record_id)
            ).fetchone()
            return dict(result) if result else None
        finally:
            conn.close()
    
    def create_annotation(self, record_type, record_id, user_identifier, fields):
        """Create new annotation for a record."""
        conn = self._get_connection()
        try:
            # Check if annotation already exists
            existing = self.get_annotation(record_type, record_id)
            if existing:
                raise ValueError("Annotation already exists for this record")
            
            # Build insert statement dynamically based on provided fields
            valid_fields = {
                'additional_names', 'birth_date', 'birth_place_detail', 'family_info',
                'pre_war_occupation', 'enlistment_details', 'service_notes',
                'casualty_details', 'burial_memorial', 'medals_honors',
                'personal_effects', 'newspaper_mentions', 'family_stories',
                'research_notes', 'sources'
            }
            
            provided_fields = {k: v for k, v in fields.items() if k in valid_fields and v}
            
            if not provided_fields:
                raise ValueError("No valid fields provided")
            
            field_names = ', '.join(provided_fields.keys())
            placeholders = ', '.join(['?'] * len(provided_fields))
            
            query = f"""
                INSERT INTO record_annotations 
                (record_type, record_id, {field_names}, created_by, modified_by)
                VALUES (?, ?, {placeholders}, ?, ?)
            """
            
            values = [record_type, record_id] + list(provided_fields.values()) + [user_identifier, user_identifier]
            
            cursor = conn.execute(query, values)
            annotation_id = cursor.lastrowid
            
            # Log confirmation
            self._log_confirmation(conn, record_type, record_id, 'add_annotation', user_identifier)
            
            conn.commit()
            return annotation_id
            
        finally:
            conn.close()
    
    VALID_ANNOTATION_FIELDS = frozenset({
        'additional_names', 'birth_date', 'birth_place_detail', 'family_info',
        'pre_war_occupation', 'enlistment_details', 'service_notes',
        'casualty_details', 'burial_memorial', 'medals_honors',
        'personal_effects', 'newspaper_mentions', 'family_stories',
        'research_notes', 'sources'
    })

    def update_annotation(self, annotation_id, user_identifier, fields, change_reason=None):
        """Update existing annotation and track changes in history."""
        safe_fields = {k: v for k, v in fields.items() if k in self.VALID_ANNOTATION_FIELDS}
        if not safe_fields:
            raise ValueError("No valid fields to update")
        
        conn = self._get_connection()
        try:
            # Get current values
            current = conn.execute(
                "SELECT * FROM record_annotations WHERE annotation_id=? AND is_active=1",
                (annotation_id,)
            ).fetchone()
            
            if not current:
                raise ValueError("Annotation not found")
            
            current_dict = dict(current)
            
            # Track changes
            changes = []
            for field, new_value in safe_fields.items():
                old_value = current_dict.get(field)
                if old_value != new_value:
                    changes.append((field, old_value, new_value))
            
            if not changes:
                return annotation_id  # No changes
            
            # Update annotation
            set_clause = ', '.join([f"{field}=?" for field in safe_fields.keys()])
            query = f"""
                UPDATE record_annotations 
                SET {set_clause}, modified_at=datetime('now'), modified_by=?
                WHERE annotation_id=?
            """
            
            values = list(safe_fields.values()) + [user_identifier, annotation_id]
            conn.execute(query, values)
            
            # Record history
            for field_name, old_value, new_value in changes:
                conn.execute("""
                    INSERT INTO annotation_history 
                    (annotation_id, field_name, old_value, new_value, changed_by, change_reason)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (annotation_id, field_name, old_value, new_value, user_identifier, change_reason))
            
            # Log confirmation
            self._log_confirmation(conn, current_dict['record_type'], current_dict['record_id'], 
                                 'edit_annotation', user_identifier)
            
            conn.commit()
            return annotation_id
            
        finally:
            conn.close()
    
    def get_annotation_history(self, annotation_id):
        """Get full change history for an annotation."""
        conn = self._get_connection()
        try:
            results = conn.execute("""
                SELECT * FROM annotation_history 
                WHERE annotation_id=? 
                ORDER BY changed_at DESC
            """, (annotation_id,)).fetchall()
            return [dict(row) for row in results]
        finally:
            conn.close()
    
    # ── Image Methods ───────────────────────────────────────────────────────
    
    def _detect_image_type(self, image_data):
        """Detect image type from magic bytes."""
        if len(image_data) < 12:
            return None
        
        # Check magic bytes for common image formats
        if image_data[:2] == b'\xff\xd8':
            return 'jpeg'
        elif image_data[:8] == b'\x89PNG\r\n\x1a\n':
            return 'png'
        elif image_data[:6] in (b'GIF87a', b'GIF89a'):
            return 'gif'
        elif image_data[:4] == b'RIFF' and image_data[8:12] == b'WEBP':
            return 'webp'
        elif image_data[:4] in (b'II*\x00', b'MM\x00*'):
            return 'tiff'
        
        return None
    
    def validate_image(self, image_data):
        """Validate image data and return type."""
        if len(image_data) > self.MAX_IMAGE_SIZE:
            raise ValueError(f"Image exceeds maximum size of {self.MAX_IMAGE_SIZE // (1024*1024)}MB")
        
        # Detect image type
        image_type = self._detect_image_type(image_data)
        if not image_type or image_type not in self.ALLOWED_IMAGE_TYPES:
            raise ValueError(f"Unsupported image type. Allowed: {', '.join(self.ALLOWED_IMAGE_TYPES)}")
        
        return f"image/{image_type}"
    
    def upload_image(self, record_type, record_id, image_data, user_identifier, metadata=None):
        """Upload image for a record."""
        metadata = metadata or {}
        
        # Validate image
        mime_type = self.validate_image(image_data)
        file_size = len(image_data)
        
        conn = self._get_connection()
        try:
            # Insert image
            cursor = conn.execute("""
                INSERT INTO record_images 
                (record_type, record_id, image_data, image_type, file_size,
                 title, description, image_category, date_taken, location,
                 photographer, source, copyright_info, is_primary, display_order,
                 uploaded_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record_type, record_id, image_data, mime_type, file_size,
                metadata.get('title'), metadata.get('description'),
                metadata.get('image_category', 'other'), metadata.get('date_taken'),
                metadata.get('location'), metadata.get('photographer'),
                metadata.get('source'), metadata.get('copyright_info'),
                metadata.get('is_primary', 0), metadata.get('display_order', 0),
                user_identifier
            ))
            
            image_id = cursor.lastrowid
            
            # Log confirmation
            self._log_confirmation(conn, record_type, record_id, 'upload_image', user_identifier)
            
            conn.commit()
            return image_id
            
        finally:
            conn.close()
    
    def get_images(self, record_type, record_id, include_data=False):
        """Get all images for a record."""
        conn = self._get_connection()
        try:
            if include_data:
                query = "SELECT * FROM record_images WHERE record_type=? AND record_id=? AND is_active=1 ORDER BY is_primary DESC, display_order, uploaded_at"
            else:
                query = """
                    SELECT image_id, record_type, record_id, image_type, file_size,
                           title, description, image_category, date_taken, location,
                           photographer, source, copyright_info, is_primary, display_order,
                           uploaded_at, uploaded_by
                    FROM record_images 
                    WHERE record_type=? AND record_id=? AND is_active=1 
                    ORDER BY is_primary DESC, display_order, uploaded_at
                """
            
            results = conn.execute(query, (record_type, record_id)).fetchall()
            return [dict(row) for row in results]
        finally:
            conn.close()
    
    def get_image(self, image_id):
        """Get single image with data."""
        conn = self._get_connection()
        try:
            result = conn.execute(
                "SELECT * FROM record_images WHERE image_id=? AND is_active=1",
                (image_id,)
            ).fetchone()
            return dict(result) if result else None
        finally:
            conn.close()
    
    def delete_image(self, image_id, user_identifier):
        """Soft delete an image."""
        conn = self._get_connection()
        try:
            # Get image info for logging
            image = self.get_image(image_id)
            if not image:
                raise ValueError("Image not found")
            
            conn.execute(
                "UPDATE record_images SET is_active=0 WHERE image_id=?",
                (image_id,)
            )
            
            # Log confirmation
            self._log_confirmation(conn, image['record_type'], image['record_id'], 
                                 'delete_image', user_identifier)
            
            conn.commit()
            
        finally:
            conn.close()
    
    def set_primary_image(self, image_id):
        """Set an image as the primary/profile image for a record."""
        conn = self._get_connection()
        try:
            # Get image info
            image = self.get_image(image_id)
            if not image:
                raise ValueError("Image not found")
            
            # Clear other primary flags for this record
            conn.execute("""
                UPDATE record_images 
                SET is_primary=0 
                WHERE record_type=? AND record_id=? AND is_active=1
            """, (image['record_type'], image['record_id']))
            
            # Set this as primary
            conn.execute(
                "UPDATE record_images SET is_primary=1 WHERE image_id=?",
                (image_id,)
            )
            
            conn.commit()
            
        finally:
            conn.close()
    
    # ── Helper Methods ──────────────────────────────────────────────────────
    
    def _log_confirmation(self, conn, record_type, record_id, action_type, user_identifier):
        """Log user confirmation."""
        conn.execute("""
            INSERT INTO user_confirmations 
            (record_type, record_id, action_type, user_identifier)
            VALUES (?, ?, ?, ?)
        """, (record_type, record_id, action_type, user_identifier))
    
    def get_statistics(self):
        """Get overall statistics."""
        conn = self._get_connection()
        try:
            stats = {}
            
            # Annotation counts
            result = conn.execute("SELECT COUNT(*) FROM record_annotations WHERE is_active=1").fetchone()
            stats['total_annotations'] = result[0]
            
            # Image counts
            result = conn.execute("SELECT COUNT(*) FROM record_images WHERE is_active=1").fetchone()
            stats['total_images'] = result[0]
            
            # Total image storage
            result = conn.execute("SELECT SUM(file_size) FROM record_images WHERE is_active=1").fetchone()
            stats['total_image_bytes'] = result[0] or 0
            stats['total_image_mb'] = (result[0] or 0) / (1024 * 1024)
            
            # Records with annotations
            result = conn.execute("""
                SELECT COUNT(DISTINCT record_type || '-' || record_id) 
                FROM record_annotations WHERE is_active=1
            """).fetchone()
            stats['records_with_annotations'] = result[0]
            
            # Records with images
            result = conn.execute("""
                SELECT COUNT(DISTINCT record_type || '-' || record_id) 
                FROM record_images WHERE is_active=1
            """).fetchone()
            stats['records_with_images'] = result[0]
            
            return stats
            
        finally:
            conn.close()
