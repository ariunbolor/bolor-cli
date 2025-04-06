# Bolor Examples

This directory contains example files to demonstrate Bolor's capabilities in detecting and fixing code issues.

## Example 1: Fixing Buggy Python Code

The file `buggy_code.py` contains various types of issues that Bolor can detect and fix:

1. **Syntax Errors**:
   - Missing colons after function definitions
   - Missing parentheses in lists
   - Incorrect indentation

2. **Logical Errors**:
   - Division by zero vulnerabilities
   - Inefficient algorithms

3. **Code Quality Issues**:
   - Unused imports
   - Poor variable names
   - Missing docstrings
   - Complex expressions
   - Redundant code
   - Inconsistent return types

4. **Security Vulnerabilities**:
   - Command injection vulnerabilities

## How to Use Bolor with These Examples

### Command Line Interface (CLI)

To scan the example file and detect issues:

```bash
bolor scan ./examples/buggy_code.py
```

To automatically fix the detected issues:

```bash
bolor scan ./examples/buggy_code.py --fix
```

For more detailed output:

```bash
bolor scan ./examples/buggy_code.py --fix --verbose
```

### Programmatic API

You can also use Bolor programmatically in your own Python code:

```python
from pathlib import Path
from bolor.utils.config import Config
from bolor.agent.scanner import Scanner
from bolor.agent.fixer import Fixer

# Create configuration
config = Config()

# Create scanner and fixer
scanner = Scanner(config)
fixer = Fixer(config)

# Scan for issues
file_path = Path("./examples/buggy_code.py")
issues = scanner.scan_file(file_path)

# Print detected issues
for issue in issues:
    print(f"Issue: {issue.issue_type} - {issue.description}")
    print(f"  Line: {issue.line_number}")
    
# Fix the issues
fixed_issues = fixer.fix_issues(issues)

# Print fixed issues
for issue in fixed_issues:
    print(f"Fixed: {issue.issue_type} - {issue.description}")
    print(f"  Original: {issue.code_snippet}")
    print(f"  Fixed: {issue.fixed_code_snippet}")
```

### Expected Fixes

When Bolor fixes the example file, you can expect the following improvements:

1. **Syntax fixes**:
   - Added missing colons after function definitions
   - Added closing bracket for the list
   - Fixed indentation issues

2. **Logical fixes**:
   - Added check for division by zero in `safe_divide`
   - Improved algorithm efficiency in `find_duplicate`

3. **Code quality improvements**:
   - Removed unused imports
   - Improved variable and function names
   - Added docstrings
   - Simplified complex expressions
   - Eliminated redundant code
   - Made return types consistent

4. **Security fixes**:
   - Replaced dangerous `shell=True` with safer alternatives

## Next Steps

- Try modifying the examples to see how Bolor handles different types of issues
- Check the Bolor documentation for more advanced usage options
- Try using the `plan` command to get improvement suggestions without modifying the code
