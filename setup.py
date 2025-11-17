from pathlib import Path

from setuptools import find_packages, setup


"""
DevSkyy - AI-Powered Luxury E-Commerce Platform
Setup configuration for package distribution
"""

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
if requirements_file.exists():
    requirements = [
        line.strip()
        for line in requirements_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
else:
    requirements = []

setup(
    name="devskyy-platform",
    version="5.1.0",  # Updated to reflect enterprise v5.1 with GDPR compliance
    description="Enterprise-grade AI platform for luxury fashion e-commerce with full GDPR compliance",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Skyy Rose LLC",
    author_email="support@skyyrose.com",
    url="https://github.com/SkyyRoseLLC/DevSkyy",
    license="Proprietary",
    packages=find_packages(exclude=["tests", "frontend", "docs"]),
    python_requires=">=3.11",  # Python 3.11+ required for performance improvements
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=8.4.2",
            "pytest-asyncio>=0.24.0",
            "pytest-cov>=5.0.0",
            "flake8>=7.1.1",
            "black>=24.10.0",
            "isort>=5.13.2",
            "mypy>=1.0.0",
        ],
        "docs": [
            "sphinx>=7.0.0",
            "sphinx-rtd-theme>=2.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "devskyy=main:main",
            "devskyy-server=backend.server:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Framework :: FastAPI",
        "Environment :: Web Environment",
        "Typing :: Typed",
    ],
    keywords="ai, machine-learning, ecommerce, fashion, luxury, automation",
    project_urls={
        "Bug Reports": "https://github.com/SkyyRoseLLC/DevSkyy/issues",
        "Source": "https://github.com/SkyyRoseLLC/DevSkyy",
        "Documentation": "https://github.com/SkyyRoseLLC/DevSkyy/tree/main/docs",
    },
    include_package_data=True,
    zip_safe=False,
)
