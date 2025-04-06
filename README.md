# Bolor

Bolor is a local LLM-powered CLI tool that helps you understand, explain, fix, and optimize your Python code without sending it to external services. By leveraging local GGUF models, Bolor provides intelligent code assistance while maintaining your privacy.

## Features

- 🔍 **Code Analysis** - Find issues and get suggested fixes
- 📖 **Code Explanation** - Understand what code does in plain English
- ⚡ **Code Optimization** - Get suggestions for improving performance and readability
- 📚 **Documentation** - Add missing docstrings and improve existing documentation
- 🧠 **Local LLM Integration** - All analysis happens locally using GGUF models

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Download required models (first time setup)
python -m bolor update
```

## Usage

### Setting Up

```bash
# Download or update GGUF models
bolor update

# Configure settings (optional)
bolor config --model phi-2 --mode accurate
bolor config --show  # View current configuration
```

### Analyzing Code

```bash
# Check code for issues
bolor check examples/example_buggy_code.py

# Automatically apply suggested fixes
bolor check examples/example_buggy_code.py --apply
```

### Understanding Code

```bash
# Explain what the code does
bolor explain examples/example_buggy_code.py

# Save explanation to a file
bolor explain examples/example_buggy_code.py -o explanation.txt
```

### Optimizing Code

```bash
# Get optimization suggestions
bolor optimize examples/example_buggy_code.py

# Apply optimizations (creates a backup)
bolor optimize examples/example_buggy_code.py --apply

# Save optimized version to a new file
bolor optimize examples/example_buggy_code.py -o optimized_code.py
```

### Documenting Code

```bash
# Find missing docstrings and suggest improvements
bolor document examples/example_buggy_code.py

# Automatically add missing documentation (creates a backup)
bolor document examples/example_buggy_code.py --apply
```

## Advanced Configuration

Bolor stores its configuration in `~/.bolor/config/config.json`. You can edit this file directly or use the `bolor config` command.

```json
{
  "model": {
    "name": "phi-2"  // Can be "phi-2" or "starcoder2-3b"
  },
  "mode": "fast",    // Can be "fast" or "accurate"
  "parameters": {
    "context_size": 2048,
    "max_tokens": 512,
    "temperature": 0.2,
    "top_p": 0.9,
    "threads": 4
  }
}
```

The default mode `fast` prioritizes speed, while `accurate` uses a higher token limit and temperature for more detailed results.

## Available Models

Bolor ships with support for two GGUF models:

- **phi-2** - Microsoft's 2.7B parameter model, general-purpose
- **starcoder2-3b** - BigCode's 3B parameter model, optimized for code

## Examples

**Example: Find and fix issues in code**

```bash
$ bolor check examples/example_buggy_code.py
⚠️ Issue 1 at line 5:
  Missing docstring in function 'calculate_sum'
  Suggested fix: """Add two numbers and return their sum."""

⚠️ Issue 2 at line 9:
  '_transform' might be undefined
  Suggested fix: Define the _transform function or replace with a defined function.

Apply suggested fixes? [y/n] (n): y
✅ Fixes applied.
```

**Example: Explain code**

```bash
$ bolor explain examples/example_buggy_code.py
📝 Explanation:
This code contains several functions with different purposes:

1. `calculate_sum`: A simple function that adds two numbers.
2. `process_data`: Attempts to process a list of data items by transforming each item, but references an undefined function `_transform`.
3. `calculate_complex_value`: Performs a complex calculation involving multiple operations.
4. `find_duplicates`: Identifies duplicate items in a list using a nested loop approach.
5. `get_large_list`: Creates a large list of squared numbers.

The main block demonstrates usage of these functions, including error handling for the undefined function issue.

The code has several issues: missing docstrings, an undefined function reference, unnecessarily complex expressions, and inefficient implementations that could be optimized.
```

## License

MIT
