#!/usr/bin/env python3
"""
Deploy Bolor to PyPI
This script packages and deploys the fixed version of Bolor.

Usage: python3 deploy-bolor.py [--test] [--upload]
"""

import os
import sys
import re
import subprocess
import shutil
import argparse

def update_version(setup_py_path, version=None):
    """Update the version number in setup.py"""
    if not os.path.exists(setup_py_path):
        print(f"❌ Could not find {setup_py_path}")
        return False
    
    # Read the file
    with open(setup_py_path, 'r') as f:
        content = f.read()
    
    # Extract the current version
    version_match = re.search(r'version="([^"]+)"', content)
    if not version_match:
        print("❌ Could not find version number in setup.py")
        return False
    
    current_version = version_match.group(1)
    print(f"📦 Current version: {current_version}")
    
    if version is None:
        # Auto-increment the patch version
        parts = current_version.split('.')
        if len(parts) < 3:
            parts = parts + ['0'] * (3 - len(parts))
        
        patch = int(parts[2])
        parts[2] = str(patch + 1)
        new_version = '.'.join(parts)
    else:
        new_version = version
    
    # Replace the version
    new_content = re.sub(
        r'version="([^"]+)"',
        f'version="{new_version}"',
        content
    )
    
    # Write the updated file
    with open(setup_py_path, 'w') as f:
        f.write(new_content)
    
    print(f"✅ Updated version to {new_version}")
    return new_version

def ensure_cli_script(project_dir):
    """Make sure the bolor-cli script is properly included"""
    cli_path = os.path.join(project_dir, "bolor-cli")
    
    if not os.path.exists(cli_path):
        print("⚠️ bolor-cli script not found, creating it...")
        
        cli_content = """#!/usr/bin/env python3
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
"""
        
        with open(cli_path, 'w') as f:
            f.write(cli_content)
        
        os.chmod(cli_path, 0o755)
        print(f"✅ Created bolor-cli at {cli_path}")
    else:
        print(f"✅ Found existing bolor-cli at {cli_path}")
    
    # Make sure MANIFEST.in includes bolor-cli
    manifest_path = os.path.join(project_dir, "MANIFEST.in")
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r') as f:
            manifest_content = f.read()
        
        if "include bolor-cli" not in manifest_content:
            print("⚠️ Adding bolor-cli to MANIFEST.in")
            with open(manifest_path, 'a') as f:
                f.write("\ninclude bolor-cli\n")
        else:
            print("✅ bolor-cli already in MANIFEST.in")
    else:
        print("⚠️ Creating MANIFEST.in")
        with open(manifest_path, 'w') as f:
            f.write("include bolor-cli\n")
    
    return True

def build_package(project_dir):
    """Build the Python package"""
    print("🔨 Building package...")
    
    # Save current directory
    original_dir = os.getcwd()
    os.chdir(project_dir)
    
    # Clean up any old builds
    for dir_name in ['dist', 'build', '*.egg-info']:
        try:
            if os.path.exists(dir_name):
                shutil.rmtree(dir_name)
                print(f"🧹 Removed {dir_name}")
        except:
            pass
    
    # Build the package
    try:
        subprocess.run(
            [sys.executable, 'setup.py', 'sdist', 'bdist_wheel'],
            check=True
        )
        print("✅ Build completed successfully")
        os.chdir(original_dir)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {str(e)}")
        os.chdir(original_dir)
        return False

def upload_to_pypi(project_dir, test=False):
    """Upload the package to PyPI"""
    print(f"📤 Uploading to {'TestPyPI' if test else 'PyPI'}...")
    
    # Save current directory
    original_dir = os.getcwd()
    os.chdir(project_dir)
    
    # Check if twine is installed
    try:
        subprocess.run(['twine', '--version'], check=True, capture_output=True)
    except:
        print("⚠️ Twine not found. Installing...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'twine'], check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install twine: {str(e)}")
            os.chdir(original_dir)
            return False
    
    # Upload with twine
    try:
        cmd = ['twine', 'upload']
        if test:
            cmd.extend(['--repository-url', 'https://test.pypi.org/legacy/'])
        cmd.append('dist/*')
        
        subprocess.run(' '.join(cmd), shell=True, check=True)
        print("✅ Upload completed successfully")
        os.chdir(original_dir)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Upload failed: {str(e)}")
        os.chdir(original_dir)
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Deploy Bolor')
    parser.add_argument('--test', action='store_true', help='Upload to TestPyPI instead of PyPI')
    parser.add_argument('--upload', action='store_true', help='Upload to PyPI after building')
    parser.add_argument('--version', type=str, help='Specific version to set (default: auto-increment)')
    args = parser.parse_args()
    
    print("Bolor Deployment Script")
    print("======================")
    
    # Get the project directory
    project_dir = os.getcwd()
    print(f"📂 Project directory: {project_dir}")
    
    # Ensure CLI script exists and is in MANIFEST.in
    ensure_cli_script(project_dir)
    
    # Update version
    setup_py_path = os.path.join(project_dir, 'setup.py')
    new_version = update_version(setup_py_path, args.version)
    if not new_version:
        return 1
    
    # Build the package
    if not build_package(project_dir):
        return 1
    
    # Upload if requested
    if args.upload:
        if not upload_to_pypi(project_dir, test=args.test):
            return 1
        
        repo = "TestPyPI" if args.test else "PyPI"
        print(f"\n🎉 Bolor {new_version} successfully deployed to {repo}!")
        print("\nTo install the new version, run:")
        if args.test:
            print(f"pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple bolor=={new_version}")
        else:
            print(f"pip install --upgrade bolor")
    else:
        print("\n📦 Bolor package built successfully!")
        print("\nTo upload to PyPI, run:")
        print("python3 deploy-bolor.py --upload")
    
    print("\nAfter installation, the 'bolor' command should work with all arguments.")
    print("Test with: bolor scan --help")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
