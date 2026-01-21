"""
Migration script to push local SQLite data to Railway PostgreSQL
"""
import sqlite3
import psycopg2
from datetime import datetime

# Railway PostgreSQL URL
RAILWAY_URL = "postgresql://postgres:SJvhACdMXPwVSfFPFqJkfPlBIuNHsETI@switchyard.proxy.rlwy.net:33847/railway"

def migrate():
    # Connect to local SQLite
    sqlite_conn = sqlite3.connect('newsletter.db')
    sqlite_cursor = sqlite_conn.cursor()
    
    # Get all newsletters from local DB
    sqlite_cursor.execute("""
        SELECT newsletter_id, week_number, date_start, date_end, content_json, created_at 
        FROM newsletters
    """)
    rows = sqlite_cursor.fetchall()
    
    print(f"📦 Found {len(rows)} newsletters to migrate")
    
    # Connect to Railway PostgreSQL
    pg_conn = psycopg2.connect(RAILWAY_URL)
    pg_cursor = pg_conn.cursor()
    
    # Create table if not exists
    pg_cursor.execute("""
        CREATE TABLE IF NOT EXISTS newsletters (
            id SERIAL PRIMARY KEY,
            newsletter_id VARCHAR(255),
            week_number INTEGER,
            date_start VARCHAR(255),
            date_end VARCHAR(255),
            content_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    pg_conn.commit()
    
    # Insert each newsletter
    for row in rows:
        newsletter_id, week_number, date_start, date_end, content_json, created_at = row
        
        # Check if already exists
        pg_cursor.execute(
            "SELECT id FROM newsletters WHERE newsletter_id = %s AND week_number = %s",
            (newsletter_id, week_number)
        )
        if pg_cursor.fetchone():
            print(f"⏭️  Skipping week {week_number} (already exists)")
            continue
        
        pg_cursor.execute("""
            INSERT INTO newsletters (newsletter_id, week_number, date_start, date_end, content_json, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (newsletter_id, week_number, date_start, date_end, content_json, created_at))
        
        print(f"✅ Migrated week {week_number}")
    
    pg_conn.commit()
    
    # Verify
    pg_cursor.execute("SELECT COUNT(*) FROM newsletters")
    count = pg_cursor.fetchone()[0]
    print(f"\n🎉 Migration complete! {count} newsletters in Railway PostgreSQL")
    
    sqlite_conn.close()
    pg_conn.close()

if __name__ == "__main__":
    migrate()
