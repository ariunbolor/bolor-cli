"""
Example buggy code to demonstrate Bolor's fix capabilities.
This contains various types of issues that Bolor can detect and fix.
"""

# Issue 1: Syntax error - Missing colon
def calculate_average(numbers)  # Missing colon here
    total = sum(numbers)
    count = len(numbers)
    return total / count

# Issue 2: Logical error - Division by zero
def safe_divide(a, b):
    # Should check if b is zero
    return a / b  

# Issue 3: Unused import
import datetime
import json
import os
import random

# Issue 4: Inefficient code
def find_duplicate(items):
    for i in range(len(items)):
        for j in range(len(items)):
            if i != j and items[i] == items[j]:
                return items[i]
    return None

# Issue 5: Security vulnerability - Command injection
def run_command(command):
    import subprocess
    subprocess.call(command, shell=True)  # Using shell=True is dangerous

# Issue 6: Bad variable name
def x(a, b):
    c = a + b
    return c

# Issue 7: Missing docstring
def calculate_tax(amount, rate):
    return amount * rate / 100

# Issue 8: Complex expressions
def is_valid(value):
    return value != None and value != "" and value != [] and value != {} and value != 0

# Issue 9: Redundant code
def get_first_item(items):
    if len(items) > 0:
        return items[0]
    else:
        return None

# Issue 10: Inconsistent return types
def process_value(value):
    if value < 0:
        return "Negative"
    elif value > 0:
        return 1
    else:
        return None

if __name__ == "__main__"
    # Issue 11: Missing parentheses
    numbers = [1, 2, 3, 4, 5
    avg = calculate_average(numbers)
    print("Average:", avg)
    
    # Issue 12: Wrong indentation
    x = 10
if x > 5:
    print("x is greater than 5")
