#!/bin/bash
# Clean setup script for Bolor
# This script cleans up the project directory and sets up a fresh environment
# for Bolor development and deployment.

echo "Bolor Clean Setup"
echo "================="
echo "This script will clean up the project directory and set up a fresh environment."

# Check if we're in the bolor directory
if [ ! -d "keep_files" ]; then
  echo "❌ Error: This script must be run from the bolor project directory."
  echo "Please run it from the directory containing the 'keep_files' folder."
  exit 1
fi

# Step 1: Clean up the project directory
echo ""
echo "Step 1: Cleaning up project directory..."
read -p "Are you sure you want to clean up the project directory? (y/n): " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
  echo "Aborted."
  exit 1
fi

# Create a list of files to keep
KEEP_FILES=(
  "bolor"
  "examples"
  "tests"
  "setup.py"
  "setup.cfg"
  "MANIFEST.in"
  "requirements.txt"
  "README.md"
  "CHANGELOG.md"
  "LICENSE"
  ".gitignore"
  "bolor-cli"
  "patch_requests.py"
  "deploy-bolor.py"
  "keep_files"
)

# Remove all unnecessary files
echo "Removing unnecessary files..."
for file in $(ls -A); do
  if [[ ! " ${KEEP_FILES[@]} " =~ " ${file} " ]]; then
    echo "  - Removing $file"
    rm -rf "$file"
  fi
done

# Step 2: Copy kept files from keep_files
echo ""
echo "Step 2: Setting up project files from keep_files..."

# Copy fixed files
echo "Copying fixed files from keep_files..."
if [ -f "keep_files/setup.py" ]; then
  cp keep_files/setup.py .
  echo "  - Copied setup.py"
fi

if [ -f "keep_files/bolor-cli" ]; then
  cp keep_files/bolor-cli .
  chmod +x bolor-cli
  echo "  - Copied bolor-cli (executable)"
fi

if [ -f "keep_files/deploy-bolor.py" ]; then
  cp keep_files/deploy-bolor.py .
  chmod +x deploy-bolor.py
  echo "  - Copied deploy-bolor.py (executable)"
fi

if [ -f "keep_files/patch_requests.py" ]; then
  cp keep_files/patch_requests.py .
  echo "  - Copied patch_requests.py"
fi

# Make sure MANIFEST.in includes bolor-cli
if [ -f "MANIFEST.in" ]; then
  if ! grep -q "include bolor-cli" MANIFEST.in; then
    echo "include bolor-cli" >> MANIFEST.in
    echo "  - Updated MANIFEST.in to include bolor-cli"
  fi
else
  echo "include bolor-cli" > MANIFEST.in
  echo "  - Created MANIFEST.in with bolor-cli included"
fi

# Fix the CLI script if it doesn't exist or is broken
if [ ! -f "bolor-cli" ]; then
  cat > bolor-cli << 'EOF'
#!/usr/bin/env python3
"""
Direct Python CLI script for Bolor.
This avoids all the bash script complexities and handles arguments directly.
"""

import sys
import os
import subprocess
from pathlib import Path

def main():
    """Main entry point with argument handling"""
    # Get all arguments
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    
    # Call bolor module with all arguments
    cmd = [sys.executable, '-m', 'bolor']
    cmd.extend(args)
    
    # Execute and return its exit code
    return subprocess.call(cmd)

if __name__ == "__main__":
    sys.exit(main())
EOF
  chmod +x bolor-cli
  echo "  - Created bolor-cli (executable)"
fi

echo ""
echo "✅ Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Make any necessary changes to the code"
echo "2. Test locally with: python -m bolor --help"
echo "3. Deploy to PyPI with: ./deploy-bolor.py --upload"
echo ""
echo "The project is now clean and ready for development."
