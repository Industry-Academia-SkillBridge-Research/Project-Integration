#!/usr/bin/env python
"""
Automated Import Fixer
Converts absolute imports (from app.X) to relative imports (from ..X)
"""

import os
import re
import sys
from pathlib import Path


class ImportFixer:
    """Fix absolute imports in Python files"""
    
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.fixed_count = 0
        self.failed_count = 0
        self.skipped_count = 0
    
    def convert_absolute_to_relative(self, file_path: Path) -> bool:
        """Convert absolute imports to relative imports in a single file"""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Get the relative path from the file to the src/app directory
            # This determines how many levels up we need to go
            src_app_path = self.base_path / 'src' / 'app'
            
            # Calculate relative path from current file to src/app
            try:
                rel_path = file_path.relative_to(src_app_path)
                levels = len(rel_path.parts) - 1  # Exclude the filename
                
                # Create the relative import prefix (../ for each level)
                prefix = '.' * (levels + 2)  # +2 for going to parent then to other module
                
                # Replace patterns
                # Pattern 1: from app.db import X -> from ..db import X
                content = re.sub(
                    r'from\s+app\.db\s+import\s+',
                    f'from {prefix}db import ',
                    content
                )
                
                # Pattern 2: from app.services.X import Y -> from ...services.X import Y
                content = re.sub(
                    r'from\s+app\.services\.',
                    f'from {prefix}services.',
                    content
                )
                
                # Pattern 3: from app.models.X import Y -> from ...models.X import Y
                content = re.sub(
                    r'from\s+app\.models\.',
                    f'from {prefix}models.',
                    content
                )
                
                # Pattern 4: from app.schemas.X import Y -> from ...schemas.X import Y
                content = re.sub(
                    r'from\s+app\.schemas\.',
                    f'from {prefix}schemas.',
                    content
                )
                
                # Pattern 5: from app.routes.X import Y -> handled by ..routes
                content = re.sub(
                    r'from\s+app\.routes\.',
                    f'from {prefix}routes.',
                    content
                )
                
                # Pattern 6: Generic - from app.X import Y
                content = re.sub(
                    r'from\s+app\.(\w+)',
                    lambda m: f'from {prefix}{m.group(1)}',
                    content
                )
                
                if content != original_content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    return True
                else:
                    return False
                    
            except ValueError:
                # File is not under src/app, use a generic approach
                content = re.sub(r'from\s+app\.', 'from ..', content)
                
                if content != original_content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    return True
                else:
                    return False
        
        except Exception as e:
            print(f"  Error: {e}")
            return False
    
    def fix_directory(self, directory: Path, pattern: str = '**/*.py'):
        """Fix all Python files in a directory"""
        
        py_files = list(directory.glob(pattern))
        
        print(f"\nFound {len(py_files)} Python files")
        print("-" * 80)
        
        for file_path in py_files:
            # Skip __pycache__ and venv
            if '__pycache__' in str(file_path) or '.venv' in str(file_path):
                continue
            
            # Check if file has absolute imports
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if 'from app.' in content:
                    rel_path = str(file_path.relative_to(self.base_path))
                    print(f"Fixing: {rel_path}")
                    
                    if self.convert_absolute_to_relative(file_path):
                        print(f"  ✓ Fixed")
                        self.fixed_count += 1
                    else:
                        print(f"  - No changes needed")
                        self.skipped_count += 1
                
            except Exception as e:
                rel_path = str(file_path.relative_to(self.base_path))
                print(f"  ✗ Error: {rel_path}")
                print(f"     {e}")
                self.failed_count += 1
    
    def print_summary(self):
        """Print summary of fixes"""
        print("\n" + "=" * 80)
        print("IMPORT FIX SUMMARY")
        print("=" * 80)
        print(f"✓ Fixed: {self.fixed_count} files")
        print(f"- Skipped: {self.skipped_count} files")
        print(f"✗ Failed: {self.failed_count} files")
        print("=" * 80)


def main():
    """Main entry point"""
    
    # Base path
    base_path = r'f:\ResearchProjrctafterPP2\Project-Integration\Nipuni_backend'
    
    print("\n" + "=" * 80)
    print("AUTOMATED IMPORT FIXER")
    print("Converting 'from app.X import' to relative imports")
    print("=" * 80)
    
    fixer = ImportFixer(base_path)
    
    # Fix routes
    print("\n[1/3] Fixing routes...")
    routes_dir = Path(base_path) / 'src' / 'app' / 'routes'
    if routes_dir.exists():
        fixer.fix_directory(routes_dir)
    
    # Fix services
    print("\n[2/3] Fixing services...")
    services_dir = Path(base_path) / 'src' / 'app' / 'services'
    if services_dir.exists():
        fixer.fix_directory(services_dir)
    
    # Fix schemas
    print("\n[3/3] Fixing schemas...")
    schemas_dir = Path(base_path) / 'src' / 'app' / 'schemas'
    if schemas_dir.exists():
        fixer.fix_directory(schemas_dir)
    
    fixer.print_summary()
    
    if fixer.failed_count == 0 and fixer.fixed_count > 0:
        print("\n✓ Import fixes complete! Try running the API again:")
        print("  python run_api.py")
    elif fixer.fixed_count == 0 and fixer.skipped_count > 0:
        print("\n✓ No absolute imports found. API should start successfully.")
    else:
        print(f"\n⚠ Warning: {fixer.failed_count} files had errors. Check the output above.")


if __name__ == '__main__':
    main()
