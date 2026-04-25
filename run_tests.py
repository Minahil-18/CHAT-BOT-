#!/usr/bin/env python3
"""
Test runner that changes to correct directory before running tests
"""

import os
import sys
import subprocess

# Change to phase5_voice directory
os.chdir("phase5_voice")
print(f"Working directory: {os.getcwd()}")
print(f"Python: {sys.executable}\n")

# Run the simple test
print("Running TEST_SIMPLE.py...")
print("="*70)
result = subprocess.run([sys.executable, "../TEST_SIMPLE.py"], cwd=".")
print()

if result.returncode == 0:
    print("\n✓ All tests passed!")
else:
    print(f"\n✗ Tests failed with code {result.returncode}")
    sys.exit(1)
