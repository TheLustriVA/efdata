"""Setup script for EFData - Economic Flow Data Integration Platform."""
from setuptools import setup, find_packages

# Read the README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="efdata",
    version="0.1.0",
    author="Kieran Bicheno",
    author_email="kieran.bicheno@gmail.com",
    description="Economic Flow Data Integration Platform for Australian Economic Statistics",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/TheLustriVA/efdata",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.12",
    entry_points={
        "console_scripts": [
            "efdata-scheduler=src.scheduler.spider_scheduler:main",
            "efdata-api=frontend.api:main",
        ],
    },
)