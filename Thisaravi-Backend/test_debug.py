#!/usr/bin/env python3
"""
Debug endpoint issues
"""
import requests
import json

BASE_URL = "http://localhost:8010"

print("Testing /generate-project with detailed error info...")
payload = {
    "student_data": {
        "name": "Alice Chen",
        "current_role": "Junior Developer",
        "skills": ["Python", "JavaScript"],
        "major": "Computer Science",
        "interests": ["Backend"]
    },
    "job_data": {
        "role": "Senior Backend Engineer",
        "required_skills": ["Python", "Java", "Kubernetes"],
        "description_summary": "Senior backend"
    },
    "target_role": "Senior Backend Engineer"
}

r = requests.post(f"{BASE_URL}/generate-project", json=payload, timeout=5)
print(f"Status: {r.status_code}")
print(f"Response: {json.dumps(r.json(), indent=2)}")
