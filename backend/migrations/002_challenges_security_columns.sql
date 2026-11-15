-- Migration 002: Add Challenge Security Columns
-- Status: APPLIED (via Claude Code session 2026-11-14)
-- Date: 2026-11-14
-- Author: Surya
--
-- Adds signature, payload, and created_at columns to challenges table
-- for HMAC-signed single-use token verification.

-- These commands were executed via Python session:
-- ALTER TABLE challenges ADD COLUMN IF NOT EXISTS signature TEXT;
-- ALTER TABLE challenges ADD COLUMN IF NOT EXISTS payload TEXT;
-- ALTER TABLE challenges ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT now();

-- Verification query:
-- SELECT column_name, data_type FROM information_schema.columns
-- WHERE table_name = 'challenges';
