#!/bin/bash
# Deploy Bolor to PyPI with CLI fixes

echo "==== Deploying Bolor to PyPI with CLI Fixes ===="
echo "This script will prepare and upload Bolor with CLI improvements to PyPI"

# Make sure bolor-cli is executable
if [ -f "./bolor-cli" ]; then
    echo "Making bolor-cli executable..."
    chmod +x ./bolor-cli
fi

# Ensure MANIFEST.in includes the CLI wrapper
if [ -f "./MANIFEST.in" ]; then
    # Check if bolor-cli is already in MANIFEST.in
    if ! grep -q "include bolor-cli" MANIFEST.in; then
        echo "Adding bolor-cli to MANIFEST.in..."
        echo "include bolor-cli" >> MANIFEST.in
    fi
else
    echo "Creating MANIFEST.in..."
    echo "include bolor-cli" > MANIFEST.in
fi

# Make sure README.md has updated CLI instructions
README_UPDATED=false
if [ -f "./README.md" ]; then
    # Check if usage instructions mention CLI fix
    if ! grep -q "directly using the 'bolor' command" README.md; then
        echo "Consider updating README.md with new CLI usage instructions."
    fi
fi

# Silence the annoying urllib3 warnings first
if [ -f "./patch_requests.py" ]; then
    echo "Patching requests library to silence warnings..."
    python3 ./patch_requests.py
fi

# Clean up previous build artifacts
echo "Cleaning up previous build artifacts..."
rm -rf dist/ build/ *.egg-info/

# Install required packages if not already installed
echo "Making sure build tools are installed..."
pip install --upgrade pip wheel build twine

# Build the package
echo "Building the package..."
PYTHONWARNINGS=ignore python3 -m build

# Check if build was successful
if [ ! -d "dist" ] || [ -z "$(ls -A dist 2>/dev/null)" ]; then
    echo "❌ Build failed! No distribution files were created."
    echo "Please check the setup.py file for syntax errors."
    echo "Common issues include:"
    echo "- Duplicate parameters in setup()"
    echo "- Invalid syntax in long_description or other fields"
    echo ""
    echo "Would you like to continue anyway? (y/n)"
    read -r continue_anyway
    if [[ ! "$continue_anyway" =~ ^[Yy]$ ]]; then
        echo "Exiting without uploading."
        exit 1
    fi
else
    # Check the package
    echo "✅ Build successful!"
    echo "Checking the package..."
    PYTHONWARNINGS=ignore python3 -m twine check dist/*
fi

echo "Ready to upload to PyPI!"
echo "-------------------------"
echo "Options:"
echo "1. Upload to Test PyPI (for testing)"
echo "2. Upload to real PyPI (for production)"
echo "3. Exit without uploading"
read -p "Choose an option (1-3): " option

case $option in
    1)
        echo "Uploading to Test PyPI..."
        PYTHONWARNINGS=ignore python3 -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*
        
        echo ""
        echo "Package uploaded to Test PyPI!"
        echo "To test installation, run:"
        echo "pip install --index-url https://test.pypi.org/simple/ --no-deps bolor"
        
        echo ""
        echo "After installation, the 'bolor' command should work directly."
        echo "Try: bolor generate \"login HTML\" --output login.html"
        ;;
    2)
        echo "Uploading to real PyPI..."
        PYTHONWARNINGS=ignore python3 -m twine upload dist/*
        
        echo ""
        echo "Package uploaded to PyPI!"
        echo "To install the new version, run:"
        echo "pip install --upgrade bolor"
        
        echo ""
        echo "After installation, the 'bolor' command should work directly."
        echo "Try: bolor generate \"login HTML\" --output login.html"
        ;;
    *)
        echo "Exiting without uploading."
        echo "The package has been built and is available in the 'dist/' directory."
        ;;
esac

echo ""
echo "Deployment complete! 🎉"
