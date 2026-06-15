-- v4: proof-of-visit selfie path stored on each checkin.
-- Idempotent: ALTER ... ADD COLUMN IF NOT EXISTS only adds when missing.

ALTER TABLE checkins
  ADD COLUMN IF NOT EXISTS selfie_path VARCHAR(500) NULL;
