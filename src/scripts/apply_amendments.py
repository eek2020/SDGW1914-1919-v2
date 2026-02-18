#!/usr/bin/env python3
"""
Apply schema amendments for record annotations and image storage
Adds new tables without modifying existing soldiers/officers data
"""

import sqlite3
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

DB_PATH = Path(__file__).parent.parent.parent / "data" / "sd_2011.db"
SCHEMA_PATH = Path(__file__).parent.parent / "schema_amendments.sql"


def apply_amendments():
    """Apply schema amendments to existing database."""
    
    if not DB_PATH.exists():
        print(f"❌ Database not found at {DB_PATH}")
        return False
    
    if not SCHEMA_PATH.exists():
        print(f"❌ Schema file not found at {SCHEMA_PATH}")
        return False
    
    print(f"📊 Applying schema amendments to {DB_PATH}")
    
    # Read schema amendments
    with open(SCHEMA_PATH, 'r') as f:
        schema_sql = f.read()
    
    # Connect and apply
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Execute all statements
        cursor.executescript(schema_sql)
        conn.commit()
        
        # Verify tables were created
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            AND name IN ('record_annotations', 'annotation_history', 'record_images', 'user_confirmations')
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"\n✅ Successfully created {len(tables)} new tables:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   - {table}: {count} rows")
        
        # Verify views
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='view' 
            AND name LIKE '%_with_annotations'
            ORDER BY name
        """)
        views = [row[0] for row in cursor.fetchall()]
        print(f"\n✅ Created {len(views)} views:")
        for view in views:
            print(f"   - {view}")
        
        # Show database size
        db_size_mb = DB_PATH.stat().st_size / (1024 * 1024)
        print(f"\n📦 Database size: {db_size_mb:.2f} MB")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Error applying amendments: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()


if __name__ == '__main__':
    success = apply_amendments()
    sys.exit(0 if success else 1)
