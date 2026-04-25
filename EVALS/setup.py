#!/usr/bin/env python3
"""
Setup script for Person A evaluation workspace
Creates all necessary directories and initializes placeholder files
"""

import os
import json
from pathlib import Path

# Define the directory structure
DIRS = [
    "test_data",
    "correctness",
    "utils",
    "tests",
    "outputs",
]

def create_directories():
    """Create all necessary directories"""
    base_path = Path(__file__).parent
    for dir_name in DIRS:
        dir_path = base_path / dir_name
        dir_path.mkdir(exist_ok=True)
        print(f"✓ Created/verified: {dir_path}")

def create_init_files():
    """Create __init__.py files for Python packages"""
    base_path = Path(__file__).parent
    for dir_name in ["correctness", "utils", "tests"]:
        init_file = base_path / dir_name / "__init__.py"
        init_file.touch()
        print(f"✓ Created: {init_file}")

def main():
    print("Setting up Person A evaluation workspace...\n")
    
    create_directories()
    print()
    create_init_files()
    
    print("\n✅ Setup complete!")
    print("\nNext steps:")
    print("1. cd EVALS")
    print("2. pip install -r requirements.txt")
    print("3. python -m pytest tests/ -v")
    print("\nStart with Phase 1: Design & Setup")

if __name__ == "__main__":
    main()
