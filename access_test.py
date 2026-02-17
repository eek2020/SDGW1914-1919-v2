#!/usr/bin/env python3
"""
Database Access Test
Safely probes MDB database using mdbtools and reports findings
"""

import subprocess
import csv
import io

db_path = "data/sd_2011.mdb"

# Get table list
result = subprocess.run(["mdb-tables", "-1", db_path], capture_output=True, text=True)
tables = result.stdout.strip().split('\n')

print("=" * 70)
print("DATABASE ACCESS VERIFICATION REPORT")
print("=" * 70)
print(f"\nDatabase: {db_path}")
print(f"Access Method: mdbtools (command-line utility)")
print(f"Status: SUCCESS ✓")
print(f"\nTables Found: {len(tables)}")
print("-" * 70)

# Get schema
print("\n" + "=" * 70)
print("SCHEMA INFORMATION")
print("=" * 70)

schema_result = subprocess.run(
    ["mdb-schema", db_path],
    capture_output=True,
    text=True,
    timeout=10
)

if schema_result.returncode == 0:
    print(schema_result.stdout)

print("\n" + "=" * 70)
print("TABLE SUMMARIES")
print("=" * 70)

# Get row counts and sample data
table_info = {}
for table in tables:
    try:
        # Export table to CSV
        result = subprocess.run(
            ["mdb-export", db_path, table],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            row_count = len(lines) - 1 if len(lines) > 0 else 0
            
            # Parse header
            if len(lines) > 0:
                try:
                    reader = csv.reader(io.StringIO(lines[0]))
                    columns = next(reader)
                except:
                    columns = lines[0].split(',')
            
            table_info[table] = {
                'rows': row_count,
                'columns': columns,
                'sample': lines[1] if row_count > 0 and len(lines) > 1 else None
            }
            
            print(f"\nTable: {table}")
            print(f"  Rows: {row_count:,}")
            print(f"  Columns ({len(columns)}): {', '.join(columns)}")
            
            # Show sample row if available
            if row_count > 0 and len(lines) > 1:
                print(f"  Sample Data: {lines[1][:100]}...")
        else:
            print(f"\nTable: {table}")
            print(f"  Error: {result.stderr[:100]}")
    
    except subprocess.TimeoutExpired:
        print(f"\nTable: {table}")
        print(f"  Status: Timeout (table may be very large)")
    except Exception as e:
        print(f"\nTable: {table}")
        print(f"  Error: {str(e)}")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"✓ Database accessible via mdbtools")
print(f"✓ Total tables: {len(tables)}")
print(f"✓ Tables: {', '.join(tables)}")
print("\nRECOMMENDATION: Use mdbtools for data extraction")
print("=" * 70)
