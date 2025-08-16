from setuptools import setup, find_packages
from pathlib import Path
import sys

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

# Debug prints to check package discovery
print("Python version:", sys.version)
print("Setup directory:", this_directory.resolve())
print("Finding packages...")
found_packages = find_packages(include=["liara", "liara.*"])
print("Packages found:", found_packages)

setup(
    name="LiaraAPI",
    version="1.0.0",
    description="An intelligent, asynchronous search engine library for Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="stone",
    author_email="kissme.cloud@example.com",
    python_requires=">=3.9",
    license="MIT",
    keywords=[
        "liara",
        "api",
        "google"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Framework :: AsyncIO",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    packages=found_packages,
    install_requires=["aiohttp"],
    url="https://github.com/kissmeBro/LiaraAPI",
)
