-- Reference schema (the app also creates these tables on startup).
CREATE DATABASE IF NOT EXISTS listing_reviewer CHARACTER SET utf8mb4;
USE listing_reviewer;
CREATE TABLE IF NOT EXISTS listings (
  id INT AUTO_INCREMENT PRIMARY KEY, title VARCHAR(500) NOT NULL, description TEXT, category VARCHAR(100),
  price VARCHAR(32), attributes TEXT, seller VARCHAR(200), tags TEXT, created_at BIGINT NOT NULL
) ENGINE=InnoDB;  -- price is VARCHAR on purpose: invalid input must be storable so validation can report it
CREATE TABLE IF NOT EXISTS reviews (
  id INT AUTO_INCREMENT PRIMARY KEY, listing_id INT NOT NULL, mode VARCHAR(16) NOT NULL, note TEXT,
  dropped INT NOT NULL DEFAULT 0, validation LONGTEXT, findings LONGTEXT, retrieved LONGTEXT, created_at BIGINT NOT NULL,
  FOREIGN KEY (listing_id) REFERENCES listings(id)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS revisions (
  id INT AUTO_INCREMENT PRIMARY KEY, review_id INT NOT NULL, listing_id INT NOT NULL, field_name VARCHAR(32) NOT NULL,
  original TEXT, suggested TEXT, final_text TEXT, status VARCHAR(16) NOT NULL DEFAULT 'pending', updated_at BIGINT NOT NULL,
  FOREIGN KEY (review_id) REFERENCES reviews(id)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS history_events (  -- append-only audit trail
  id INT AUTO_INCREMENT PRIMARY KEY, listing_id INT NOT NULL, review_id INT NULL, field_name VARCHAR(32),
  action VARCHAR(40) NOT NULL, before_text TEXT, after_text TEXT, created_at BIGINT NOT NULL
) ENGINE=InnoDB;
