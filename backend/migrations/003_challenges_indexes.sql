-- Migration 003: Add Challenges Table Indexes
-- Status: PENDING
-- Date: 2026-11-15
-- Author: Surya
--
-- Adds required indexes to challenges table for performance:
-- - token: Unique index for fast lookup during verification
-- - expires_at: Index for cleanup queries
-- - used: Index for filtering active challenges

-- Idempotent index creation
CREATE UNIQUE INDEX IF NOT EXISTS ix_challenges_token ON challenges(token);
CREATE INDEX IF NOT EXISTS ix_challenges_expires_at ON challenges(expires_at);
CREATE INDEX IF NOT EXISTS ix_challenges_used ON challenges(used);

-- Verification query:
-- SELECT indexname FROM pg_indexes WHERE tablename = 'challenges';
