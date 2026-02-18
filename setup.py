"""
Setup script for Mallo framework
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="mallo",
    version="0.3.0a5.1",
    author="Akum betrand",
    author_email="betrandojong146@gmail.com",
    description="A lightweight web framework with hot reload",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Betrand-dev/mallo-fr.git",
    packages=find_packages(),
    package_data={
        "mallo": ["defaults/*.html"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Internet :: WWW/HTTP :: WSGI",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "mallo=mallo.cli:cli",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
