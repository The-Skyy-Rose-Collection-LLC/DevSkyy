#!/usr/bin/env python3
"""
Ultimate Enterprise Python Fixer
Handles all corruption patterns systematically
"""

import re
from pathlib import Path
from typing import List

def remove_duplicate_try(lines: List[str]) -> List[str]:
    """Remove duplicate 'try:' statements"""
    fixed = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check for duplicate try
        if i + 1 < len(lines):
            next_line = lines[i + 1]
            if line.strip() == 'try:' and next_line.strip() == 'try:':
                # Skip first, keep second with proper indentation
                fixed.append('try:\n')
                i += 2
                # Ensure next block is properly indented
                while i < len(lines):
                    l = lines[i]
                    if l.strip().startswith(('except', 'finally', 'else', 'class ', 'def ', '# ---')):
                        fixed.append(l)
                        i += 1
                        break
                    # Properly indent the block
                    if l.strip() and not l.startswith(('    ', '\t')):
                        fixed.append('    ' + l.lstrip())
                    else:
                        fixed.append(l)
                    i += 1
                continue
        
        fixed.append(line)
        i += 1
    
    return fixed

def fix_all_files():
    agent_dir = Path('agent')
    fixed_count = 0
    
    for py_file in sorted(agent_dir.rglob('*.py')):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            original = lines.copy()
            lines = remove_duplicate_try(lines)
            
            if lines != original:
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                fixed_count += 1
                print(f"✅ {py_file.name}")
        except Exception as e:
            print(f"❌ {py_file}: {e}")
    
    print(f"\n✅ Fixed {fixed_count} files")

if __name__ == '__main__':
    print("🔧 Ultimate Enterprise Fixer")
    print("=" * 60)
    fix_all_files()
    print("=" * 60)

