#!/usr/bin/env python3
"""
Database Migration Script for Employee Video Table

This script adds the employee_video table to the existing SQLite database
to support the new video upload functionality.

Usage:
    python migrate_video_table.py
"""

import sqlite3
import os
import sys

def migrate_database():
    """Add the employee_video table to the database."""
    
    # Database file path (relative to the script location)
    db_path = 'instance/ourteam.db'
    
    # Check if database file exists
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        print("Please make sure you're running this script from the project root directory.")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the table already exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='employee_video'
        """)
        
        if cursor.fetchone():
            print("Table 'employee_video' already exists. Migration not needed.")
            conn.close()
            return True
        
        # Create the employee_video table
        cursor.execute("""
            CREATE TABLE employee_video (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_url VARCHAR(500) NOT NULL,
                employee_id INTEGER NOT NULL,
                caption VARCHAR(255),
                thumbnail_url VARCHAR(500),
                FOREIGN KEY (employee_id) REFERENCES employee (id)
            )
        """)
        
        # Commit the changes
        conn.commit()
        conn.close()
        
        print("✅ Successfully created employee_video table!")
        print("Migration completed successfully.")
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def verify_migration():
    """Verify that the migration was successful."""
    
    db_path = 'instance/ourteam.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='employee_video'
        """)
        
        if cursor.fetchone():
            # Get table schema
            cursor.execute("PRAGMA table_info(employee_video)")
            columns = cursor.fetchall()
            
            print("\n📋 Table schema verification:")
            print("employee_video table columns:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
            
            conn.close()
            return True
        else:
            print("❌ Table verification failed: employee_video table not found")
            conn.close()
            return False
            
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Starting database migration for employee_video table...")
    print("=" * 50)
    
    # Run migration
    if migrate_database():
        print("\n🔍 Verifying migration...")
        if verify_migration():
            print("\n✅ Migration completed and verified successfully!")
            print("You can now use the video upload functionality.")
        else:
            print("\n❌ Migration verification failed!")
            sys.exit(1)
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)
