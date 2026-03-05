#!/usr/bin/env python3
"""
Test /roles endpoint with direct request
"""
import requests
import json
import time

print("Testing /roles endpoint with timeout...")

start = time.time()
try:
    # Use shorter timeout to fail faster
    r = requests.get('http://localhost:8010/roles', timeout=5)
    elapsed = time.time() - start
    print(f"✓ Status: {r.status_code} (took {elapsed:.2f}s)")
    print(f"✓ Response: {json.dumps(r.json(), indent=2)[:500]}")
except requests.Timeout:
    elapsed = time.time() - start
    print(f"✗ Timeout after {elapsed:.2f}s")
except Exception as e:
    elapsed = time.time() - start
    print(f"✗ Error after {elapsed:.2f}s: {e}")
