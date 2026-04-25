@echo off
REM Setup script for Person A evaluation workspace on Windows
REM Creates all necessary directories and files

echo.
echo ====================================================
echo Person A Evaluation Suite - Setup
echo ====================================================
echo.

REM Change to EVALS directory
cd /d "%~dp0"

REM Create directories
echo Creating directory structure...
if not exist "test_data" mkdir test_data
if not exist "correctness" mkdir correctness
if not exist "utils" mkdir utils
if not exist "tests" mkdir tests
if not exist "outputs" mkdir outputs

echo.
echo Creating Python package files...
type nul > correctness\__init__.py
type nul > utils\__init__.py
type nul > tests\__init__.py

echo.
echo ====================================================
echo Setup Complete!
echo ====================================================
echo.
echo Next steps:
echo 1. pip install -r requirements.txt
echo 2. Read QUICK_START.md
echo 3. Read README.md
echo.
echo Start with Phase 1: Design ^& Setup
echo.
pause
