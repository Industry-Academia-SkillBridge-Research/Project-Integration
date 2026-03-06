import pymysql

conn = pymysql.connect(
    host='localhost',
    user='root',
    password='tharusha2001',
    database='oauth_users'
)

cursor = conn.cursor()

# Check recent candidates with analysis data
cursor.execute("""
    SELECT 
        id, 
        user_id, 
        readiness_score, 
        LENGTH(ai_explanation) as ai_len,
        LENGTH(matched_skills) as matched_len,
        LENGTH(missing_skills) as missing_len,
        latest_analysis_date
    FROM candidates 
    ORDER BY id DESC 
    LIMIT 5
""")

rows = cursor.fetchall()

print("\n" + "="*90)
print("CANDIDATES TABLE - Analysis Data Summary")
print("="*90)
print(f"{'ID':<5} {'User':<6} {'Readiness':<10} {'AI Len':<10} {'Matched':<10} {'Missing':<10} {'Date':<20}")
print("-"*90)

for row in rows:
    cid, uid, readiness, ai_len, matched_len, missing_len, date = row
    print(f"{cid:<5} {uid:<6} {readiness or 'NULL':<10} {ai_len or 0:<10} {matched_len or 0:<10} {missing_len or 0:<10} {str(date) if date else 'No analysis':<20}")

print("="*90)

# Check specific user's AI explanation
print("\n\nChecking AI Explanation for User ID 3:")
print("-"*90)
cursor.execute("""
    SELECT ai_explanation
    FROM candidates 
    WHERE user_id = 3
""")
result = cursor.fetchone()
if result and result[0]:
    print(f"AI Explanation (first 500 chars):\n{result[0][:500]}")
else:
    print("❌ NO AI EXPLANATION SAVED!")

conn.close()
