"""
Add missing latest_analysis_date column and index
"""
import pymysql
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Parse DATABASE_URL
db_url = os.getenv('DATABASE_URL', 'mysql+pymysql://root:tharusha2001@localhost:3306/oauth_users')
db_url = db_url.replace('mysql+pymysql://', '')
credentials, host_db = db_url.split('@')
username, password = credentials.split(':')
host_port, database = host_db.split('/')
host = host_port.split(':')[0]
port = int(host_port.split(':')[1])

print(f"Adding remaining migration items to: {database}")

# Connect to database
connection = pymysql.connect(
    host=host,
    port=port,
    user=username,
    password=password,
    database=database,
    charset='utf8mb4'
)

try:
    with connection.cursor() as cursor:
        # Add latest_analysis_date column
        print("\n1. Adding latest_analysis_date column...")
        try:
            cursor.execute("""
                ALTER TABLE candidates 
                ADD COLUMN latest_analysis_date DATETIME NULL
            """)
            print("  ✓ Column added")
        except pymysql.err.OperationalError as e:
            if "Duplicate column name" in str(e):
                print("  ⚠ Column already exists")
            else:
                raise
        
        # Add index
        print("\n2. Creating index on latest_analysis_date...")
        try:
            cursor.execute("""
                CREATE INDEX idx_candidates_latest_analysis_date 
                ON candidates(latest_analysis_date)
            """)
            print("  ✓ Index created")
        except pymysql.err.OperationalError as e:
            if "Duplicate key name" in str(e):
                print("  ⚠ Index already exists")
            else:
                raise
        
        # Add check constraint (MySQL 8.0.16+)
        print("\n3. Adding check constraint for readiness_score...")
        try:
            cursor.execute("""
                ALTER TABLE candidates 
                ADD CONSTRAINT chk_readiness_score 
                CHECK (readiness_score IS NULL OR (readiness_score >= 0 AND readiness_score <= 100))
            """)
            print("  ✓ Constraint added")
        except pymysql.err.OperationalError as e:
            if "Duplicate constraint name" in str(e):
                print("  ⚠ Constraint already exists")
            elif "CHECK constraint" in str(e) or "doesn't exist" in str(e):
                print("  ⚠ CHECK constraints not supported (MySQL < 8.0.16)")
            else:
                raise
        
        # Commit changes
        connection.commit()
        print("\n✅ All migration items completed!")
        
        # Final verification
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = %s
            AND table_name = 'candidates'
            AND column_name IN (
                'latest_analysis_date',
                'readiness_score', 
                'skill_gap_index',
                'ai_explanation',
                'matched_skills',
                'missing_skills',
                'analysis_summary'
            )
            ORDER BY column_name
        """, (database,))
        
        results = cursor.fetchall()
        print(f"\n📋 Final verification - {len(results)}/7 columns present:")
        for row in results:
            print(f"  ✓ {row[0]:25} {row[1]:15} (Nullable: {row[2]})")

finally:
    connection.close()
    print("\n✓ Database connection closed")
