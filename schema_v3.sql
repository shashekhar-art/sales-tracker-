-- v3: expand account types to include retailer + wholesaler.
-- Idempotent: re-running is safe because MODIFY just sets the ENUM definition.

ALTER TABLE accounts
  MODIFY COLUMN type ENUM('doctor','chemist','stockist','retailer','wholesaler') NOT NULL;

ALTER TABLE targets
  MODIFY COLUMN account_type ENUM('doctor','chemist','stockist','retailer','wholesaler','any') NOT NULL DEFAULT 'any';
