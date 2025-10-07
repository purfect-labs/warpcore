-- WARPCORE Security Licensing Database Schema Enhancement
-- Migration script to add security licensing tables
-- WARP-DEMO watermark: Test data includes WARP-DEMO prefixes

-- Create license_keys table with hardware binding support
CREATE TABLE IF NOT EXISTS license_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    license_key TEXT NOT NULL UNIQUE,
    license_type TEXT NOT NULL DEFAULT 'standard',
    hardware_fingerprint TEXT,
    hardware_binding_strict BOOLEAN DEFAULT 0,
    encryption_key TEXT,
    fernet_token TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    max_activations INTEGER DEFAULT 1,
    current_activations INTEGER DEFAULT 0,
    features_json TEXT, -- JSON array of enabled features
    metadata_json TEXT, -- JSON object for additional metadata
    watermark TEXT DEFAULT '' -- WARP-DEMO watermark for test licenses
);

-- Create license_validation_log for comprehensive audit trail
CREATE TABLE IF NOT EXISTS license_validation_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    license_key_id INTEGER,
    validation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    validation_result TEXT NOT NULL, -- 'valid', 'invalid', 'expired', 'revoked'
    validation_details TEXT, -- JSON object with validation specifics
    hardware_fingerprint TEXT,
    ip_address TEXT,
    user_agent TEXT,
    application_version TEXT,
    validation_method TEXT, -- 'api', 'offline', 'batch'
    processing_time_ms INTEGER,
    error_message TEXT,
    watermark TEXT DEFAULT '', -- WARP-DEMO-VALIDATION for test logs
    FOREIGN KEY (license_key_id) REFERENCES license_keys (id)
);

-- Create license_revocation table for blacklist management
CREATE TABLE IF NOT EXISTS license_revocation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    license_key_id INTEGER,
    revoked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    revoked_by TEXT, -- Admin user or system identifier
    revocation_reason TEXT NOT NULL,
    revocation_type TEXT DEFAULT 'manual', -- 'manual', 'automatic', 'emergency'
    is_permanent BOOLEAN DEFAULT 1,
    reinstate_at TIMESTAMP, -- For temporary revocations
    revocation_details TEXT, -- JSON object with additional details
    watermark TEXT DEFAULT '', -- WARP-DEMO-REVOCATION for test data
    FOREIGN KEY (license_key_id) REFERENCES license_keys (id)
);

-- Create security_events table for advanced monitoring
CREATE TABLE IF NOT EXISTS security_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    event_type TEXT NOT NULL, -- 'validation', 'revocation', 'tampering', 'anomaly'
    license_key_id INTEGER,
    severity_level TEXT DEFAULT 'info', -- 'info', 'warning', 'error', 'critical'
    event_data TEXT, -- JSON object with event-specific data
    source_ip TEXT,
    user_agent TEXT,
    hardware_fingerprint TEXT,
    processed BOOLEAN DEFAULT 0,
    alert_sent BOOLEAN DEFAULT 0,
    watermark TEXT DEFAULT '', -- WARP-DEMO-EVENT for test events
    FOREIGN KEY (license_key_id) REFERENCES license_keys (id)
);

-- Create usage_analytics table for monitoring and reporting
CREATE TABLE IF NOT EXISTS usage_analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    license_key_id INTEGER,
    usage_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    feature_accessed TEXT,
    usage_duration_seconds INTEGER,
    request_count INTEGER DEFAULT 1,
    data_transferred_bytes INTEGER DEFAULT 0,
    session_id TEXT,
    user_identifier TEXT,
    application_context TEXT, -- JSON with app-specific context
    performance_metrics TEXT, -- JSON with performance data
    watermark TEXT DEFAULT '', -- WARP-DEMO-USAGE for test analytics
    FOREIGN KEY (license_key_id) REFERENCES license_keys (id)
);

-- Performance optimization indexes
CREATE INDEX IF NOT EXISTS idx_license_keys_active ON license_keys(is_active, expires_at);
CREATE INDEX IF NOT EXISTS idx_license_keys_hardware ON license_keys(hardware_fingerprint);
CREATE INDEX IF NOT EXISTS idx_license_keys_type ON license_keys(license_type);

CREATE INDEX IF NOT EXISTS idx_validation_log_timestamp ON license_validation_log(validation_timestamp);
CREATE INDEX IF NOT EXISTS idx_validation_log_key_id ON license_validation_log(license_key_id);
CREATE INDEX IF NOT EXISTS idx_validation_log_result ON license_validation_log(validation_result);

CREATE INDEX IF NOT EXISTS idx_revocation_active ON license_revocation(license_key_id, is_permanent);
CREATE INDEX IF NOT EXISTS idx_revocation_timestamp ON license_revocation(revoked_at);

CREATE INDEX IF NOT EXISTS idx_security_events_type ON security_events(event_type, event_timestamp);
CREATE INDEX IF NOT EXISTS idx_security_events_severity ON security_events(severity_level, processed);
CREATE INDEX IF NOT EXISTS idx_security_events_license ON security_events(license_key_id);

CREATE INDEX IF NOT EXISTS idx_usage_analytics_timestamp ON usage_analytics(usage_timestamp);
CREATE INDEX IF NOT EXISTS idx_usage_analytics_license ON usage_analytics(license_key_id);
CREATE INDEX IF NOT EXISTS idx_usage_analytics_feature ON usage_analytics(feature_accessed);

-- Insert WARP-DEMO test data for development and testing
INSERT OR REPLACE INTO license_keys (
    license_key, 
    license_type, 
    hardware_fingerprint, 
    features_json, 
    watermark,
    expires_at
) VALUES 
(
    'WARP-DEMO-LICENSE-KEY-12345-ABCDEF', 
    'test', 
    'WARP-DEMO-FINGERPRINT-HARDWARE-001',
    '["basic", "test", "demo"]',
    'WARP-DEMO-TEST-LICENSE',
    datetime('now', '+7 days')
),
(
    'WARP-DEMO-PREMIUM-LICENSE-67890-GHIJK',
    'premium_test',
    'WARP-DEMO-FINGERPRINT-HARDWARE-002', 
    '["basic", "premium", "test", "security"]',
    'WARP-DEMO-PREMIUM-LICENSE',
    datetime('now', '+30 days')
);

-- Insert corresponding validation log entries
INSERT OR REPLACE INTO license_validation_log (
    license_key_id,
    validation_result,
    validation_details,
    hardware_fingerprint,
    watermark
) VALUES
(
    (SELECT id FROM license_keys WHERE license_key = 'WARP-DEMO-LICENSE-KEY-12345-ABCDEF'),
    'valid',
    '{"test_mode": true, "demo_validation": "WARP-DEMO-VALIDATION"}',
    'WARP-DEMO-FINGERPRINT-HARDWARE-001',
    'WARP-DEMO-VALIDATION-LOG'
),
(
    (SELECT id FROM license_keys WHERE license_key = 'WARP-DEMO-PREMIUM-LICENSE-67890-GHIJK'),
    'valid', 
    '{"test_mode": true, "premium_demo": "WARP-DEMO-PREMIUM-VALIDATION"}',
    'WARP-DEMO-FINGERPRINT-HARDWARE-002',
    'WARP-DEMO-VALIDATION-LOG'
);

-- Migration completed successfully
-- WARP-DEMO watermarks have been applied to all test data
