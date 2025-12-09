#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
飞行参数分析工具安装配置文件
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh.readlines() if line.strip() and not line.startswith("#")]

setup(
    name="flight-parameter-analyzer",
    version="2.0.0",
    author="Flight Analysis Team",
    author_email="support@flight-analysis.com",
    description="飞行参数分析工具，用于分析飞行数据并生成专业报告",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/flight-analysis/flight-parameter",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Environment :: X11 Applications :: wxWidgets",
    ],
    python_requires='>=3.6',
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'flight-analyzer=app:main',
        ],
    },
    package_data={
        '': ['*.ico', '*.csv'],
    },
    include_package_data=True,
)