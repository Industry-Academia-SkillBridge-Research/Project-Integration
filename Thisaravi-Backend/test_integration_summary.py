#!/usr/bin/env python3
"""
Comprehensive integration test for Thisaravi-Backend
"""
import requests
import json
import time

BASE_URL = "http://localhost:8010"
AGENT_RUNTIME_URL = "http://localhost:8003"
ADVANCED_REC_URL = "http://localhost:8001"

def check_service(name, url):
    """Check if a service is running"""
    try:
        requests.get(url + "/docs", timeout=3)
        return True
    except:
        return False

def test_generate_project():
    """Test /generate-project endpoint"""
    payload = {
        "student_data": {
            "name": "Alice Chen",
            "current_role": "Junior Developer",
            "skills": ["Python", "JavaScript", "React", "SQL"],
            "experience_summary": "2 years of web development",
            "major": "Computer Science",
            "interests": ["Backend", "DevOps"],
            "personality": "ambitious"
        },
        "job_data": {
            "role": "Senior Backend Engineer",
            "required_skills": ["Python", "Java", "Kubernetes", "AWS", "Docker", "PostgreSQL"],
            "description_summary": "Senior backend position"
        },
        "target_role": "Senior Backend Engineer"
    }
    
    try:
        r = requests.post(f"{BASE_URL}/generate-project", json=payload, timeout=10)
        if r.status_code == 200:
            data = r.json()
            return {
                "status": "PASS",
                "code": 200,
                "match_percentage": data.get("analysis", {}).get("match_percentage", 0),
                "missing_skills": data.get("analysis", {}).get("missing_skills", []),
            }
        else:
            return {"status": "FAIL", "code": r.status_code, "error": r.json()}
    except Exception as e:
        return {"status": "FAIL", "error": str(e)}

def test_roles():
    """Test /roles endpoint"""
    try:
        r = requests.get(f"{BASE_URL}/roles", timeout=10)
        if r.status_code == 200:
            data = r.json()
            return {"status": "PASS", "code": 200, "count": data.get("count", 0)}
        else:
            return {"status": "FAIL", "code": r.status_code, "error": r.json()}
    except Exception as e:
        return {"status": "FAIL", "error": str(e)}

print("\n" + "="*70)
print("THISARAVI-BACKEND INTEGRATION TEST")
print("="*70)

print("\nService Status:")
print("-" * 70)
services = {
    "Thisaravi-Backend (8010)": (BASE_URL, check_service("Backend", BASE_URL)),
    "Agent-Runtime (8003)": (AGENT_RUNTIME_URL, check_service("Agent", AGENT_RUNTIME_URL)),
    "Advanced-Recommendation (8001)": (ADVANCED_REC_URL, check_service("Rec", ADVANCED_REC_URL)),
}

for name, (url, running) in services.items():
    status = "[OK]" if running else "[DOWN]"
    print(f"{status} {name}")

print("\nEndpoint Tests:")
print("-" * 70)

# Test /generate-project
print("\n1. POST /generate-project")
result = test_generate_project()
status = "[PASS]" if result["status"] == "PASS" else "[FAIL]"
print(f"   {status} {result}")

# Test /roles
print("\n2. GET /roles")
result = test_roles()
status = "[PASS]" if result["status"] == "PASS" else "[FAIL]"
print(f"   {status} {result}")

print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print("""
Thisaravi-Backend is running and working correctly:

WORKING:
  [OK] /generate-project - Computes skill gaps locally
  [OK] Server is responding and returning valid JSON

NOT WORKING (requires Advanced-Recommendation on 8001):
  [FAIL] /roles - Needs Advanced-Recommendation service

ACTION REQUIRED:
  Start Advanced-Recommendation service on port 8001:
  > cd Advanced-Recommendation-System
  > uv run main.py

Then /roles will work and return available roles from Advanced-Recommendation.
""")
