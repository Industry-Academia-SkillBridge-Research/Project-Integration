#!/usr/bin/env python
import requests
import json

req = {
    'student_data': {
        'name': 'Test User',
        'current_role': 'Engineer',
        'skills': ['Python', 'JavaScript'],
        'experience_summary': '3 years',
    },
    'job_data': {
        'role': 'Senior Engineer',
        'required_skills': ['Python', 'React', 'Node.js'],
        'description_summary': 'Senior role',
    },
    'target_role': 'Senior Engineer',
    'model_provider': 'gemini',
}

try:
    r = requests.post('http://localhost:8010/generate-project', json=req, timeout=10)
    print(f'Status: {r.status_code}')
    print(f'Content-Type: {r.headers.get("content-type")}')
    print(f'Response Body:')
    try:
        data = r.json()
        print(json.dumps(data, indent=2))
    except:
        print(r.text)
except Exception as e:
    import traceback
    print(f'Error: {e}')
    traceback.print_exc()
