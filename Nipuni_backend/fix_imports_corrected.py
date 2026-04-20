#!/usr/bin/env python
"""
Corrected Import Fixer
Properly converts imports based on file location
"""

import os
import re
from pathlib import Path


def fix_file(file_path: Path):
    """Fix imports in a single file based on its location"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Determine file depth relative to src/app
    try:
        rel_to_app = file_path.relative_to(file_path.parents[0] / 'src' / 'app')
        depth = len(rel_to_app.parents) - 1  # -1 because we don't count the filename as a dir
    except:
        depth = 0
    
    # For files in routes, services, schemas: they are 1 level deep
    # from app, so they need .. to go up to app, then .module to access
    # Example: routes/admin.py needs ..db to access app/db.py
    
    # Replace ..X with correct depth
    # Routes/Services/Schemas files (1 level deep) need: from ..db, from ..services, etc
    # But currently they might have from ...db (3 dots = too many)
    
    # Simple approach: Replace all from app. with from ..
    content = re.sub(r'from\s+app\.', 'from ..', content)
    content = re.sub(r'import\s+app\.', 'import ..', content)
    
    # Fix any triple dots back to double dots (for routes, services, schemas)
    content = re.sub(r'from\s+\.\.\..', 'from ..', content)
    
    if content != original:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False


def main():
    base_path = Path(r'f:\ResearchProjrctafterPP2\Project-Integration\Nipuni_backend')
    
    print("\n" + "=" * 80)
    print("CORRECTED IMPORT FIXER - FIX TRIPLE DOTS")
    print("=" * 80)
    
    fixed = 0
    
    # Fix all Python files in src/app
    for py_file in (base_path / 'src' / 'app').rglob('*.py'):
        if '__pycache__' in str(py_file):
            continue
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'from ...' in content or 'import ...' in content:
                rel_path = py_file.relative_to(base_path)
                print(f"Fixing: {rel_path}")
                
                if fix_file(py_file):
                    print(f"  ✓ Fixed triple dots to double dots")
                    fixed += 1
        except Exception as e:
            print(f"  Error: {e}")
    
    print("\n" + "=" * 80)
    print(f"✓ Fixed {fixed} files")
    print("=" * 80)


if __name__ == '__main__':
    main()
