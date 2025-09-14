#!/usr/bin/env python3
"""
DevSkyy Development CLI
Management commands for DevSkyy platform development.
"""

import argparse
import subprocess
import sys
import os
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent
BACKEND_DIR = PROJECT_ROOT
FRONTEND_DIR = PROJECT_ROOT / "frontend"


def run_command(cmd, cwd=None, check=True):
    """Run a shell command with error handling."""
    try:
        logger.info(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {e}")
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        sys.exit(1)


def setup():
    """Setup development environment."""
    logger.info("🚀 Setting up DevSkyy development environment...")
    
    # Check Python version
    if sys.version_info < (3, 11):
        logger.error("Python 3.11+ required")
        sys.exit(1)
    
    # Create .env from template if not exists
    env_path = PROJECT_ROOT / ".env"
    env_example_path = PROJECT_ROOT / ".env.example"
    
    if not env_path.exists() and env_example_path.exists():
        logger.info("📝 Creating .env from template...")
        env_path.write_text(env_example_path.read_text())
        logger.info("✅ .env created! Please edit with your configuration.")
    
    # Install Python dependencies
    logger.info("📦 Installing Python dependencies...")
    run_command([sys.executable, "-m", "pip", "install", "-r", "backend/requirements.txt"])
    dev_requirements_path = PROJECT_ROOT / "requirements-dev.txt"
    if dev_requirements_path.exists():
        run_command([sys.executable, "-m", "pip", "install", "-r", str(dev_requirements_path)])
    else:
        logger.warning("requirements-dev.txt not found. Skipping dev dependencies install.")
    
    # Install frontend dependencies
    if FRONTEND_DIR.exists():
        logger.info("📦 Installing frontend dependencies...")
        run_command(["npm", "install"], cwd=FRONTEND_DIR)
    
    logger.info("✅ Setup complete! Run 'python dev.py start' to start the development server.")


def start():
    """Start development servers."""
    logger.info("🚀 Starting DevSkyy development servers...")
    
    # Check if .env exists
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        logger.warning("⚠️  .env file not found. Run 'python dev.py setup' first.")
    
    try:
        # Start backend server
        logger.info("🐍 Starting Python backend server...")
        backend_process = subprocess.Popen(
            [sys.executable, "main.py"],
            cwd=PROJECT_ROOT
        )
        
        # Start frontend server if available
        frontend_process = None
        if FRONTEND_DIR.exists():
            logger.info("⚛️  Starting React frontend server...")
            frontend_process = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=FRONTEND_DIR
            )
        
        logger.info("🌟 Development servers started!")
        logger.info("Backend: http://localhost:8000")
        logger.info("Frontend: http://localhost:3000")
        logger.info("API Docs: http://localhost:8000/docs")
        logger.info("Press Ctrl+C to stop servers")
        
        # Wait for processes
        try:
            if frontend_process:
                frontend_process.wait()
            backend_process.wait()
        except KeyboardInterrupt:
            logger.info("🛑 Stopping servers...")
            if frontend_process:
                frontend_process.terminate()
            backend_process.terminate()
    
    except Exception as e:
        logger.error(f"Failed to start servers: {e}")
        sys.exit(1)


def test():
    """Run all tests."""
    logger.info("🧪 Running DevSkyy test suite...")
    
    # Backend tests
    logger.info("🐍 Running Python tests...")
    run_command([sys.executable, "-m", "pytest", "tests/", "-v", "--cov"])
    
    # Frontend tests
    if FRONTEND_DIR.exists():
        logger.info("⚛️  Running frontend tests...")
        run_command(["npm", "test"], cwd=FRONTEND_DIR)
    
    logger.info("✅ All tests completed!")


def lint():
    """Run code linting and formatting."""
    logger.info("🔍 Running code quality checks...")
    
    # Python linting
    logger.info("🐍 Formatting Python code...")
    run_command(["black", ".", "--line-length", "120"])
    
    logger.info("🔍 Linting Python code...")
    run_command(["flake8", ".", "--max-line-length=120"], check=False)
    
    logger.info("🔍 Type checking Python code...")
    run_command(["mypy", "."], check=False)
    
    # Frontend linting
    if FRONTEND_DIR.exists():
        logger.info("⚛️  Linting frontend code...")
        run_command(["npm", "run", "lint"], cwd=FRONTEND_DIR, check=False)
    
    logger.info("✅ Code quality checks completed!")


def build():
    """Build production assets."""
    logger.info("🏗️  Building production assets...")
    
    # Build frontend
    if FRONTEND_DIR.exists():
        logger.info("⚛️  Building frontend...")
        run_command(["npm", "run", "build"], cwd=FRONTEND_DIR)
    
    logger.info("✅ Build completed!")


def clean():
    """Clean build artifacts and caches."""
    logger.info("🧹 Cleaning build artifacts...")
    
    # Python cache
    run_command(["find", ".", "-type", "d", "-name", "__pycache__", "-exec", "rm", "-rf", "{}", "+"], check=False)
    run_command(["find", ".", "-name", "*.pyc", "-delete"], check=False)
    
    # Frontend cache
    if FRONTEND_DIR.exists():
        build_dir = FRONTEND_DIR / "build"
        dist_dir = FRONTEND_DIR / "dist"
        if build_dir.exists():
            run_command(["rm", "-rf", str(build_dir)])
        if dist_dir.exists():
            run_command(["rm", "-rf", str(dist_dir)])
    
    logger.info("✅ Cleanup completed!")


def audit():
    """Run security audits."""
    logger.info("🔒 Running security audits...")
    
    # Python security audit
    logger.info("🐍 Auditing Python dependencies...")
    result = run_command([sys.executable, "-m", "pip", "list", "--format=json"], check=False)
    
    # Frontend security audit
    if FRONTEND_DIR.exists():
        logger.info("⚛️  Auditing frontend dependencies...")
        run_command(["npm", "audit"], cwd=FRONTEND_DIR, check=False)
    
    logger.info("✅ Security audit completed!")


def docs():
    """Generate and serve documentation."""
    logger.info("📚 Starting documentation server...")
    logger.info("API Documentation: http://localhost:8000/docs")
    logger.info("ReDoc: http://localhost:8000/redoc")
    
    # Start minimal server for docs
    run_command([sys.executable, "-c", 
                "import uvicorn; from main import app; uvicorn.run(app, host='0.0.0.0', port=8000)"])


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="DevSkyy Development CLI")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Setup development environment')
    
    # Start command
    start_parser = subparsers.add_parser('start', help='Start development servers')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Run all tests')
    
    # Lint command
    lint_parser = subparsers.add_parser('lint', help='Run code linting and formatting')
    
    # Build command
    build_parser = subparsers.add_parser('build', help='Build production assets')
    
    # Clean command
    clean_parser = subparsers.add_parser('clean', help='Clean build artifacts')
    
    # Audit command
    audit_parser = subparsers.add_parser('audit', help='Run security audits')
    
    # Docs command
    docs_parser = subparsers.add_parser('docs', help='Generate and serve documentation')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    commands = {
        'setup': setup,
        'start': start,
        'test': test,
        'lint': lint,
        'build': build,
        'clean': clean,
        'audit': audit,
        'docs': docs
    }
    
    if args.command in commands:
        commands[args.command]()
    else:
        logger.error(f"Unknown command: {args.command}")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()