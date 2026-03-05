import sys
try:
    import main
    print("✓ main.py imports OK")
except Exception as e:
    print(f"✗ Import error: {e}")
    import traceback
    traceback.print_exc()
