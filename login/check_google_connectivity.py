#!/usr/bin/env python3
"""
Diagnostic script to check connectivity to Google OAuth servers
Use this to troubleshoot OAuth timeout issues
"""

import asyncio
import httpx
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

async def check_connectivity():
    """Check if we can reach Google's OAuth servers"""
    print("=" * 70)
    print("GOOGLE OAUTH CONNECTIVITY CHECK")
    print("=" * 70)
    
    urls_to_check = [
        ("Google Search", "https://www.google.com"),
        ("Google Accounts", "https://accounts.google.com"),
        ("Google OAuth Config", "https://accounts.google.com/.well-known/openid-configuration"),
        ("Google OAuth Token", "https://oauth2.googleapis.com/token"),
    ]
    
    timeout_configs = [
        ("Default (5s)", 5.0),
        ("Extended (30s)", 30.0),
        ("Very Long (60s)", 60.0),
    ]
    
    for timeout_name, timeout_value in timeout_configs:
        print(f"\n[TIMEOUT: {timeout_name}]")
        print("-" * 70)
        
        async with httpx.AsyncClient(timeout=timeout_value, follow_redirects=True) as client:
            for url_name, url in urls_to_check:
                try:
                    response = await client.head(url)
                    print(f"  ✓ {url_name:30} ({response.status_code})")
                except httpx.TimeoutException:
                    print(f"  ✗ {url_name:30} (TIMEOUT after {timeout_value}s)")
                except httpx.ConnectError as e:
                    print(f"  ✗ {url_name:30} (CONNECT ERROR: {str(e)[:40]})")
                except Exception as e:
                    print(f"  ✗ {url_name:30} ({type(e).__name__}: {str(e)[:30]})")
    
    print("\n" + "=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                "https://accounts.google.com/.well-known/openid-configuration"
            )
            print("✓ Google OAuth servers are REACHABLE")
            print(f"  Response status: {response.status_code}")
            if response.status_code == 200:
                print("✓ Configuration endpoint is working")
                config = response.json()
                print(f"  - Token endpoint: {config.get('token_endpoint', 'N/A')}")
                print(f"  - Authorization endpoint: {config.get('authorization_endpoint', 'N/A')}")
            else:
                print("✗ Configuration endpoint returned unexpected status")
        except Exception as e:
            print(f"✗ Cannot reach Google OAuth servers: {type(e).__name__}")
            print(f"  Error: {str(e)}")
            print("\nPOSSIBLE SOLUTIONS:")
            print("  1. Check your internet connection")
            print("  2. Check if Google is accessible in your network")
            print("  3. Check for firewall/proxy blocking HTTPS connections")
            print("  4. Try using a VPN if in a restricted network")
            print("  5. Check if your DNS is working correctly")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    asyncio.run(check_connectivity())
