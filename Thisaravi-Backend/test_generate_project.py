#!/usr/bin/env python3
"""
Test /generate-project endpoint with correct schema
"""
import requests
import json
import time

payload = {
    "student_data": {
        "name": "Alice Chen",
        "current_role": "Junior Developer",
        "skills": ["Python", "JavaScript", "React", "SQL"],
        "experience_summary": "2 years of web development experience, specializing in frontend",
        "major": "Computer Science",
        "interests": ["Backend", "DevOps"],
        "personality": "ambitious, quick learner"
    },
    "job_data": {
        "role": "Senior Backend Engineer",
        "required_skills": ["Python", "Java", "Kubernetes", "AWS", "Docker", "PostgreSQL"],
        "description_summary": "Senior backend position requiring cloud infrastructure and leadership"
    },
    "target_role": "Senior Backend Engineer"
}

print("Testing /generate-project endpoint...")
start = time.time()
try:
    r = requests.post('http://localhost:8010/generate-project', json=payload, timeout=15)
    elapsed = time.time() - start
    print(f"[OK] Status: {r.status_code} (took {elapsed:.2f}s)")
    
    if r.status_code == 200:
        data = r.json()
        print(f"\n[OK] Response structure:")
        print(f"  - candidate_id: {data.get('candidate_id')}")
        print(f"  - target_role: {data.get('target_role')}")
        
        analysis = data.get('analysis', {})
        print(f"\n[OK] Analysis results:")
        print(f"  - Match percentage: {analysis.get('match_percentage', 0):.1f}%")
        print(f"  - Current skills: {analysis.get('covered_skills', [])}")
        print(f"  - Missing skills: {analysis.get('missing_skills', [])}")
        
        rec = data.get('recommendation', {})
        print(f"\n[OK] Recommendation:")
        print(f"  {rec.get('summary', 'N/A')}")
        
        # Print full response
        print(f"\n[FULL] Response:\n{json.dumps(data, indent=2)}")
    else:
        print(f"[FAIL] Error response: {json.dumps(r.json(), indent=2)}")
        
except requests.Timeout:
    elapsed = time.time() - start
    print(f"[FAIL] Timeout after {elapsed:.2f}s")
except Exception as e:
    elapsed = time.time() - start
    print(f"[FAIL] Error after {elapsed:.2f}s: {e}")
