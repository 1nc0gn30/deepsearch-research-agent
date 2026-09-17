#!/usr/bin/env python3
"""Setup script for deepsearch-research-agent."""

from setuptools import setup, find_packages

setup(
    name="deepsearch-research-agent",
    version="0.1.0",
    description="Autonomous Multi-Perspective Deep Research & Verification Agent",
    author="DeepSearch Research Team",
    author_email="dev@deepsearch-agent.org",
    url="https://github.com/deepsearch-agent/deepsearch-research-agent",
    license="MIT",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.9",
    install_requires=[],
    extras_require={
        "dev": ["pytest>=7.0.0", "pytest-cov>=4.0.0"],
    },
    entry_points={
        "console_scripts": [
            "deepsearch=deepsearch_research_agent.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
)
