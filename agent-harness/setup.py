#!/usr/bin/env python3
"""setup.py for cli-anything-openclaw-admin."""

from setuptools import find_namespace_packages, setup


with open("cli_anything/openclaw_admin/README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


setup(
    name="cli-anything-openclaw-admin",
    version="0.1.0",
    description="CLI-Anything harness for the OpenClaw Admin Vue/Express console.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Alex-Shen1121/OpenClaw-Admin",
    packages=find_namespace_packages(include=["cli_anything.*"]),
    python_requires=">=3.9",
    install_requires=[
        "click>=8.0.0",
        "prompt-toolkit>=3.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "cli-anything-openclaw-admin=cli_anything.openclaw_admin.openclaw_admin_cli:cli",
        ],
    },
    package_data={
        "cli_anything.openclaw_admin": ["skills/*.md"],
    },
    include_package_data=True,
    zip_safe=False,
)
