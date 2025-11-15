#!/bin/bash
# Simple test runner that writes output to files

echo "Running Zephyr Tests..."
echo "======================="
echo ""

# Test 1: Check Python version
echo "Test 1: Python version"
python3 --version
echo ""

# Test 2: Check if modules can be imported
echo "Test 2: Import test"
python3 -c "import sys; sys.path.insert(0, 'src'); from zephyr import __version__; print('✓ Zephyr version:', __version__)" 2>&1
echo ""

# Test 3: Check if entry point exists
echo "Test 3: Entry point test"
python3 -c "import sys; sys.path.insert(0, 'src'); from zephyr.__main__ import main; print('✓ Entry point found')" 2>&1
echo ""

# Test 4: Check daemon can be imported
echo "Test 4: Daemon import test"
python3 -c "import sys; sys.path.insert(0, 'src'); from zephyr.daemon import ZephyrDaemon; print('✓ Daemon imported')" 2>&1
echo ""

# Test 5: Run integration tests
echo "Test 5: Integration tests"
python3 test_integration_workflow.py 2>&1
echo ""

# Test 6: Verify AUR package
echo "Test 6: AUR package verification"
bash test_aur_package.sh 2>&1
echo ""

echo "======================="
echo "Tests complete!"
