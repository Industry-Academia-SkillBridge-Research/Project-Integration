#!/usr/bin/env python3
"""
Test RecommendationClient directly
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'clients'))

import time
from clients import RecommendationClient

print("Creating RecommendationClient...")
start = time.time()
client = RecommendationClient()
elapsed = time.time() - start
print(f"✓ Client created in {elapsed:.2f}s")

print("\nCalling list_roles()...")
start = time.time()
try:
    roles = client.list_roles()
    elapsed = time.time() - start
    print(f"✓ Got {len(roles)} roles in {elapsed:.2f}s")
    for role in roles[:3]:
        print(f"  - {role.get('name')}")
except Exception as e:
    elapsed = time.time() - start
    print(f"✗ Failed after {elapsed:.2f}s: {e}")
