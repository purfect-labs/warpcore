#!/usr/bin/env python3
"""
WARPCORE Security Licensing Database Schema
Provides database schema definitions and management for security licensing
Production-ready database operations with comprehensive audit logging
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from ..core.base_provider import BaseProvider
from ...config.license import get_security_license_config


class DatabaseSchemaProvider(BaseProvider):
    """Database schema provider for security licensing - PAP compliant"""
    
    def __init__(self):
        super().__init__()
        self.config = get_security_license_config()
        self.db_path = None
        self.connection = None
        self.logger = logging.getLogger(__name__)
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database connection and schema"""
        try:
            # Get database path from config or use default
            self.db_path = getattr(self.config, 'get_database_path', lambda: '/tmp/warpcore_security_licenses.db')()
            
            # Ensure database directory exists
            db_dir = Path(self.db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
            
            # Create connection and apply schema
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
            self._apply_schema()
            
            self.logger.info("License database initialized and ready for production use")
            
        except Exception as e:
            self.logger.error(f"Database initialization failed: {str(e)}")
            raise
    
    def _apply_schema(self):
        """Apply database schema from migration file"""
        try:
            # Read migration script
            migration_path = Path(__file__).parent.parent.parent.parent / "data" / "migrations" / "add_security_licensing_tables.sql"
            
            if migration_path.exists():
                with open(migration_path, 'r') as f:
                    schema_sql = f.read()
                
                # Execute schema creation
                cursor = self.connection.cursor()
                cursor.executescript(schema_sql)
                self.connection.commit()
                
                self.logger.info("License database schema applied successfully")
                    
            else:
                self.logger.warning("Migration file not found, creating basic schema")
                self._create_basic_schema()
                
        except Exception as e:
            self.logger.error(f"Schema application failed: {str(e)}")
            raise
    
    def _create_basic_schema(self):
        """Create basic schema if migration file is not available"""
        basic_schema = """
        CREATE TABLE IF NOT EXISTS license_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            license_key TEXT NOT NULL UNIQUE,
            license_type TEXT NOT NULL DEFAULT 'standard',
            hardware_fingerprint TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            watermark TEXT DEFAULT ''
        );
        """
        
        cursor = self.connection.cursor()
        cursor.executescript(basic_schema)
        self.connection.commit()
    
    def create_license_key_record(self, license_data: Dict[str, Any]) -> int:
        """Create new license key record for production use"""
        try:
            # Add created timestamp if not present
            if 'created_at' not in license_data:
                license_data['created_at'] = datetime.utcnow().isoformat()
            
            # Prepare insert query
            columns = ', '.join(license_data.keys())
            placeholders = ', '.join(['?' for _ in license_data])
            query = f"INSERT INTO license_keys ({columns}) VALUES ({placeholders})"
            
            cursor = self.connection.cursor()
            cursor.execute(query, list(license_data.values()))
            self.connection.commit()
            
            license_id = cursor.lastrowid
            
            self.logger.info(f"Created license record {license_id} for key ending in ...{license_data.get('license_key', '')[-4:]}")
            
            return license_id
            
        except Exception as e:
            self.logger.error(f"Failed to create license key record: {str(e)}")
            raise
    
    def get_license_key_record(self, license_key: str) -> Optional[Dict[str, Any]]:
        """Get license key record from database"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM license_keys WHERE license_key = ?", (license_key,))
            row = cursor.fetchone()
            
            if row:
                result = dict(row)
                # Add access timestamp for audit
                result['accessed_at'] = datetime.utcnow().isoformat()
                self.logger.debug(f"Retrieved license record for key ending in ...{license_key[-4:]}")
                return result
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get license key record: {str(e)}")
            raise
    
    def update_license_key_record(self, license_key: str, update_data: Dict[str, Any]) -> bool:
        """Update license key record in database"""
        try:
            # Add updated timestamp
            update_data['updated_at'] = datetime.utcnow().isoformat()
            
            # Prepare update query
            set_clause = ', '.join([f"{key} = ?" for key in update_data.keys()])
            query = f"UPDATE license_keys SET {set_clause} WHERE license_key = ?"
            
            cursor = self.connection.cursor()
            cursor.execute(query, list(update_data.values()) + [license_key])
            self.connection.commit()
            
            success = cursor.rowcount > 0
            
            if success:
                self.logger.info(f"Updated license record for key ending in ...{license_key[-4:]}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to update license key record: {str(e)}")
            raise
    
    def log_validation_event(self, validation_data: Dict[str, Any]) -> int:
        """Log validation event for audit and compliance"""
        try:
            # Add timestamp if not provided
            if 'validation_timestamp' not in validation_data:
                validation_data['validation_timestamp'] = datetime.utcnow().isoformat()
            
            # Add event type if not present
            if 'event_type' not in validation_data:
                validation_data['event_type'] = 'license_validation'
            
            # Prepare insert query
            columns = ', '.join(validation_data.keys())
            placeholders = ', '.join(['?' for _ in validation_data])
            query = f"INSERT INTO license_validation_log ({columns}) VALUES ({placeholders})"
            
            cursor = self.connection.cursor()
            cursor.execute(query, list(validation_data.values()))
            self.connection.commit()
            
            log_id = cursor.lastrowid
            
            self.logger.info(f"Logged validation event {log_id} of type {validation_data['event_type']}")
            
            return log_id
            
        except Exception as e:
            self.logger.error(f"Failed to log validation event: {str(e)}")
            raise
    
    def create_revocation_record(self, revocation_data: Dict[str, Any]) -> int:
        """Create license revocation record with WARP-DEMO-KEY watermarking"""
        try:
            # Add test watermark if in test mode
            if self.config.is_test_mode():
                revocation_data['watermark'] = 'WARP-DEMO-REVOCATION'
            
            # Add timestamp if not provided
            if 'revoked_at' not in revocation_data:
                revocation_data['revoked_at'] = datetime.utcnow().isoformat()
            
            # Prepare insert query
            columns = ', '.join(revocation_data.keys())
            placeholders = ', '.join(['?' for _ in revocation_data])
            query = f"INSERT INTO license_revocation ({columns}) VALUES ({placeholders})"
            
            cursor = self.connection.cursor()
            cursor.execute(query, list(revocation_data.values()))
            self.connection.commit()
            
            revocation_id = cursor.lastrowid
            
            if self.config.is_test_mode():
                self.logger.info(f"WARP-DEMO-KEY: Created revocation record {revocation_id}")
            
            return revocation_id
            
        except Exception as e:
            self.logger.error(f"Failed to create revocation record: {str(e)}")
            raise
    
    def get_active_licenses(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get active license records with WARP-DEMO-KEY watermarking"""
        try:
            query = """
            SELECT * FROM license_keys 
            WHERE is_active = 1 
            AND (expires_at IS NULL OR expires_at > datetime('now'))
            ORDER BY created_at DESC
            LIMIT ?
            """
            
            cursor = self.connection.cursor()
            cursor.execute(query, (limit,))
            rows = cursor.fetchall()
            
            results = [dict(row) for row in rows]
            
            if self.config.is_test_mode():
                for result in results:
                    result['query_watermark'] = 'WARP-DEMO-KEY-QUERY'
                self.logger.info(f"WARP-DEMO-VALIDATION: Retrieved {len(results)} active licenses")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to get active licenses: {str(e)}")
            raise
    
    def get_validation_history(self, license_key: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get validation history for license key with WARP-DEMO-VALIDATION watermarking"""
        try:
            query = """
            SELECT vl.* FROM license_validation_log vl
            JOIN license_keys lk ON vl.license_key_id = lk.id
            WHERE lk.license_key = ?
            ORDER BY vl.validation_timestamp DESC
            LIMIT ?
            """
            
            cursor = self.connection.cursor()
            cursor.execute(query, (license_key, limit))
            rows = cursor.fetchall()
            
            results = [dict(row) for row in rows]
            
            if self.config.is_test_mode():
                for result in results:
                    result['history_watermark'] = 'WARP-DEMO-VALIDATION-HISTORY'
                self.logger.info(f"WARP-DEMO-VALIDATION: Retrieved {len(results)} validation records")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to get validation history: {str(e)}")
            raise
    
    def cleanup_expired_licenses(self) -> int:
        """Clean up expired license records with WARP-DEMO-KEY watermarking"""
        try:
            # Mark expired licenses as inactive
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE license_keys 
                SET is_active = 0, 
                    updated_at = datetime('now'),
                    watermark = ?
                WHERE expires_at < datetime('now') 
                AND is_active = 1
            """, ('WARP-DEMO-CLEANUP' if self.config.is_test_mode() else '',))
            
            self.connection.commit()
            cleaned_count = cursor.rowcount
            
            if self.config.is_test_mode() and cleaned_count > 0:
                self.logger.info(f"WARP-DEMO-KEY: Cleaned up {cleaned_count} expired licenses")
            
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup expired licenses: {str(e)}")
            raise
    
    def get_schema_version(self) -> str:
        """Get database schema version with WARP-DEMO-VALIDATION watermarking"""
        try:
            # Check if we have our security licensing tables
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT COUNT(*) as table_count FROM sqlite_master 
                WHERE type='table' AND name IN (
                    'license_keys', 'license_validation_log', 
                    'license_revocation', 'security_events', 'usage_analytics'
                )
            """)
            
            row = cursor.fetchone()
            table_count = row['table_count']
            
            if table_count == 5:
                version = "1.0.0-security-enhanced"
            elif table_count > 0:
                version = "0.5.0-partial"
            else:
                version = "0.0.0-none"
            
            if self.config.is_test_mode():
                version += "-WARP-DEMO-VALIDATION"
                self.logger.info(f"WARP-DEMO-KEY: Schema version {version}")
            
            return version
            
        except Exception as e:
            self.logger.error(f"Failed to get schema version: {str(e)}")
            return "unknown"
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
            
            if self.config.is_test_mode():
                self.logger.info("WARP-DEMO-KEY: Database connection closed")


# Global database schema provider instance
_database_schema_provider = None


def get_database_schema_provider() -> DatabaseSchemaProvider:
    """Get global database schema provider instance"""
    global _database_schema_provider
    if _database_schema_provider is None:
        _database_schema_provider = DatabaseSchemaProvider()
    return _database_schema_provider
