#!/usr/bin/env python
"""Setup script for hanzo-router package."""

import os
import sys
from setuptools import setup, find_packages

# Add the main router directory to the path to ensure imports work
router_path = "/Users/z/work/hanzo/router"
if os.path.exists(router_path):
    sys.path.insert(0, router_path)

setup(
    name="hanzo-router",
    version="1.74.3",
    packages=find_packages(where=router_path),
    package_dir={"": router_path},
    include_package_data=True,
)