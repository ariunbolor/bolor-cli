#!/bin/bash

# Make the script exit on first error
set -e

# Display commands as they're run
set -x

echo "===== Testing Bolor CLI ====="

# Update models
echo "Updating models..."
bolor update

# Check a file
echo "Checking example_buggy_code.py..."
bolor check examples/example_buggy_code.py

# Get an explanation
echo "Explaining example_buggy_code.py..."
bolor explain examples/example_buggy_code.py

# Test the optimize command
echo "Testing optimize command..."
bolor optimize examples/example_buggy_code.py 

# Show configuration
echo "Showing configuration..."
bolor config --show

echo "===== All tests completed ====="
