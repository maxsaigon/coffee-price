#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database module for storing coffee price history
Simple SQLite implementation for price tracking and analysis
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class CoffeePriceDB:
    """
    SQLite database for coffee price storage and retrieval
    """
    
    def __init__(self, db_path: str = "coffee_prices.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS coffee_prices (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        coffee_type TEXT NOT NULL,
                        current_price REAL NOT NULL,
                        price_display TEXT,
                        change_value TEXT,
                        change_percent TEXT,
                        volume TEXT,
                        unit TEXT,
                        symbol TEXT,
                        source TEXT DEFAULT 'investing.com',
                        raw_data TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS scraping_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        success_count INTEGER,
                        total_count INTEGER,
                        errors TEXT,
                        duration_seconds REAL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS telegram_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        message_type TEXT,
                        success BOOLEAN,
                        error_message TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for better performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_coffee_type_timestamp ON coffee_prices(coffee_type, timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON coffee_prices(timestamp)")
                
                logger.info(f"Database initialized: {self.db_path}")
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def store_price_data(self, price_data: Dict[str, Any]) -> bool:
        """
        Store scraped price data
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                international_data = price_data.get('international', {})
                
                for coffee_type, data in international_data.items():
                    if 'current_price' in data:
                        conn.execute("""
                            INSERT INTO coffee_prices (
                                timestamp, coffee_type, current_price, price_display,
                                change_value, change_percent, volume, unit, symbol, raw_data
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            data.get('timestamp', datetime.now().isoformat()),
                            coffee_type,
                            data['current_price'],
                            data.get('price_display'),
                            data.get('change'),
                            data.get('change_percent'),
                            data.get('volume'),
                            data.get('unit'),
                            data.get('symbol'),
                            json.dumps(data)
                        ))
                
                # Log scraping session
                conn.execute("""
                    INSERT INTO scraping_logs (
                        timestamp, success_count, total_count, errors
                    ) VALUES (?, ?, ?, ?)
                """, (
                    price_data.get('timestamp', datetime.now().isoformat()),
                    price_data.get('success_count', 0),
                    price_data.get('total_count', 0),
                    json.dumps(price_data.get('errors', []))
                ))
                
                logger.info(f"Stored price data for {len(international_data)} coffee types")
                return True
                
        except Exception as e:
            logger.error(f"Failed to store price data: {e}")
            return False
    
    def get_latest_prices(self) -> Dict[str, Any]:
        """
        Get latest prices for all coffee types
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                cursor = conn.execute("""
                    SELECT coffee_type, current_price, price_display, change_value, 
                           change_percent, volume, unit, symbol, timestamp
                    FROM coffee_prices 
                    WHERE (coffee_type, timestamp) IN (
                        SELECT coffee_type, MAX(timestamp)
                        FROM coffee_prices 
                        GROUP BY coffee_type
                    )
                    ORDER BY coffee_type
                """)
                
                results = {}
                for row in cursor.fetchall():
                    results[row['coffee_type']] = {
                        'current_price': row['current_price'],
                        'price_display': row['price_display'],
                        'change': row['change_value'],
                        'change_percent': row['change_percent'],
                        'volume': row['volume'],
                        'unit': row['unit'],
                        'symbol': row['symbol'],
                        'timestamp': row['timestamp']
                    }
                
                return results
                
        except Exception as e:
            logger.error(f"Failed to get latest prices: {e}")
            return {}
    
    def get_price_history(self, coffee_type: str, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get price history for specific coffee type
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                since_date = (datetime.now() - timedelta(days=days)).isoformat()
                
                cursor = conn.execute("""
                    SELECT timestamp, current_price, change_value, change_percent
                    FROM coffee_prices 
                    WHERE coffee_type = ? AND timestamp >= ?
                    ORDER BY timestamp DESC
                """, (coffee_type, since_date))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to get price history: {e}")
            return []
    
    def get_price_statistics(self, coffee_type: str, days: int = 30) -> Dict[str, Any]:
        """
        Calculate price statistics
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                since_date = (datetime.now() - timedelta(days=days)).isoformat()
                
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as count,
                        AVG(current_price) as avg_price,
                        MIN(current_price) as min_price,
                        MAX(current_price) as max_price,
                        (MAX(current_price) - MIN(current_price)) as price_range
                    FROM coffee_prices 
                    WHERE coffee_type = ? AND timestamp >= ?
                """, (coffee_type, since_date))
                
                row = cursor.fetchone()
                
                if row and row[0] > 0:  # count > 0
                    return {
                        'count': row[0],
                        'average_price': round(row[1], 2) if row[1] else 0,
                        'min_price': row[2] if row[2] else 0,
                        'max_price': row[3] if row[3] else 0,
                        'price_range': round(row[4], 2) if row[4] else 0,
                        'volatility': round((row[4] / row[1]) * 100, 2) if row[1] and row[4] else 0
                    }
                
                return {}
                
        except Exception as e:
            logger.error(f"Failed to calculate statistics: {e}")
            return {}
    
    def log_telegram_message(self, message_type: str, success: bool, error_message: str = None):
        """
        Log Telegram message attempts
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO telegram_logs (
                        timestamp, message_type, success, error_message
                    ) VALUES (?, ?, ?, ?)
                """, (
                    datetime.now().isoformat(),
                    message_type,
                    success,
                    error_message
                ))
                
        except Exception as e:
            logger.error(f"Failed to log Telegram message: {e}")
    
    def get_system_stats(self) -> Dict[str, Any]:
        """
        Get system statistics for monitoring
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Count total records
                cursor = conn.execute("SELECT COUNT(*) FROM coffee_prices")
                total_records = cursor.fetchone()[0]
                
                # Count records by coffee type
                cursor = conn.execute("""
                    SELECT coffee_type, COUNT(*) 
                    FROM coffee_prices 
                    GROUP BY coffee_type
                """)
                records_by_type = dict(cursor.fetchall())
                
                # Get latest scraping session
                cursor = conn.execute("""
                    SELECT timestamp, success_count, total_count 
                    FROM scraping_logs 
                    ORDER BY created_at DESC 
                    LIMIT 1
                """)
                latest_scraping = cursor.fetchone()
                
                # Get Telegram success rate (last 24 hours)
                yesterday = (datetime.now() - timedelta(hours=24)).isoformat()
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful
                    FROM telegram_logs 
                    WHERE timestamp >= ?
                """, (yesterday,))
                telegram_stats = cursor.fetchone()
                
                return {
                    'total_records': total_records,
                    'records_by_type': records_by_type,
                    'latest_scraping': {
                        'timestamp': latest_scraping[0] if latest_scraping else None,
                        'success_count': latest_scraping[1] if latest_scraping else 0,
                        'total_count': latest_scraping[2] if latest_scraping else 0
                    },
                    'telegram_success_rate': {
                        'total': telegram_stats[0] if telegram_stats else 0,
                        'successful': telegram_stats[1] if telegram_stats else 0,
                        'rate': (telegram_stats[1] / telegram_stats[0] * 100) if telegram_stats and telegram_stats[0] > 0 else 0
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to get system stats: {e}")
            return {}
    
    def cleanup_old_records(self, days_to_keep: int = 90) -> int:
        """
        Clean up old records to prevent database bloat
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
                
                # Delete old price records
                cursor = conn.execute("""
                    DELETE FROM coffee_prices 
                    WHERE timestamp < ?
                """, (cutoff_date,))
                
                deleted_count = cursor.rowcount
                logger.info(f"Cleaned up {deleted_count} old price records")
                
                return deleted_count
                
        except Exception as e:
            logger.error(f"Failed to cleanup old records: {e}")
            return 0

def main():
    """Test database functions"""
    db = CoffeePriceDB("test_coffee.db")
    
    # Test data
    test_data = {
        'timestamp': datetime.now().isoformat(),
        'international': {
            'robusta': {
                'current_price': 4250.0,
                'price_display': '$4,250.00',
                'change': '+15.00',
                'change_percent': '+0.35%',
                'unit': 'USD/tonne',
                'symbol': 'LCF',
                'timestamp': datetime.now().isoformat()
            }
        },
        'success_count': 1,
        'total_count': 1
    }
    
    # Store test data
    success = db.store_price_data(test_data)
    print(f"Store test: {'✅' if success else '❌'}")
    
    # Get latest prices
    latest = db.get_latest_prices()
    print(f"Latest prices: {latest}")
    
    # Get statistics
    stats = db.get_price_statistics('robusta')
    print(f"Statistics: {stats}")
    
    # Get system stats
    system_stats = db.get_system_stats()
    print(f"System stats: {system_stats}")

if __name__ == "__main__":
    main()