"""
cli-anything-skyyrose-theme — meta-CLI for the SkyyRose WordPress theme dev loop.

Wraps deploy-theme.sh, PHPCS, wp-cli-over-SSH, and version management into a
unified, scriptable interface with a REPL default mode.
"""

from setuptools import find_namespace_packages, setup

setup(
    name="cli-anything-skyyrose-theme",
    version="1.0.0",
    description="Meta-CLI unifying the SkyyRose WordPress theme dev loop",
    author="The-Skyy-Rose-Collection",
    python_requires=">=3.10",
    packages=find_namespace_packages(include=["cli_anything.*"]),
    install_requires=[
        "click>=8.1,<9.0",
        "prompt-toolkit>=3.0,<4.0",
        "requests>=2.28,<3.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7",
            "pytest-cov>=4",
            "responses>=0.25",
            "build",
            "twine",
        ],
    },
    entry_points={
        "console_scripts": [
            "cli-anything-skyyrose-theme=cli_anything.skyyrose_theme.skyyrose_theme_cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
