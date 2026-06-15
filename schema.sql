CREATE DATABASE IF NOT EXISTS sales_tracker
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE sales_tracker;

CREATE TABLE IF NOT EXISTS employees (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  name          VARCHAR(120) NOT NULL,
  email         VARCHAR(190) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role          ENUM('employee','admin') NOT NULL DEFAULT 'employee',
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS planned_visits (
  id                  INT AUTO_INCREMENT PRIMARY KEY,
  employee_id         INT NOT NULL,
  plan_date           DATE NOT NULL,
  planned_place_name  VARCHAR(255) NOT NULL,
  planned_lat         DOUBLE NULL,
  planned_lon         DOUBLE NULL,
  notes               VARCHAR(500) NULL,
  created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uniq_emp_date (employee_id, plan_date),
  FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS checkins (
  id                 INT AUTO_INCREMENT PRIMARY KEY,
  employee_id        INT NOT NULL,
  plan_id            INT NULL,
  checkin_time       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  source             ENUM('gps','manual') NOT NULL,
  actual_place_name  VARCHAR(255) NULL,
  actual_lat         DOUBLE NULL,
  actual_lon         DOUBLE NULL,
  distance_km        DOUBLE NULL,
  text_similarity    DOUBLE NULL,
  match_score        DOUBLE NULL,
  matched            TINYINT(1) NOT NULL DEFAULT 0,
  FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
  FOREIGN KEY (plan_id) REFERENCES planned_visits(id) ON DELETE SET NULL,
  INDEX idx_emp_time (employee_id, checkin_time)
);

CREATE TABLE IF NOT EXISTS anomaly_flags (
  id           INT AUTO_INCREMENT PRIMARY KEY,
  employee_id  INT NOT NULL,
  checkin_id   INT NOT NULL,
  score        DOUBLE NULL,
  reason       VARCHAR(255) NULL,
  created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
  FOREIGN KEY (checkin_id)  REFERENCES checkins(id)  ON DELETE CASCADE
);

-- Seed admin (password: admin123 — change after first login)
-- Hash generated with werkzeug.security.generate_password_hash('admin123', method='pbkdf2:sha256')
INSERT IGNORE INTO employees (name, email, password_hash, role) VALUES
  ('Admin', 'admin@example.com',
   'pbkdf2:sha256:600000$placeholder$placeholder',
   'admin');
-- NOTE: run scripts/seed_admin.py after creating tables to set a real password hash.
