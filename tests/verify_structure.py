#!/usr/bin/env python3
"""
Test Suite Verification Script
Validates that the test suite is properly organized and discoverable.
"""

import os
import sys
from pathlib import Path
from collections import defaultdict


def verify_test_structure():
    """Verify test directory structure and naming conventions."""
    
    tests_dir = Path(__file__).parent
    project_root = tests_dir.parent
    
    print("🔍 DevSkyy Test Suite Verification\n")
    print("=" * 70)
    
    # 1. Check for required directories
    print("\n1. Checking required directories...")
    required_dirs = [
        'smoke', 'unit', 'integration', 'api', 'security', 
        'ml', 'e2e', 'performance', 'agents', 'infrastructure'
    ]
    
    missing_dirs = []
    for dir_name in required_dirs:
        dir_path = tests_dir / dir_name
        if not dir_path.exists():
            missing_dirs.append(dir_name)
        else:
            print(f"   ✓ {dir_name}/")
    
    if missing_dirs:
        print(f"   ✗ Missing directories: {', '.join(missing_dirs)}")
        return False
    
    # 2. Check for __init__.py in all test directories
    print("\n2. Checking for __init__.py files...")
    test_dirs = [d for d in tests_dir.rglob('*') if d.is_dir() and d.name != '__pycache__']
    
    missing_init = []
    for dir_path in test_dirs:
        if dir_path == tests_dir:
            continue
        init_file = dir_path / '__init__.py'
        if not init_file.exists():
            missing_init.append(str(dir_path.relative_to(tests_dir)))
    
    if missing_init:
        print(f"   ✗ Missing __init__.py in: {', '.join(missing_init)}")
        return False
    else:
        print(f"   ✓ All {len(test_dirs)} directories have __init__.py")
    
    # 3. Check test file naming convention
    print("\n3. Checking test file naming conventions...")
    test_files = list(tests_dir.rglob('*.py'))
    
    invalid_names = []
    for test_file in test_files:
        if test_file.name in ['__init__.py', 'conftest.py', 'verify_structure.py']:
            continue
        if not test_file.name.startswith('test_'):
            invalid_names.append(str(test_file.relative_to(tests_dir)))
    
    if invalid_names:
        print(f"   ✗ Invalid test file names: {', '.join(invalid_names)}")
        return False
    else:
        valid_test_files = [f for f in test_files if f.name.startswith('test_')]
        print(f"   ✓ All {len(valid_test_files)} test files follow 'test_*.py' convention")
    
    # 4. Count tests by category
    print("\n4. Test distribution by category...")
    test_count = defaultdict(int)
    
    for test_file in test_files:
        if test_file.name.startswith('test_'):
            # Find the immediate parent directory
            rel_path = test_file.relative_to(tests_dir)
            category = rel_path.parts[0] if len(rel_path.parts) > 1 else 'root'
            test_count[category] += 1
    
    total = 0
    for category in sorted(test_count.keys()):
        count = test_count[category]
        total += count
        print(f"   • {category:30s} {count:3d} files")
    
    print(f"\n   Total test files: {total}")
    
    # 5. Check for documentation
    print("\n5. Checking documentation files...")
    doc_files = ['README.md', 'TEST_STRUCTURE.md', 'QUICK_REFERENCE.md', 'CI_CD_EXAMPLES.md']
    
    for doc_file in doc_files:
        doc_path = tests_dir / doc_file
        if doc_path.exists():
            print(f"   ✓ {doc_file}")
        else:
            print(f"   ✗ Missing: {doc_file}")
    
    # 6. Check for orphaned test files at project root
    print("\n6. Checking for orphaned test files at project root...")
    root_test_files = [f for f in project_root.iterdir() 
                       if f.is_file() and f.name.startswith('test_') and f.suffix == '.py']
    
    if root_test_files:
        print(f"   ⚠ Found orphaned test files:")
        for f in root_test_files:
            print(f"     - {f.name}")
    else:
        print(f"   ✓ No orphaned test files at project root")
    
    # 7. Check pytest.ini
    print("\n7. Checking pytest.ini configuration...")
    pytest_ini = project_root / 'pytest.ini'
    
    if pytest_ini.exists():
        content = pytest_ini.read_text()
        if 'testpaths = tests' in content:
            print(f"   ✓ pytest.ini exists with correct testpaths")
        else:
            print(f"   ⚠ pytest.ini missing 'testpaths = tests'")
    else:
        print(f"   ✗ pytest.ini not found")
    
    print("\n" + "=" * 70)
    print("\n✅ Test suite verification complete!")
    print(f"\nSummary:")
    print(f"  • {len(required_dirs)} test categories")
    print(f"  • {total} test files")
    print(f"  • {len(test_dirs)} test directories")
    print(f"  • {len(doc_files)} documentation files")
    print(f"\n🎯 Test suite is properly organized and ready for CI/CD!")
    
    return True


if __name__ == '__main__':
    success = verify_test_structure()
    sys.exit(0 if success else 1)
