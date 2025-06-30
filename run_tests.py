#!/usr/bin/env python3
"""
Simple script to run tests with proper Django settings.
Usage: python run_tests.py [pytest arguments]
"""
import os
import sys
import subprocess

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anahit_backend.settings')

# Run pytest with any additional arguments
cmd = ['uv', 'run', 'pytest'] + sys.argv[1:]
exit_code = subprocess.call(cmd)
sys.exit(exit_code)