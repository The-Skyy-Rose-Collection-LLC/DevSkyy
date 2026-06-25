"""
setup.py for cli-anything-hf-spaces.

Install:
    pip install -e .                          # core only
    pip install -e ".[hf]"                    # + huggingface_hub
    pip install -e ".[logs]"                  # + httpx for log streaming
    pip install -e ".[repl]"                  # + prompt-toolkit for REPL
    pip install -e ".[all]"                   # everything
    pip install -e ".[dev]"                   # dev dependencies
"""

from setuptools import find_namespace_packages, setup

setup(
    name="cli-anything-hf-spaces",
    version="1.0.0",
    description="cli-anything harness for HuggingFace Spaces administration",
    python_requires=">=3.10",
    packages=find_namespace_packages(include=["cli_anything.*"]),
    install_requires=[
        "click>=8.1,<9.0",
    ],
    extras_require={
        "hf": [
            "huggingface_hub>=0.26.0,<1.0",
        ],
        "logs": [
            "huggingface_hub>=0.26.0,<1.0",
            "httpx>=0.24.0",
        ],
        "repl": [
            "prompt-toolkit>=3.0,<4.0",
        ],
        "all": [
            "huggingface_hub>=0.26.0,<1.0",
            "httpx>=0.24.0",
            "prompt-toolkit>=3.0,<4.0",
        ],
        "dev": [
            "huggingface_hub>=0.26.0,<1.0",
            "httpx>=0.24.0",
            "prompt-toolkit>=3.0,<4.0",
            "pytest>=7",
            "pytest-cov>=4",
            "build",
            "twine",
        ],
    },
    entry_points={
        "console_scripts": [
            "hf-spaces=cli_anything.hf_spaces.hf_spaces_cli:main",
            "cli-anything-hf-spaces=cli_anything.hf_spaces.hf_spaces_cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Environment :: Console",
    ],
)
