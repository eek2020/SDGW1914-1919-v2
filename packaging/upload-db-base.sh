#!/usr/bin/env bash
# Upload the SDGW database to the `db-base` GitHub release.
#
# The CI build pipeline pulls sd_2011.db.zip from this release at build
# time. Re-run this whenever the local database is updated and you want
# future installer builds to include the new data.
#
# Usage:
#   packaging/upload-db-base.sh [path/to/sd_2011.db]
#
# Default DB path: ~/SDGW-USB/Windows/SDGW/data/sd_2011.db
# Override by passing a path as the first argument.

set -euo pipefail

REPO="eek2020/SDGW1914-1919-v2"
TAG="db-base"
DEFAULT_DB="${HOME}/SDGW-USB/Windows/SDGW/data/sd_2011.db"
DB_PATH="${1:-$DEFAULT_DB}"

if [[ ! -f "$DB_PATH" ]]; then
    echo "ERROR: database file not found: $DB_PATH" >&2
    echo "Pass the correct path as the first argument." >&2
    exit 1
fi

if ! head -c 16 "$DB_PATH" | grep -q "SQLite format 3"; then
    echo "ERROR: $DB_PATH does not look like a SQLite database" >&2
    exit 1
fi

DB_SIZE_MB=$(( $(stat -f %z "$DB_PATH") / 1048576 ))
echo "Database: $DB_PATH ($DB_SIZE_MB MB uncompressed)"

WORK_DIR=$(mktemp -d)
trap 'rm -rf "$WORK_DIR"' EXIT

echo "Copying and zipping (this may take a minute)..."
cp "$DB_PATH" "$WORK_DIR/sd_2011.db"
( cd "$WORK_DIR" && zip -9 -q sd_2011.db.zip sd_2011.db )
ZIP_SIZE_MB=$(( $(stat -f %z "$WORK_DIR/sd_2011.db.zip") / 1048576 ))
echo "Compressed: $ZIP_SIZE_MB MB"

if ! gh release view "$TAG" --repo "$REPO" >/dev/null 2>&1; then
    echo "Creating release '$TAG'..."
    gh release create "$TAG" \
        --repo "$REPO" \
        --title "Database base asset" \
        --notes "Holding release for the SDGW SQLite database. Used by the build-windows CI workflow. Not a user-facing release." \
        --latest=false
else
    echo "Release '$TAG' already exists; will overwrite asset."
fi

echo "Uploading sd_2011.db.zip (this may take several minutes on slow connections)..."
gh release upload "$TAG" "$WORK_DIR/sd_2011.db.zip" --repo "$REPO" --clobber

echo ""
echo "Done. The next push to main or v* tag will pick up this database."
echo "Asset URL: https://github.com/$REPO/releases/download/$TAG/sd_2011.db.zip"
