"""
Setup script for Zephyr voice-to-text application
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read version from package
version = {}
with open("src/zephyr/__init__.py") as f:
    for line in f:
        if line.startswith("__version__"):
            exec(line, version)

# Read long description from README
readme_file = Path(__file__).parent / "README.md"
long_description = ""
if readme_file.exists():
    long_description = readme_file.read_text(encoding="utf-8")

setup(
    name="zephyr-voice-input",
    version=version.get("__version__", "0.1.0"),
    author="Zephyr Contributors",
    author_email="",
    description="Push-to-talk voice input for Linux",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/zephyr",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires=">=3.11",
    install_requires=[
        "PyYAML>=6.0",
        "pynput>=1.7.6",
        "PyAudio>=0.2.13",
        "faster-whisper>=0.10.0",
        "python-xlib>=0.33",
        "python-evdev>=1.6.1",
        "PyGObject>=3.46.0",
        "noisereduce>=3.0.0",
        "numpy>=1.24.0",
        "watchdog>=3.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "zephyr=zephyr.__main__:main",
        ],
    },
    include_package_data=True,
    package_data={
        "zephyr": ["config/*.yaml"],
    },
)
