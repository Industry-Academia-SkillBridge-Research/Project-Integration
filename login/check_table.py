"""
Check candidates table structure
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

print(f"Checking database: {database}")

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
        # Check if candidates table exists
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = %s AND table_name = 'candidates'
        """, (database,))
        
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            print("✓ 'candidates' table exists")
            
            # Get all columns
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = 'candidates'
                ORDER BY ordinal_position
            """, (database,))
            
            columns = cursor.fetchall()
            print(f"\n📋 Table structure ({len(columns)} columns):")
            for col in columns:
                default = f" DEFAULT {col[3]}" if col[3] else ""
                print(f"  • {col[0]:30} {col[1]:15} {col[2]:5}{default}")
            
            # Check for analysis columns specifically
            analysis_cols = [
                'latest_analysis_date',
                'readiness_score', 
                'skill_gap_index',
                'ai_explanation',
                'matched_skills',
                'missing_skills',
                'analysis_summary'
            ]
            
            existing_analysis = [col[0] for col in columns if col[0] in analysis_cols]
            
            print(f"\n🔍 Analysis columns status:")
            for ac in analysis_cols:
                status = "✓ EXISTS" if ac in existing_analysis else "✗ MISSING"
                print(f"  {status}  {ac}")
                
        else:
            print("✗ 'candidates' table NOT found!")
            print("\n📋 Available tables:")
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = %s
            """, (database,))
            tables = cursor.fetchall()
            for table in tables:
                print(f"  • {table[0]}")

finally:
    connection.close()
