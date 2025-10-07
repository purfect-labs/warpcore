#!/usr/bin/env python3
"""
License Database for WARPCORE License Server
Simple SQLite database for license storage and management
"""

import sqlite3
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging
import aiosqlite


class LicenseDatabase:
    """Simple SQLite database for license management"""
    
    def __init__(self, config):
        self.config = config
        self.db_path = self._get_db_path()
        self.logger = logging.getLogger(__name__)
        
    def _get_db_path(self) -> str:
        """Get database path based on mode"""
        if self.config.mode == "local":
            return "warp_license_local.db"
        elif self.config.mode == "hybrid":
            return "warp_license_hybrid.db"
        else:
            # For remote mode, this would be PostgreSQL
            return "warp_license_remote.db"
    
    async def initialize(self):
        """Initialize database tables"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Create licenses table
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS licenses (
                        license_id TEXT PRIMARY KEY,
                        user_email TEXT NOT NULL,
                        user_name TEXT NOT NULL,
                        license_key TEXT NOT NULL,
                        license_type TEXT NOT NULL,
                        features TEXT NOT NULL,  -- JSON array
                        expires_date TEXT NOT NULL,
                        created_date TEXT NOT NULL,
                        hardware_signature TEXT,
                        is_active BOOLEAN DEFAULT 1,
                        revoked_date TEXT,
                        revoked_reason TEXT
                    )
                ''')
                
                # Create purchases table
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS purchases (
                        purchase_id TEXT PRIMARY KEY,
                        user_email TEXT NOT NULL,
                        license_type TEXT NOT NULL,
                        amount REAL NOT NULL,
                        currency TEXT DEFAULT 'USD',
                        payment_method TEXT,
                        payment_status TEXT,
                        stripe_payment_id TEXT,
                        created_date TEXT NOT NULL,
                        completed_date TEXT,
                        license_id TEXT,
                        FOREIGN KEY (license_id) REFERENCES licenses (license_id)
                    )
                ''')
                
                # Create users table
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_email TEXT PRIMARY KEY,
                        user_name TEXT NOT NULL,
                        created_date TEXT NOT NULL,
                        last_login_date TEXT,
                        total_purchases INTEGER DEFAULT 0,
                        total_spent REAL DEFAULT 0.0
                    )
                ''')
                
                await db.commit()
                self.logger.info(f"✅ WARP LICENSE DB: Database initialized at {self.db_path}")
                
        except Exception as e:
            self.logger.error(f"❌ WARP LICENSE DB: Database initialization failed: {str(e)}")
            raise e
    
    async def store_license(self, license_id: str, user_email: str, user_name: str,
                           license_key: str, license_type: str, expires_date: datetime,
                           hardware_signature: str, features: List[str]) -> bool:
        """Store a new license"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Insert license
                await db.execute('''
                    INSERT INTO licenses 
                    (license_id, user_email, user_name, license_key, license_type, 
                     features, expires_date, created_date, hardware_signature, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                ''', (
                    license_id, user_email, user_name, license_key, license_type,
                    json.dumps(features), expires_date.isoformat(), 
                    datetime.now().isoformat(), hardware_signature
                ))
                
                # Update or insert user
                await db.execute('''
                    INSERT OR REPLACE INTO users 
                    (user_email, user_name, created_date, total_purchases)
                    VALUES (?, ?, COALESCE((SELECT created_date FROM users WHERE user_email = ?), ?), 
                            COALESCE((SELECT total_purchases FROM users WHERE user_email = ?), 0) + 1)
                ''', (user_email, user_name, user_email, datetime.now().isoformat(), user_email))
                
                await db.commit()
                self.logger.info(f"✅ WARP LICENSE DB: Stored license {license_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ WARP LICENSE DB: Store license failed: {str(e)}")
            return False
    
    async def get_license_by_id(self, license_id: str) -> Optional[Dict[str, Any]]:
        """Get license by ID"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute('''
                    SELECT * FROM licenses WHERE license_id = ? AND is_active = 1
                ''', (license_id,)) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        return {
                            "license_id": row[0],
                            "user_email": row[1],
                            "user_name": row[2],
                            "license_key": row[3],
                            "license_type": row[4],
                            "features": json.loads(row[5]),
                            "expires_date": row[6],
                            "created_date": row[7],
                            "hardware_signature": row[8],
                            "is_active": bool(row[9])
                        }
                    return None
                    
        except Exception as e:
            self.logger.error(f"❌ WARP LICENSE DB: Get license failed: {str(e)}")
            return None
    
    async def get_licenses_by_user(self, user_email: str) -> List[Dict[str, Any]]:
        """Get all licenses for a user"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute('''
                    SELECT * FROM licenses WHERE user_email = ? ORDER BY created_date DESC
                ''', (user_email,)) as cursor:
                    rows = await cursor.fetchall()
                    licenses = []
                    for row in rows:
                        licenses.append({
                            "license_id": row[0],
                            "user_email": row[1],
                            "user_name": row[2],
                            "license_key": row[3],
                            "license_type": row[4],
                            "features": json.loads(row[5]),
                            "expires_date": row[6],
                            "created_date": row[7],
                            "hardware_signature": row[8],
                            "is_active": bool(row[9]),
                            "revoked_date": row[10],
                            "revoked_reason": row[11]
                        })
                    return licenses
                    
        except Exception as e:
            self.logger.error(f"❌ WARP LICENSE DB: Get user licenses failed: {str(e)}")
            return []
    
    async def revoke_license(self, license_id: str, reason: str = "Manual revocation") -> bool:
        """Revoke a license"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    UPDATE licenses 
                    SET is_active = 0, revoked_date = ?, revoked_reason = ?
                    WHERE license_id = ?
                ''', (datetime.now().isoformat(), reason, license_id))
                
                await db.commit()
                self.logger.info(f"🚫 WARP LICENSE DB: Revoked license {license_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ WARP LICENSE DB: Revoke license failed: {str(e)}")
            return False
    
    async def store_purchase(self, purchase_id: str, user_email: str, license_type: str,
                           amount: float, payment_method: str, stripe_payment_id: str = None) -> bool:
        """Store a purchase record"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT INTO purchases 
                    (purchase_id, user_email, license_type, amount, currency, 
                     payment_method, payment_status, stripe_payment_id, created_date)
                    VALUES (?, ?, ?, ?, 'USD', ?, 'pending', ?, ?)
                ''', (
                    purchase_id, user_email, license_type, amount, 
                    payment_method, stripe_payment_id, datetime.now().isoformat()
                ))
                
                await db.commit()
                self.logger.info(f"💳 WARP LICENSE DB: Stored purchase {purchase_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ WARP LICENSE DB: Store purchase failed: {str(e)}")
            return False
    
    async def update_purchase_status(self, purchase_id: str, status: str, license_id: str = None) -> bool:
        """Update purchase status"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                if license_id:
                    await db.execute('''
                        UPDATE purchases 
                        SET payment_status = ?, completed_date = ?, license_id = ?
                        WHERE purchase_id = ?
                    ''', (status, datetime.now().isoformat(), license_id, purchase_id))
                else:
                    await db.execute('''
                        UPDATE purchases 
                        SET payment_status = ?
                        WHERE purchase_id = ?
                    ''', (status, purchase_id))
                
                await db.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"❌ WARP LICENSE DB: Update purchase status failed: {str(e)}")
            return False