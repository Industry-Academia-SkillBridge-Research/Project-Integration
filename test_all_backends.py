#!/usr/bin/env python3
"""Test all 5 unified backends are responding"""
import requests
import sys

backends = {
    "Login Backend": ("http://localhost:8182/auth/health", "8182"),
    "Agent Runtime": ("http://localhost:8003/health", "8003"),
    "Skill Backend": ("http://localhost:8000/health", "8000"),
    "Interview Backend": ("http://localhost:8188/health", "8188"),
    "Recommendation Engine": ("http://localhost:8001/health", "8001"),
}

print("\n" + "="*80)
print("UNIFIED BACKEND LAUNCHER - HEALTH CHECK")
print("="*80 + "\n")

all_ok = True
for name, (url, port) in backends.items():
    try:
        response = requests.get(url, timeout=5)
        status = "OK" if response.status_code == 200 else f"FAILED ({response.status_code})"
        symbol = "[OK]" if response.status_code == 200 else "[FAIL]"
        print(f"{symbol} {name:25} (port {port}): {status}")
        if response.status_code != 200:
            all_ok = False
    except requests.exceptions.ConnectionError:
        print(f"[FAIL] {name:25} (port {port}): CONNECTION FAILED")
        all_ok = False
    except Exception as e:
        print(f"[FAIL] {name:25} (port {port}): ERROR - {str(e)}")
        all_ok = False

print("\n" + "="*80)
if all_ok:
    print("SUCCESS! All 5 backends are running and responding!")
    print("="*80)
    print("\nAccess services at:")
    print("  Login:          http://localhost:8182/docs")
    print("  Agent:          http://localhost:8003/docs")
    print("  Skill:          http://localhost:8000/docs")
    print("  Interview:      http://localhost:8188/docs")
    print("  Recommendation: http://localhost:8001/docs")
    print("="*80 + "\n")
    sys.exit(0)
else:
    print("FAILURE! Some backends are not responding")
    print("="*80 + "\n")
    sys.exit(1)
