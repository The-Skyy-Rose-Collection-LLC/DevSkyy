"""cli-anything-trellis — setup.py

Namespace package: cli_anything.trellis
Entry point:       trellis → cli_anything.trellis.trellis_cli:main
"""

from setuptools import find_namespace_packages, setup

setup(
    name="cli-anything-trellis",
    version="1.0.0",
    description="CLI harness for Microsoft TRELLIS.2 image-to-3D generation",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="DevSkyy",
    python_requires=">=3.10",
    # Namespace package — do NOT add cli_anything/__init__.py
    packages=find_namespace_packages(include=["cli_anything.*"]),
    package_data={
        "cli_anything.trellis": [
            "resources/trellis_runner.py",
            "skills/SKILL.md",
        ],
    },
    install_requires=[
        "click>=8.1",
        "prompt-toolkit>=3.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4",
            "pytest-cov>=4.1",
            # Pillow only needed for E2E tests
            "Pillow>=10.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "trellis=cli_anything.trellis.trellis_cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Multimedia :: Graphics :: 3D Modeling",
    ],
)
