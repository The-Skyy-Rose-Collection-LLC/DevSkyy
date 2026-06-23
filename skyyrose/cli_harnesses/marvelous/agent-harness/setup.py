"""cli-anything-marvelous — Marvelous Designer CLI harness."""

from setuptools import find_namespace_packages, setup

setup(
    name="cli-anything-marvelous",
    version="1.0.0",
    description="CLI harness for Marvelous Designer (CLO Virtual Fashion)",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="cli-anything contributors",
    python_requires=">=3.10",
    packages=find_namespace_packages(include=["cli_anything.*"]),
    include_package_data=True,
    package_data={
        "cli_anything.marvelous": [
            "resources/scripts/*.tpl",
            "skills/SKILL.md",
        ],
    },
    install_requires=[
        "click>=8.1",
        "prompt-toolkit>=3.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "cli-anything-marvelous=cli_anything.marvelous.marvelous_cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS :: MacOS X",
        "Environment :: Console",
        "Topic :: Utilities",
    ],
)
