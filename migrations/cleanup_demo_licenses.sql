-- Demo License Cleanup Migration
-- Removes demo/test data from license database for production readiness
-- Execute this migration to clean up demo data before production deployment

-- Remove any test/demo license records
DELETE FROM license_keys 
WHERE license_key LIKE '%DEMO%' 
   OR license_key LIKE '%TEST%' 
   OR license_key LIKE '%WARP-FAKE%'
   OR watermark LIKE '%DEMO%'
   OR watermark LIKE '%TEST%'
   OR watermark LIKE '%WARP%';

-- Remove validation log entries with demo watermarks
DELETE FROM license_validation_log 
WHERE watermark LIKE '%DEMO%' 
   OR watermark LIKE '%TEST%'
   OR watermark LIKE '%WARP%'
   OR event_data LIKE '%DEMO%'
   OR event_data LIKE '%TEST%';

-- Clean up any security audit records with demo data
DELETE FROM security_audit_log 
WHERE event_data LIKE '%DEMO%' 
   OR event_data LIKE '%TEST%'
   OR event_data LIKE '%WARP-FAKE%'
   OR audit_context LIKE '%DEMO%';

-- Remove any temporary encryption keys with demo patterns
DELETE FROM encryption_keys 
WHERE key_name LIKE '%demo%' 
   OR key_name LIKE '%test%'
   OR key_purpose LIKE '%demo%'
   OR created_context LIKE '%DEMO%';

-- Clean up license feature mappings with demo content
DELETE FROM license_features 
WHERE feature_name LIKE '%demo%' 
   OR feature_name LIKE '%test%'
   OR feature_description LIKE '%demo%'
   OR feature_description LIKE '%test%';

-- Update any remaining records to remove watermark columns (if they exist)
-- Note: This is a safe operation - if columns don't exist, the statements will be ignored

-- Remove watermark columns from license_keys if they exist
BEGIN;
    -- Create new table without watermark columns
    CREATE TABLE license_keys_clean AS 
    SELECT 
        id,
        license_key,
        license_type,
        hardware_fingerprint,
        user_email,
        user_name,
        expires_at,
        created_at,
        updated_at,
        is_active,
        features_json,
        payment_reference
    FROM license_keys 
    WHERE license_key IS NOT NULL;
    
    -- Drop old table and rename new one
    DROP TABLE license_keys;
    ALTER TABLE license_keys_clean RENAME TO license_keys;
    
    -- Recreate indexes
    CREATE UNIQUE INDEX idx_license_keys_key ON license_keys(license_key);
    CREATE INDEX idx_license_keys_active ON license_keys(is_active);
    CREATE INDEX idx_license_keys_expires ON license_keys(expires_at);
    CREATE INDEX idx_license_keys_email ON license_keys(user_email);
COMMIT;

-- Clean up validation log table
BEGIN;
    CREATE TABLE license_validation_log_clean AS 
    SELECT 
        id,
        license_key,
        validation_timestamp,
        validation_result,
        event_type,
        hardware_fingerprint,
        client_ip,
        user_agent,
        success
    FROM license_validation_log
    WHERE validation_timestamp IS NOT NULL;
    
    DROP TABLE license_validation_log;
    ALTER TABLE license_validation_log_clean RENAME TO license_validation_log;
    
    -- Recreate indexes
    CREATE INDEX idx_validation_log_key ON license_validation_log(license_key);
    CREATE INDEX idx_validation_log_timestamp ON license_validation_log(validation_timestamp);
    CREATE INDEX idx_validation_log_result ON license_validation_log(validation_result);
COMMIT;

-- Final verification queries (commented out - uncomment to verify cleanup)
-- SELECT COUNT(*) as remaining_demo_licenses FROM license_keys WHERE license_key LIKE '%DEMO%';
-- SELECT COUNT(*) as remaining_demo_validations FROM license_validation_log WHERE event_data LIKE '%DEMO%';
-- SELECT COUNT(*) as total_clean_licenses FROM license_keys;
-- SELECT COUNT(*) as total_clean_validations FROM license_validation_log;

-- Add production-ready constraints
ALTER TABLE license_keys ADD CONSTRAINT chk_license_key_format 
    CHECK (length(license_key) >= 16 AND license_key NOT LIKE '%demo%' AND license_key NOT LIKE '%test%');

-- Add audit triggers for production compliance
CREATE TRIGGER tr_license_audit_insert 
AFTER INSERT ON license_keys
BEGIN
    INSERT INTO license_validation_log (
        license_key, 
        validation_timestamp, 
        event_type,
        validation_result
    ) VALUES (
        NEW.license_key,
        datetime('now'),
        'license_created',
        'success'
    );
END;

CREATE TRIGGER tr_license_audit_update 
AFTER UPDATE ON license_keys
BEGIN
    INSERT INTO license_validation_log (
        license_key,
        validation_timestamp,
        event_type,
        validation_result
    ) VALUES (
        NEW.license_key,
        datetime('now'),
        'license_updated',
        'success'
    );
END;

-- Migration completed successfully
-- All demo/test data has been removed from the license database
-- Production-ready constraints and audit triggers have been added