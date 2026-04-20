#!/usr/bin/env python3
"""
Fix remaining import depth issues in services directory.
Services are at src/app/services/, so imports should use .. not ...
"""
import re
from pathlib import Path

def fix_imports_in_file(filepath):
    """Fix import paths in a single file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        
        # Fix imports: from ...X to from ..X (3 dots to 2 dots)
        content = re.sub(r'from \.\.\..* import', lambda m: m.group(0).replace('...', '..'), content)
        
        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def main():
    services_dir = Path("Nipuni_backend/src/app/services")
    models_dir = Path("Nipuni_backend/src/app/models")
    schemas_dir = Path("Nipuni_backend/src/app/schemas")
    
    fixed_count = 0
    
    # Fix services
    for py_file in services_dir.glob("*.py"):
        if fix_imports_in_file(py_file):
            print(f"✓ Fixed: {py_file.name}")
            fixed_count += 1
    
    # Fix models (if needed)
    if models_dir.exists():
        for py_file in models_dir.glob("*.py"):
            if fix_imports_in_file(py_file):
                print(f"✓ Fixed: {py_file.name}")
                fixed_count += 1
    
    # Fix schemas (if needed)
    if schemas_dir.exists():
        for py_file in schemas_dir.glob("*.py"):
            if fix_imports_in_file(py_file):
                print(f"✓ Fixed: {py_file.name}")
                fixed_count += 1
    
    print(f"\nTotal files fixed: {fixed_count}")

if __name__ == "__main__":
    main()
