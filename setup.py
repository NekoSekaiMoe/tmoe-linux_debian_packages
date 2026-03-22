#!/usr/bin/env python3
"""Setup script for tmoe-python."""

from setuptools import setup, find_packages

setup(
    name="tmoe",
    version="2.0.0",
    description="TMOE - More Optional Environments (Python 3.10+)",
    author="2moe",
    author_email="2moe@example.com",
    url="https://github.com/2moe/tmoe",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.10",
    install_requires=[
        "textual>=0.52.0",
        "pydantic>=2.0",
        "httpx>=0.27.0",
        "rich>=13.0",
        "typing-extensions>=4.0",
    ],
    entry_points={
        "console_scripts": [
            "tmoe=tmoe.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Android",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
)
