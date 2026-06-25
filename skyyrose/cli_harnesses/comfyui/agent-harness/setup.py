"""Package setup for cli-anything-comfyui."""

from setuptools import find_namespace_packages, setup

setup(
    name="cli-anything-comfyui",
    version="1.0.0",
    description="cli-anything harness for ComfyUI — Tier 2 #7",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    python_requires=">=3.11",
    packages=find_namespace_packages(include=["cli_anything.*"]),
    install_requires=[
        "click>=8.1,<9.0",
        "httpx>=0.24.0",
    ],
    extras_require={
        "repl": ["prompt-toolkit>=3.0,<4.0"],
        "all": [
            "httpx>=0.24.0",
            "prompt-toolkit>=3.0,<4.0",
        ],
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "build",
            "twine",
        ],
    },
    entry_points={
        "console_scripts": [
            "comfyui=cli_anything.comfyui.comfyui_cli:main",
            "cli-anything-comfyui=cli_anything.comfyui.comfyui_cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
