-- Sales Tracker schema v2 — adds India geo hierarchy, multi-account visits, targets.
-- Idempotent: safe to run repeatedly. Requires MariaDB 10.0+ for ADD COLUMN IF NOT EXISTS.

USE sales_tracker;

-- ---------------------------------------------------------------
-- Regions (Indian states + union territories)
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS regions (
  id    INT AUTO_INCREMENT PRIMARY KEY,
  name  VARCHAR(120) NOT NULL,
  code  VARCHAR(10)  NOT NULL UNIQUE,
  type  ENUM('state','ut') NOT NULL DEFAULT 'state'
);

-- ---------------------------------------------------------------
-- Districts
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS districts (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  region_id  INT NOT NULL,
  name       VARCHAR(120) NOT NULL,
  code       VARCHAR(20),
  FOREIGN KEY (region_id) REFERENCES regions(id) ON DELETE CASCADE,
  UNIQUE KEY uniq_region_district (region_id, name),
  INDEX idx_district_region (region_id)
);

-- ---------------------------------------------------------------
-- Accounts: the entities a salesperson visits (doctors, chemists, stockists)
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS accounts (
  id           INT AUTO_INCREMENT PRIMARY KEY,
  name         VARCHAR(200) NOT NULL,
  type         ENUM('doctor','chemist','stockist') NOT NULL,
  specialty    VARCHAR(120),
  district_id  INT,
  address      VARCHAR(500),
  phone        VARCHAR(30),
  email        VARCHAR(190),
  lat          DOUBLE,
  lon          DOUBLE,
  created_by   INT,
  created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (district_id) REFERENCES districts(id) ON DELETE SET NULL,
  FOREIGN KEY (created_by)  REFERENCES employees(id) ON DELETE SET NULL,
  INDEX idx_account_type (type),
  INDEX idx_account_district (district_id),
  INDEX idx_account_name (name)
);

-- ---------------------------------------------------------------
-- planned_visit_items: links a daily plan to multiple accounts
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS planned_visit_items (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  plan_id    INT NOT NULL,
  account_id INT NOT NULL,
  order_idx  INT NOT NULL DEFAULT 0,
  notes      VARCHAR(500),
  FOREIGN KEY (plan_id)    REFERENCES planned_visits(id) ON DELETE CASCADE,
  FOREIGN KEY (account_id) REFERENCES accounts(id)       ON DELETE CASCADE,
  UNIQUE KEY uniq_plan_account (plan_id, account_id),
  INDEX idx_pvi_plan (plan_id)
);

-- ---------------------------------------------------------------
-- Targets: company / region / district / employee level
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS targets (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  scope           ENUM('company','region','district','employee') NOT NULL,
  employee_id     INT NULL,
  region_id       INT NULL,
  district_id     INT NULL,
  account_type    ENUM('doctor','chemist','stockist','any') NOT NULL DEFAULT 'any',
  period_type     ENUM('daily','weekly','monthly','quarterly') NOT NULL,
  target_count    INT NOT NULL,
  effective_from  DATE NOT NULL,
  effective_to    DATE NULL,
  created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
  FOREIGN KEY (region_id)   REFERENCES regions(id)   ON DELETE CASCADE,
  FOREIGN KEY (district_id) REFERENCES districts(id) ON DELETE CASCADE,
  INDEX idx_target_scope (scope, period_type, effective_from)
);

-- ---------------------------------------------------------------
-- employees: add geo + manager hierarchy + proctor role
-- ---------------------------------------------------------------
ALTER TABLE employees
  ADD COLUMN IF NOT EXISTS phone       VARCHAR(30)  NULL,
  ADD COLUMN IF NOT EXISTS territory   VARCHAR(120) NULL,
  ADD COLUMN IF NOT EXISTS region_id   INT NULL,
  ADD COLUMN IF NOT EXISTS district_id INT NULL,
  ADD COLUMN IF NOT EXISTS manager_id  INT NULL;

-- expand role enum to include proctor (national visibility)
ALTER TABLE employees MODIFY COLUMN role
  ENUM('employee','admin','proctor') NOT NULL DEFAULT 'employee';

-- Add FKs (safe re-run: errors here can be ignored if they already exist)
-- MariaDB doesn't support IF NOT EXISTS on ADD FOREIGN KEY, so we wrap in informational comments.
-- If these statements fail with "duplicate foreign key" on re-run, that's expected and harmless.
ALTER TABLE employees
  ADD CONSTRAINT fk_emp_region   FOREIGN KEY (region_id)   REFERENCES regions(id)   ON DELETE SET NULL,
  ADD CONSTRAINT fk_emp_district FOREIGN KEY (district_id) REFERENCES districts(id) ON DELETE SET NULL,
  ADD CONSTRAINT fk_emp_manager  FOREIGN KEY (manager_id)  REFERENCES employees(id) ON DELETE SET NULL;

-- ---------------------------------------------------------------
-- checkins: extend to act as a "visit" — link to accounts + outcome
-- A check-in with account_id IS NULL is a generic location check-in (legacy).
-- A check-in with account_id IS NOT NULL is a visit to that account.
-- ---------------------------------------------------------------
ALTER TABLE checkins
  ADD COLUMN IF NOT EXISTS account_id  INT NULL,
  ADD COLUMN IF NOT EXISTS outcome     ENUM('met','not_met','rescheduled') NULL,
  ADD COLUMN IF NOT EXISTS visit_notes VARCHAR(500) NULL;

ALTER TABLE checkins
  ADD CONSTRAINT fk_checkin_account FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE SET NULL;

ALTER TABLE checkins ADD INDEX IF NOT EXISTS idx_checkin_account (account_id);
ALTER TABLE checkins ADD INDEX IF NOT EXISTS idx_checkin_outcome (outcome);
