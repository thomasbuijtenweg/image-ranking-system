"""
Setup script for the Image Ranking System.

This script can be used to install the application as a package
or to create distributable packages.
"""

from setuptools import setup, find_packages

# Read the README file for the long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read the requirements file
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="image-ranking-system",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A sophisticated pairwise comparison system for ranking collections of images",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/image-ranking-system",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Graphics :: Viewers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "image-ranking-system=main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)