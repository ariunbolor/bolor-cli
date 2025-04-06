#!/bin/bash
# Test script for Bolor CLI
# This script tests the Bolor CLI functionality to ensure it works correctly

echo "Bolor CLI Test Script"
echo "===================="
echo "This script tests the Bolor CLI functionality."

# Test 1: Global help flag
echo ""
echo "Test 1: Global help flag"
echo "========================"
echo "Running: python -m bolor --help"
python -m bolor --help
if [ $? -eq 0 ]; then
  echo "✅ Test 1 passed!"
else
  echo "❌ Test 1 failed: Global help flag doesn't work"
fi

# Test 2: Command-specific help flag
echo ""
echo "Test 2: Command-specific help flag"
echo "=================================="
echo "Running: python -m bolor scan --help"
python -m bolor scan --help
if [ $? -eq 0 ]; then
  echo "✅ Test 2 passed!"
else
  echo "❌ Test 2 failed: Command-specific help flag doesn't work"
fi

# Test 3: Generate command with multi-word prompt
echo ""
echo "Test 3: Generate command with multi-word prompt"
echo "=============================================="
echo "Running: python -m bolor generate \"hello world\""
python -m bolor generate "hello world"
if [ $? -eq 0 ]; then
  echo "✅ Test 3 passed!"
else
  echo "❌ Test 3 failed: Generate command with multi-word prompt doesn't work"
fi

# Test 4: CLI script with global help flag
echo ""
echo "Test 4: CLI script with global help flag"
echo "======================================="
if [ -f "./bolor-cli" ]; then
  echo "Running: ./bolor-cli --help"
  ./bolor-cli --help
  if [ $? -eq 0 ]; then
    echo "✅ Test 4 passed!"
  else
    echo "❌ Test 4 failed: CLI script with global help flag doesn't work"
  fi
else
  echo "⚠️ Test 4 skipped: bolor-cli script not found"
fi

# Test 5: CLI script with command-specific help flag
echo ""
echo "Test 5: CLI script with command-specific help flag"
echo "================================================="
if [ -f "./bolor-cli" ]; then
  echo "Running: ./bolor-cli scan --help"
  ./bolor-cli scan --help
  if [ $? -eq 0 ]; then
    echo "✅ Test 5 passed!"
  else
    echo "❌ Test 5 failed: CLI script with command-specific help flag doesn't work"
  fi
else
  echo "⚠️ Test 5 skipped: bolor-cli script not found"
fi

# Test 6: CLI script with generate command and multi-word prompt
echo ""
echo "Test 6: CLI script with generate command and multi-word prompt"
echo "============================================================="
if [ -f "./bolor-cli" ]; then
  echo "Running: ./bolor-cli generate \"hello world\""
  ./bolor-cli generate "hello world"
  if [ $? -eq 0 ]; then
    echo "✅ Test 6 passed!"
  else
    echo "❌ Test 6 failed: CLI script with generate command and multi-word prompt doesn't work"
  fi
else
  echo "⚠️ Test 6 skipped: bolor-cli script not found"
fi

# Summary
echo ""
echo "Test Summary"
echo "==========="
echo "The tests verify that Bolor CLI correctly handles:"
echo "- Global help flags (--help)"
echo "- Command-specific help flags (scan --help)"
echo "- Generate commands with multi-word prompts"
echo "- Both direct module invocation (python -m bolor) and CLI script (./bolor-cli)"
echo ""
echo "If all tests passed, the Bolor CLI is working correctly."
echo "If any tests failed, check the error messages for details."
