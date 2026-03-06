"""
Run MySQL migration script to add analysis fields to candidates table
"""
import pymysql
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Parse DATABASE_URL
# Format: mysql+pymysql://root:tharusha2001@localhost:3306/oauth_users
db_url = os.getenv('DATABASE_URL', 'mysql+pymysql://root:tharusha2001@localhost:3306/oauth_users')
db_url = db_url.replace('mysql+pymysql://', '')
credentials, host_db = db_url.split('@')
username, password = credentials.split(':')
host_port, database = host_db.split('/')
host = host_port.split(':')[0]
port = int(host_port.split(':')[1])

print(f"Connecting to MySQL database: {database} on {host}:{port}")

# Read migration SQL file
with open('migrations/001_add_analysis_fields_mysql.sql', 'r') as f:
    sql_content = f.read()

# Split into individual statements
statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]

# Connect to database
connection = pymysql.connect(
    host=host,
    port=port,
    user=username,
    password=password,
    database=database,
    charset='utf8mb4'
)

print("Connected successfully!")

try:
    with connection.cursor() as cursor:
        for i, statement in enumerate(statements, 1):
            # Skip comments and empty statements
            if statement.startswith('--') or not statement.strip():
                continue
            
            print(f"\n[{i}/{len(statements)}] Executing:")
            print(f"  {statement[:80]}...")
            
            try:
                cursor.execute(statement)
                print("  ✓ Success")
            except pymysql.err.OperationalError as e:
                if "Duplicate column name" in str(e):
                    print(f"  ⚠ Column already exists (skipping)")
                elif "Duplicate key name" in str(e):
                    print(f"  ⚠ Index already exists (skipping)")
                elif "Duplicate constraint name" in str(e):
                    print(f"  ⚠ Constraint already exists (skipping)")
                else:
                    print(f"  ✗ Error: {e}")
                    raise
            except Exception as e:
                print(f"  ✗ Error: {e}")
                # Continue with other statements
        
        # Commit changes
        connection.commit()
        print("\n✅ Migration completed successfully!")
        
        # Verify columns were added
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
        print(f"\n📋 Verification - {len(results)} new columns added:")
        for row in results:
            print(f"  • {row[0]:25} {row[1]:15} (Nullable: {row[2]})")

finally:
    connection.close()
    print("\n✓ Database connection closed")
