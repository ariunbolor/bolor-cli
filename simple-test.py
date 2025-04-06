#!/usr/bin/env python3
"""
Simple test script for Bolor components.
"""
import sys
from pathlib import Path

# Import modules to test
from bolor_core.symbol_map import build_symbol_map
from bolor_core.code_checker import analyze_file_and_suggest_fixes

# Test file path
example_file = Path('examples/buggy_code.py')
print(f"Testing with file: {example_file}")
print(f"File exists: {example_file.exists()}")

# Test symbol mapping
print("\nTesting symbol mapping:")
symbol_map = build_symbol_map(example_file.parent)
print(f"Symbol map contains {len(symbol_map)} files")
for file_path, symbols in symbol_map.items():
    print(f"File: {file_path} - {len(symbols)} symbols")

# Print a separator
print("\n" + "-" * 40 + "\n")

# Test code checker
print("Testing code checker:")
try:
    suggestions = analyze_file_and_suggest_fixes(example_file)
    print(f"Found {len(suggestions)} issues")
    
    # Print first few suggestions
    for i, (line, message, fix) in enumerate(suggestions[:3], 1):
        print(f"Issue {i}: Line {line} - {message}")
except Exception as e:
    print(f"Error in code checker: {e}")

print("\nTest completed!")
