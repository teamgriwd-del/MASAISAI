-- MASAISAI Phase-1 schema (proposal Section 2.3)
CREATE DATABASE IF NOT EXISTS masaisai CHARACTER SET utf8mb4;
USE masaisai;

CREATE TABLE IF NOT EXISTS sensing_readings (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    node_id VARCHAR(64) NOT NULL,
    channel VARCHAR(16) NOT NULL,
    timestamp DATETIME(3) NOT NULL,
    rssi_dbm FLOAT NOT NULL,
    occupied TINYINT(1) NOT NULL,
    sensing_confidence FLOAT NOT NULL,
    INDEX idx_node_channel_ts (node_id, channel, timestamp)
);

CREATE TABLE IF NOT EXISTS access_decisions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    node_id VARCHAR(64) NOT NULL,
    channel VARCHAR(16) NOT NULL,
    timestamp DATETIME(3) NOT NULL,
    granted TINYINT(1) NOT NULL,
    reason VARCHAR(512) NOT NULL,
    ml_probability FLOAT NULL,
    sensing_confidence FLOAT NULL,
    expires_at DATETIME(3) NULL,
    INDEX idx_ts (timestamp)
);

CREATE TABLE IF NOT EXISTS znfap_rules (
    channel VARCHAR(16) PRIMARY KEY,
    protected TINYINT(1) NOT NULL DEFAULT 0,
    exclusion_zone_id VARCHAR(64) NULL,
    source_version VARCHAR(64) NOT NULL DEFAULT 'PLACEHOLDER-v1'
);
