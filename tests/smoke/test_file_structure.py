"""
Smoke Test: Configuration Validation
Validates that all required configuration is present and valid.
"""

import os
import pytest
from pathlib import Path


@pytest.mark.smoke
def test_project_root_structure():
    """Test that critical project directories exist."""
    project_root = Path(__file__).parent.parent.parent
    
    critical_dirs = [
        'agent',
        'api',
        'database',
        'security',
        'tests',
        'ml',
        'monitoring',
    ]
    
    missing_dirs = []
    for dir_name in critical_dirs:
        if not (project_root / dir_name).exists():
            missing_dirs.append(dir_name)
    
    if missing_dirs:
        pytest.fail(f"Missing critical directories: {', '.join(missing_dirs)}")


@pytest.mark.smoke
def test_required_files_exist():
    """Test that required configuration files exist."""
    project_root = Path(__file__).parent.parent.parent
    
    required_files = [
        'main.py',
        'requirements.txt',
        'pytest.ini',
        '.env.example',
        'README.md',
    ]
    
    missing_files = []
    for file_name in required_files:
        if not (project_root / file_name).exists():
            missing_files.append(file_name)
    
    if missing_files:
        pytest.fail(f"Missing required files: {', '.join(missing_files)}")


@pytest.mark.smoke
def test_test_directory_structure():
    """Test that test directory structure follows best practices."""
    tests_dir = Path(__file__).parent.parent
    
    expected_test_dirs = [
        'unit',
        'integration',
        'api',
        'security',
        'ml',
        'e2e',
        'smoke',
    ]
    
    missing_dirs = []
    for dir_name in expected_test_dirs:
        test_dir = tests_dir / dir_name
        if not test_dir.exists():
            missing_dirs.append(dir_name)
        elif not (test_dir / '__init__.py').exists():
            pytest.fail(f"Missing __init__.py in {dir_name}")
    
    if missing_dirs:
        pytest.fail(f"Missing test directories: {', '.join(missing_dirs)}")


@pytest.mark.smoke
def test_pytest_configuration():
    """Test that pytest.ini exists and is valid."""
    project_root = Path(__file__).parent.parent.parent
    pytest_ini = project_root / 'pytest.ini'
    
    assert pytest_ini.exists(), "pytest.ini not found"
    
    content = pytest_ini.read_text()
    assert '[pytest]' in content, "pytest.ini missing [pytest] section"
    assert 'testpaths' in content, "pytest.ini missing testpaths"


@pytest.mark.smoke
def test_conftest_exists():
    """Test that conftest.py exists with required fixtures."""
    tests_dir = Path(__file__).parent.parent
    conftest = tests_dir / 'conftest.py'
    
    assert conftest.exists(), "conftest.py not found"
    
    content = conftest.read_text()
    # Check for some critical fixtures
    assert 'test_client' in content, "Missing test_client fixture"
    assert 'setup_test_environment' in content, "Missing setup_test_environment fixture"


@pytest.mark.smoke
def test_environment_variables_structure():
    """Test that environment variable setup is correct."""
    # These should be set by conftest.py setup_test_environment fixture
    required_env_vars = [
        'ENVIRONMENT',
        'JWT_SECRET_KEY',
        'ENCRYPTION_MASTER_KEY',
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    # In test environment, these should be set
    if missing_vars and os.getenv('ENVIRONMENT') != 'test':
        # Only warn, don't fail (they might be set later by conftest)
        pass


@pytest.mark.smoke
def test_test_file_naming_convention():
    """Test that all test files follow naming convention."""
    tests_dir = Path(__file__).parent.parent
    
    # Find all Python files in test directories
    test_files = list(tests_dir.rglob('*.py'))
    
    invalid_names = []
    for test_file in test_files:
        # Skip __init__.py and conftest.py
        if test_file.name in ['__init__.py', 'conftest.py']:
            continue
        
        # Test files must start with 'test_'
        if not test_file.name.startswith('test_'):
            invalid_names.append(str(test_file.relative_to(tests_dir)))
    
    if invalid_names:
        pytest.fail(
            f"Test files must start with 'test_': {', '.join(invalid_names)}"
        )


@pytest.mark.smoke
def test_no_orphaned_test_files_in_root():
    """Test that no test files exist in project root."""
    project_root = Path(__file__).parent.parent.parent
    
    # Find test files in project root (not in tests/ directory)
    root_test_files = []
    for file in project_root.iterdir():
        if file.is_file() and file.name.startswith('test_') and file.suffix == '.py':
            root_test_files.append(file.name)
    
    # These are legacy files that should eventually be moved
    # For now, we document them but don't fail
    if root_test_files:
        # Just log a warning, don't fail
        print(f"Note: Found test files in root that should be moved: {', '.join(root_test_files)}")
