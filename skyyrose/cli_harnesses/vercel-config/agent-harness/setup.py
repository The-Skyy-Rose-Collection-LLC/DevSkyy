"""Setup for cli-anything-vercel-config."""

from setuptools import find_namespace_packages, setup

setup(
    name="cli-anything-vercel-config",
    version="1.0.0",
    description="CLI harness for Vercel project settings (REST API surface not covered by vercel CLI)",
    packages=find_namespace_packages(include=["cli_anything.*"]),
    python_requires=">=3.10",
    install_requires=[
        "click>=8.1,<9.0",
        "prompt-toolkit>=3.0,<4.0",
        "requests>=2.31",
    ],
    extras_require={
        "dev": [
            "pytest>=7",
            "pytest-cov>=4",
            "requests-mock>=1.11",
            "build",
            "twine",
        ]
    },
    entry_points={
        "console_scripts": [
            "cli-anything-vercel-config=cli_anything.vercel_config.vercel_config_cli:main",
        ]
    },
)
