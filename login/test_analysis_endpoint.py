"""
Test the /candidate/me/analysis endpoint manually
"""
import requests
import json

# This should be the actual token from your localStorage
# You can get it from browser console: localStorage.getItem('access_token')
TOKEN = "PASTE_YOUR_TOKEN_HERE"

# Test data
test_data = {
    "readiness_score": 75,
    "skill_gap_index": {"python": 0.8, "sql": 0.6},
    "ai_explanation": "Test explanation from manual script",
    "matched_skills": [
        {"skill": "Python", "confidence": 0.9},
        {"skill": "Data Analysis", "confidence": 0.85}
    ],
    "missing_skills": [
        {"skill": "Machine Learning", "deficit": 0.7},
        {"skill": "Deep Learning", "deficit": 0.8}
    ],
    "analysis_summary": "Test analysis summary - 75% readiness",
    "target_role": "DATA_ANALYST"
}

print("🧪 Testing PUT /candidate/me/analysis endpoint...\n")

# Try without token first
print("1️⃣ Testing WITHOUT token (should fail with 401):")
response = requests.put(
    'http://localhost:8182/candidate/me/analysis',
    json=test_data,
    headers={'Content-Type': 'application/json'}
)
print(f"   Status: {response.status_code}")
print(f"   Response: {response.text[:200]}\n")

# Now test with token (you need to paste your actual token)
if TOKEN != "PASTE_YOUR_TOKEN_HERE":
    print("2️⃣ Testing WITH token:")
    response = requests.put(
        'http://localhost:8182/candidate/me/analysis',
        json=test_data,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {TOKEN}'
        }
    )
    print(f"   Status: {response.status_code}")
    if response.ok:
        print(f"   ✅ Success! Response: {response.json()}")
    else:
        print(f"   ❌ Failed! Response: {response.text}")
else:
    print("2️⃣ SKIPPED - No token provided")
    print("\n📝 To get your token:")
    print("   1. Open browser dev tools (F12)")
    print("   2. Go to Console tab")
    print("   3. Type: localStorage.getItem('access_token')")
    print("   4. Copy the token and paste it in this script")
    print("   5. Run the script again")
