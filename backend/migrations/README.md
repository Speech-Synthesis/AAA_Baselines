# AAA Engine Database Migrations

## Overview

Version-controlled database schema migrations for the AAA Engine.

## Migration History

| Version | Description | Status | Date |
|---------|-------------|--------|------|
| 001 | Initial schema (users, voiceprints, challenges, auth_logs) | APPLIED | 2026-11-12 |
| 002 | Add challenges security columns (signature, payload, created_at) | APPLIED | 2026-11-14 |
| 003 | Add challenges table indexes (token, expires_at, used) | PENDING | 2026-11-15 |

## Database Configuration

- **Database**: PostgreSQL 17.11 (Supabase)
- **Extensions**: uuid-ossp, pgcrypto
- **RLS**: Enabled on all tables

## Running Migrations

```bash
cd backend
python -m migrations.run
```

Or apply manually:
```bash
psql $DATABASE_URL -f migrations/003_challenges_indexes.sql
```

## Migration Guidelines

1. **Forward-only**: Never modify applied migrations
2. **Idempotent**: Use `IF NOT EXISTS` / `IF EXISTS` where possible
3. **No data loss**: Never DROP tables with data
4. **Document**: Include status, date, and author in each migration
