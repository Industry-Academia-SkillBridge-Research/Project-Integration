"""
Check if any candidate has analysis data
"""
import pymysql
import os
from dotenv import load_dotenv
import json

load_dotenv()

# Parse DATABASE_URL
db_url = os.getenv('DATABASE_URL', 'mysql+pymysql://root:tharusha2001@localhost:3306/oauth_users')
db_url = db_url.replace('mysql+pymysql://', '')
credentials, host_db = db_url.split('@')
username, password = credentials.split(':')
host_port, database = host_db.split('/')
host = host_port.split(':')[0]
port = int(host_port.split(':')[1])

connection = pymysql.connect(
    host=host,
    port=port,
    user=username,
    password=password,
    database=database,
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

try:
    with connection.cursor() as cursor:
        # Check all candidates and their analysis data
        cursor.execute("""
            SELECT 
                c.id,
                c.user_id,
                u.email,
                c.target_role,
                c.readiness_score,
                c.latest_analysis_date,
                c.matched_skills,
                c.missing_skills,
                c.analysis_summary
            FROM candidates c
            LEFT JOIN users u ON c.user_id = u.id
            ORDER BY c.id DESC
        """)
        
        candidates = cursor.fetchall()
        
        print(f"📊 Found {len(candidates)} candidate(s) in database:\n")
        
        has_analysis = False
        for cand in candidates:
            print(f"👤 Candidate ID: {cand['id']} | User: {cand['email'] or 'N/A'}")
            print(f"   Target Role: {cand['target_role'] or 'Not set'}")
            
            if cand['readiness_score'] is not None:
                has_analysis = True
                print(f"   ✅ HAS ANALYSIS DATA:")
                print(f"      • Readiness Score: {cand['readiness_score']}%")
                print(f"      • Analysis Date: {cand['latest_analysis_date']}")
                
                if cand['matched_skills']:
                    try:
                        matched = json.loads(cand['matched_skills'])
                        print(f"      • Matched Skills: {len(matched)} skills")
                    except:
                        print(f"      • Matched Skills: Present")
                
                if cand['missing_skills']:
                    try:
                        missing = json.loads(cand['missing_skills'])
                        print(f"      • Missing Skills: {len(missing)} skills")
                    except:
                        print(f"      • Missing Skills: Present")
                
                if cand['analysis_summary']:
                    summary = cand['analysis_summary'][:60] + "..." if len(cand['analysis_summary']) > 60 else cand['analysis_summary']
                    print(f"      • Summary: {summary}")
            else:
                print(f"   ❌ NO ANALYSIS DATA - Profile card won't show")
            
            print()
        
        if not has_analysis:
            print("⚠️  No candidates have run the CV analysis yet!")
            print("\n📋 To see the 'Latest Career Analysis' card:")
            print("   1. Login to the app")
            print("   2. Go to 'Personalized Learning Path'")
            print("   3. Upload your CV and select target role")
            print("   4. Wait for the 6-stage analysis to complete")
            print("   5. Go to Profile page - the card will appear!")

finally:
    connection.close()
