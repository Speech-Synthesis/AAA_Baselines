"""
AAA Engine Migration Runner

Simple forward-only migration system.
Tracks applied migrations in a migrations_history table.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment
load_dotenv(Path(__file__).parent.parent.parent / ".env")


def get_engine():
    """Get database engine from environment."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL not set")
    return create_engine(db_url)


def ensure_history_table(engine):
    """Create migrations_history table if it doesn't exist."""
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS migrations_history (
                id SERIAL PRIMARY KEY,
                version VARCHAR(10) NOT NULL UNIQUE,
                name VARCHAR(255) NOT NULL,
                applied_at TIMESTAMP DEFAULT NOW()
            )
        """))
        conn.commit()


def get_applied_migrations(engine):
    """Get list of already applied migrations."""
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT version FROM migrations_history ORDER BY version"
        ))
        return {row[0] for row in result}


def apply_migration(engine, version: str, name: str, sql_path: Path):
    """Apply a single migration."""
    sql = sql_path.read_text()

    # Extract executable SQL (skip comments and documentation)
    executable_lines = []
    for line in sql.split("\n"):
        stripped = line.strip()
        # Skip comments and empty lines
        if stripped.startswith("--") or not stripped:
            continue
        executable_lines.append(line)

    executable_sql = "\n".join(executable_lines)

    if not executable_sql.strip():
        print(f"  [SKIP] {version}: No executable SQL (documentation only)")
        return False

    with engine.connect() as conn:
        try:
            conn.execute(text(executable_sql))
            conn.execute(text(
                "INSERT INTO migrations_history (version, name) VALUES (:v, :n)"
            ), {"v": version, "n": name})
            conn.commit()
            print(f"  [OK] {version}: {name}")
            return True
        except Exception as e:
            print(f"  [FAIL] {version}: {e}")
            conn.rollback()
            return False


def run_migrations(dry_run: bool = False):
    """Run all pending migrations."""
    migrations_dir = Path(__file__).parent
    engine = get_engine()

    # Ensure history table exists
    ensure_history_table(engine)

    # Get applied migrations
    applied = get_applied_migrations(engine)
    print(f"Applied migrations: {sorted(applied) or 'none'}")

    # Find pending migrations
    sql_files = sorted(migrations_dir.glob("*.sql"))
    pending = []

    for sql_file in sql_files:
        version = sql_file.stem.split("_")[0]  # e.g., "003" from "003_challenges_indexes.sql"
        if version not in applied:
            pending.append((version, sql_file.stem, sql_file))

    if not pending:
        print("No pending migrations.")
        return

    print(f"\nPending migrations: {len(pending)}")
    for version, name, _ in pending:
        print(f"  {version}: {name}")

    if dry_run:
        print("\n[DRY RUN] No changes applied.")
        return

    print("\nApplying migrations...")
    applied_count = 0
    for version, name, sql_path in pending:
        if apply_migration(engine, version, name, sql_path):
            applied_count += 1

    print(f"\nApplied {applied_count} migration(s).")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    run_migrations(dry_run=dry_run)
