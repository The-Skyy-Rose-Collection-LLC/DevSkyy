#!/usr/bin/env python3
"""
Script to fix register_model() calls in ML test files
Adds missing framework, parameters, and dataset_info parameters
"""

from pathlib import Path
import re


def fix_register_model_calls(filepath: Path) -> bool:
    """Fix register_model calls in a file"""
    with open(filepath, 'r') as f:
        content = f.read()

    original_content = content

    # Pattern to match register_model calls that don't have framework parameter
    # This regex finds register_model( calls and captures everything until the closing )
    pattern = r'(\.register_model\(\s*(?:[^)]*?))(metrics=\{[^}]+\},?)(\s*\))'

    def replacer(match):
        """Add framework, parameters, and dataset_info if not present"""
        prefix = match.group(1)
        metrics_part = match.group(2)
        suffix = match.group(3)

        # Check if framework is already present
        if 'framework=' in prefix:
            return match.group(0)  # Already fixed

        # Add framework parameter
        new_call = prefix
        if 'framework=' not in new_call:
            # Add framework before metrics
            new_call = new_call.rstrip().rstrip(',') + ',\n            framework="sklearn",'

        new_call += '\n            ' + metrics_part

        # Add parameters if not present
        if 'parameters=' not in new_call:
            new_call += ',\n            parameters={}'

        # Add dataset_info if not present
        if 'dataset_info=' not in new_call:
            new_call += ',\n            dataset_info={}'

        new_call += suffix

        return new_call

    # Apply the fix
    fixed_content = re.sub(pattern, replacer, content, flags=re.MULTILINE | re.DOTALL)

    # Write back if changed
    if fixed_content != original_content:
        with open(filepath, 'w') as f:
            f.write(fixed_content)
        return True

    return False


def main():
    """Fix all ML test files"""
    test_dir = Path("/home/user/DevSkyy/tests/ml")

    fixed_files = []
    for test_file in test_dir.glob("test_*.py"):
        print(f"Processing {test_file.name}...")
        if fix_register_model_calls(test_file):
            fixed_files.append(test_file.name)
            print(f"  ✅ Fixed {test_file.name}")
        else:
            print(f"  ⏭️  No changes needed for {test_file.name}")

    print(f"\n📊 Summary: Fixed {len(fixed_files)} files")
    for fname in fixed_files:
        print(f"  - {fname}")


if __name__ == "__main__":
    main()
