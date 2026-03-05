#!/usr/bin/env python3
"""
Test the integrated backend endpoints
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8010"

def test_roles_endpoint():
    """Test /roles endpoint"""
    print("\n" + "="*70)
    print("TEST 1: /roles endpoint")
    print("="*70)
    try:
        r = requests.get(f"{BASE_URL}/roles", timeout=10)
        print(f"✓ Status: {r.status_code}")
        data = r.json()
        print(f"✓ Got {data.get('count', 0)} roles:")
        for role in data.get('roles', [])[:3]:
            print(f"  - {role}")
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False

def test_generate_project():
    """Test /generate-project endpoint"""
    print("\n" + "="*70)
    print("TEST 2: /generate-project endpoint")
    print("="*70)
    
    payload = {
        "student_data": {
            "name": "Alice Chen",
            "current_role": "Junior Developer",
            "skills": ["Python", "JavaScript", "React", "SQL"],
            "major": "Computer Science",
            "interests": ["Backend", "DevOps"]
        },
        "job_data": {
            "role": "Senior Backend Engineer",
            "required_skills": ["Python", "Java", "Kubernetes", "AWS", "Docker", "PostgreSQL"],
            "description_summary": "Senior backend position requiring cloud infrastructure"
        },
        "target_role": "Senior Backend Engineer"
    }
    
    try:
        r = requests.post(f"{BASE_URL}/generate-project", json=payload, timeout=15)
        print(f"✓ Status: {r.status_code}")
        data = r.json()
        
        print(f"✓ Candidate ID: {data.get('candidate_id')}")
        print(f"✓ Target Role: {data.get('target_role')}")
        
        analysis = data.get('analysis', {})
        print(f"✓ Analysis:")
        print(f"  - Current skills: {analysis.get('covered_skills', [])}")
        print(f"  - Missing skills: {analysis.get('missing_skills', [])}")
        print(f"  - Match %: {analysis.get('match_percentage', 0):.1f}%")
        
        rec = data.get('recommendation', {})
        print(f"✓ Recommendation: {rec.get('summary', '')[:100]}...")
        
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_health():
    """Test basic health check"""
    print("\n" + "="*70)
    print("TEST 0: Server health check")
    print("="*70)
    try:
        r = requests.get(f"{BASE_URL}/docs", timeout=5)
        print(f"✓ Server responding (status {r.status_code})")
        return True
    except Exception as e:
        print(f"✗ Server not responding: {e}")
        return False

if __name__ == "__main__":
    print("\n🧪 Testing Thisaravi-Backend Integration")
    print("="*70)
    
    tests = [
        ("Server Health", test_health),
        ("Roles Endpoint", test_roles_endpoint),
        ("Generate Project Endpoint", test_generate_project),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            results.append((name, test_func()))
        except Exception as e:
            print(f"\n✗ {name} crashed: {e}")
            results.append((name, False))
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(p for _, p in results)
    sys.exit(0 if all_passed else 1)
