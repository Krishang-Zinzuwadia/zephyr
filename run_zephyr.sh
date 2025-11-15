#!/bin/bash
set -e

echo "=== Zephyr Startup Script ===" > /tmp/zephyr_run.log 2>&1
echo "Working directory: $(pwd)" >> /tmp/zephyr_run.log 2>&1
echo "Python version: $(python3 --version)" >> /tmp/zephyr_run.log 2>&1
echo "" >> /tmp/zephyr_run.log 2>&1

export PYTHONPATH="$PWD/src:$PYTHONPATH"
echo "PYTHONPATH set to: $PYTHONPATH" >> /tmp/zephyr_run.log 2>&1
echo "" >> /tmp/zephyr_run.log 2>&1

echo "Testing imports..." >> /tmp/zephyr_run.log 2>&1
python3 -c "import sys; sys.path.insert(0, 'src'); import zephyr; print('✓ Zephyr imported')" >> /tmp/zephyr_run.log 2>&1

echo "" >> /tmp/zephyr_run.log 2>&1
echo "Starting Zephyr..." >> /tmp/zephyr_run.log 2>&1
python3 simple_test.py >> /tmp/zephyr_run.log 2>&1
