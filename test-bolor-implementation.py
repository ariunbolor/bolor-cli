#!/usr/bin/env python3
"""
Test script for the Bolor CLI implementation.
"""
import sys
from pathlib import Path

# Add current directory to path to ensure modules are found
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from bolor_core.symbol_map import build_symbol_map
from bolor_core.validator import validate_file
from bolor_core.code_checker import analyze_file_and_suggest_fixes

def test_symbol_map():
    """Test the symbol map functionality."""
    print("\n=== Testing Symbol Map ===")
    example_file = Path('examples/buggy_code.py')
    if not example_file.exists():
        print(f"Example file not found: {example_file}")
        return
    
    try:
        symbol_map = build_symbol_map(example_file.parent)
        print(f"Found {sum(len(symbols) for symbols in symbol_map.values())} symbols in {len(symbol_map)} files")
        
        # Print some example symbols
        for file_path, symbols in symbol_map.items():
            print(f"\nFile: {file_path}")
            for i, symbol in enumerate(symbols[:3], 1):  # Show first 3 symbols
                print(f"  {i}. {symbol['type']} '{symbol['name']}' at line {symbol['line']}")
            if len(symbols) > 3:
                print(f"  ... and {len(symbols) - 3} more symbols")
        
        print("Symbol map test successful!")
    except Exception as e:
        print(f"Error in symbol map test: {e}")

def test_validator():
    """Test the code validator functionality."""
    print("\n=== Testing Code Validator ===")
    example_file = Path('examples/buggy_code.py')
    if not example_file.exists():
        print(f"Example file not found: {example_file}")
        return
    
    try:
        success, error_message = validate_file(example_file)
        if success:
            print("Validation successful (no errors found)")
        else:
            print("Validation failed with error:")
            print(error_message)
            
            from bolor_core.validator import parse_traceback
            error_info = parse_traceback(error_message)
            print("\nParsed error information:")
            for key, value in error_info.items():
                print(f"  {key}: {value}")
        
        print("Validator test completed!")
    except Exception as e:
        print(f"Error in validator test: {e}")

def test_code_checker():
    """Test the code checker functionality."""
    print("\n=== Testing Code Checker ===")
    example_file = Path('examples/buggy_code.py')
    if not example_file.exists():
        print(f"Example file not found: {example_file}")
        return
    
    try:
        suggestions = analyze_file_and_suggest_fixes(example_file)
        print(f"Found {len(suggestions)} issues:")
        
        for i, (line, message, fix) in enumerate(suggestions[:5], 1):  # Show first 5 issues
            print(f"\nIssue {i} at line {line}:")
            print(f"  {message}")
            print(f"  Suggested fix: {fix}")
            
        if len(suggestions) > 5:
            print(f"\n... and {len(suggestions) - 5} more issues")
            
        print("\nCode checker test completed!")
    except Exception as e:
        print(f"Error in code checker test: {e}")

if __name__ == "__main__":
    print("=== Bolor Implementation Test ===")
    print("This script tests the core functionality of the Bolor tool.")
    
    test_symbol_map()
    test_validator()
    test_code_checker()
    
    print("\nAll tests completed!")
