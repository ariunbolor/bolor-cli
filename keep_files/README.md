# Bolor Keep Files

This directory contains the essential fixed files for the Bolor CLI project. These files are used by the `clean-setup.sh` script to reset the project to a clean state.

## Contents

- `setup.py` - Fixed setup script with proper dependencies and version information
- `bolor-cli` - Fixed CLI wrapper script that properly handles all arguments
- `deploy-bolor.py` - Python script to build and deploy the Bolor package to PyPI
- `clean-setup.sh` - Bash script to clean up the project and set up a fresh environment
- Other essential build and configuration files

## How to Use

### Clean Setup

To reset the project to a clean state and apply all the fixes:

```bash
./keep_files/clean-setup.sh
```

This will:
1. Remove all unnecessary files and scripts
2. Keep only the essential project files
3. Copy the fixed files from this directory to the main project directory
4. Set proper permissions on executable scripts

### Deploy to PyPI

After cleaning up and making any necessary changes, you can deploy to PyPI:

```bash
./deploy-bolor.py --upload
```

For test deployment to TestPyPI:

```bash
./deploy-bolor.py --test --upload
```

### Testing Locally

You can test the changes locally before deployment:

```bash
# Test CLI with help flag
python -m bolor --help

# Test specific commands
python -m bolor scan --help
python -m bolor generate "hello world"
```

## Fixed Issues

1. **CLI Argument Handling**: The bolor-cli script now properly handles all arguments, including help flags (`--help`) and multi-word prompts in the generate command.

2. **Setup Script**: The setup.py file has been fixed with proper dependencies and version information.

3. **Deployment**: A clean deployment script is provided that handles versioning, building, and uploading to PyPI.
