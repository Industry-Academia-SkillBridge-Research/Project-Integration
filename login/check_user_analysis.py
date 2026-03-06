import pymysql

conn = pymysql.connect(
    host='localhost',
    user='root',
    password='tharusha2001',
    database='oauth_users'
)

cursor = conn.cursor()

# Check user 3's candidate data
cursor.execute('''
    SELECT id, user_id, target_role, latest_analysis_date, readiness_score, 
           matched_skills, missing_skills, ai_explanation 
    FROM candidates WHERE user_id=3
''')

row = cursor.fetchone()

print('=== User 3 (tharushabandara423@gmail.com) ===')
if row:
    print(f'Candidate ID: {row[0]}')
    print(f'Target Role: {row[2]}')
    print(f'Analysis Date: {row[3]}')
    print(f'Readiness Score: {row[4]}')
    print(f'Matched Skills: {"YES ({} chars)".format(len(row[5])) if row[5] else "NO"}')
    print(f'Missing Skills: {"YES ({} chars)".format(len(row[6])) if row[6] else "NO"}')
    print(f'AI Explanation: {"YES ({} chars)".format(len(row[7])) if row[7] else "NO"}')
else:
    print('NO CANDIDATE RECORD FOUND')

conn.close()
