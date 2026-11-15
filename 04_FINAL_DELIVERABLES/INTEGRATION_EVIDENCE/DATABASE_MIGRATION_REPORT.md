# AAA Engine — Database Migration Report

**Date:** November 15, 2026
**Author:** Surya
**Database:** PostgreSQL 17.11 (Supabase)

---

## 1. Connection Verification

| Parameter | Value |
|-----------|-------|
| Host | `db.wsniwyojscpxbfygcbud.supabase.co` |
| Port | 6543 (Supavisor pooler) |
| Database | postgres |
| Version | PostgreSQL 17.11 |
| Connection | Verified ✓ |

---

## 2. Extensions

| Extension | Status |
|-----------|--------|
| plpgsql | Active |
| uuid-ossp | Active |
| pgcrypto | Active |
| pg_stat_statements | Active |
| supabase_vault | Active |

---

## 3. Table Schema

### users
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() |
| name | TEXT | NOT NULL |
| email | TEXT | NOT NULL, UNIQUE |
| created_at | TIMESTAMP | DEFAULT now() |

### voiceprints
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() |
| user_id | UUID | NOT NULL, FK → users(id), UNIQUE |
| embedding | FLOAT8[] | NOT NULL |
| sample_count | INTEGER | NOT NULL, DEFAULT 1 |
| updated_at | TIMESTAMP | DEFAULT now() |

### challenges
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() |
| user_id | UUID | NOT NULL, FK → users(id) |
| phrase | TEXT | NOT NULL |
| token | TEXT | NOT NULL, UNIQUE INDEX |
| expires_at | TIMESTAMP | NOT NULL, INDEX |
| used | BOOLEAN | NOT NULL, DEFAULT false, INDEX |
| signature | TEXT | NULL |
| payload | TEXT | NULL |
| created_at | TIMESTAMP | DEFAULT now() |

### auth_logs
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() |
| user_id | UUID | FK → users(id) |
| challenge_id | UUID | FK → challenges(id) |
| l2_label | TEXT | NULL |
| l2_confidence | DOUBLE PRECISION | NULL |
| l1_score | DOUBLE PRECISION | NULL |
| result | TEXT | NULL |
| layer_blocked | INTEGER | NULL |
| created_at | TIMESTAMP | DEFAULT now() |

---

## 4. Row Level Security

| Table | RLS Status |
|-------|------------|
| users | ENABLED |
| voiceprints | ENABLED |
| challenges | ENABLED |
| auth_logs | ENABLED |

---

## 5. Indexes Applied

| Index Name | Table | Columns | Type |
|------------|-------|---------|------|
| users_pkey | users | id | PRIMARY |
| users_email_key | users | email | UNIQUE |
| voiceprints_pkey | voiceprints | id | PRIMARY |
| voiceprints_user_id_key | voiceprints | user_id | UNIQUE |
| challenges_pkey | challenges | id | PRIMARY |
| ix_challenges_token | challenges | token | UNIQUE |
| ix_challenges_expires_at | challenges | expires_at | B-TREE |
| ix_challenges_used | challenges | used | B-TREE |
| auth_logs_pkey | auth_logs | id | PRIMARY |

---

## 6. Migration History

| Version | Name | Applied At |
|---------|------|------------|
| 003 | 003_challenges_indexes | 2026-11-15 04:39:59 |

**Note:** Migrations 001 and 002 document schema that was created manually via Supabase dashboard.

---

## 7. Data Counts (Pre-Migration)

| Table | Records |
|-------|---------|
| users | 6 |
| voiceprints | 6 |
| challenges | 72 |
| auth_logs | 68 |

---

## 8. Functional Tests

### Single-Use Token Enforcement
```
1. Created challenge: ca51bb26-920d-4d51-b737-703a4cbb0118
2. First consume: SUCCESS
3. Second consume blocked: YES
4. Cleanup: OK
```

### Foreign Key Integrity
```
User: avkbsurya@gmail.com
Voiceprints for user: 1
Auth logs for user: 19
```

---

## 9. Compatibility Fixes Applied

| Issue | Fix | File |
|-------|-----|------|
| UUID handling | Handle native PostgreSQL UUID | models.py |
| Boolean syntax | Use true/false instead of 0/1 | layer3_adaptive.py |
| Missing indexes | Applied via migration 003 | migrations/ |

---

**Report Status:** COMPLETE
**Database Status:** SYNCHRONIZED
