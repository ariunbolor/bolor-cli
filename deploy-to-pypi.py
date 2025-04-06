#!/usr/bin/env python3
"""
Simple script to build and deploy Bolor to PyPI
"""

import os
import sys
import re
import subprocess
import shutil

def clean_build_dirs():
    """Remove old build artifacts"""
    print("🧹 Cleaning build directories...")
    
    dirs_to_clean = ['dist', 'build', '*.egg-info']
    for dir_name in dirs_to_clean:
        try:
            if os.path.exists(dir_name):
                if os.path.isdir(dir_name):
                    shutil.rmtree(dir_name)
                else:
                    os.unlink(dir_name)
                print(f"  Removed {dir_name}")
        except Exception as e:
            print(f"  Warning: Could not remove {dir_name}: {e}")
    
    print("✅ Cleanup complete")

def build_package():
    """Build the package distribution files"""
    print("🔨 Building package...")
    
    try:
        subprocess.run(
            [sys.executable, 'setup.py', 'sdist', 'bdist_wheel'],
            check=True
        )
        print("✅ Build completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {str(e)}")
        return False

def upload_to_pypi(test=False):
    """Upload the package to PyPI using twine"""
    destination = "TestPyPI" if test else "PyPI"
    print(f"📤 Uploading to {destination}...")
    
    # Check if twine is installed
    try:
        subprocess.run(['twine', '--version'], check=True, capture_output=True)
    except:
        print("⚠️ Twine not found. Installing...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'twine'], check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install twine: {str(e)}")
            return False
    
    # Upload with twine
    try:
        cmd = [sys.executable, '-m', 'twine', 'upload']
        if test:
            cmd.extend(['--repository-url', 'https://test.pypi.org/legacy/'])
        cmd.append('dist/*')
        
        # Use a different command format for more reliable execution
        upload_cmd = f"{sys.executable} -m twine upload {'--repository-url https://test.pypi.org/legacy/ ' if test else ''}dist/*"
        subprocess.run(upload_cmd, shell=True, check=True)
        print(f"✅ Successfully uploaded to {destination}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Upload failed: {str(e)}")
        return False

def main():
    """Main function"""
    print("Bolor PyPI Deployment")
    print("====================")
    
    # Parse arguments
    test_mode = "--test" in sys.argv
    build_only = "--build-only" in sys.argv
    # Read current version from setup.py
    try:
        with open('setup.py', 'r') as f:
            setup_content = f.read()
            version_match = re.search(r'version="([^"]+)"', setup_content)
            if version_match:
                version = version_match.group(1)
                print(f"📦 Current version: {version}")
            else:
                version = "0.2.6"  # Default if not found
                print(f"⚠️ Version not found in setup.py, using default: {version}")
    except Exception as e:
        version = "0.2.6"  # Default if error occurs
        print(f"⚠️ Error reading version from setup.py: {e}")
        print(f"⚠️ Using default version: {version}")
    
    # Make sure script permissions are set correctly
    for script in ["bolor-cli", "bolor-wrap", "bolor-cli.sh"]:
        if os.path.exists(script):
            print(f"🔒 Setting executable permissions for {script}...")
            os.chmod(script, 0o755)
    
    # Clean, build, and upload
    clean_build_dirs()
    if build_package():
        print(f"📦 Built bolor version {version}")
        
        if not build_only:
            if upload_to_pypi(test=test_mode):
                destination = "TestPyPI" if test_mode else "PyPI"
                print(f"\n🎉 Bolor {version} successfully deployed to {destination}!")
                print("\nTo install the new version, run:")
                if test_mode:
                    print(f"pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple bolor=={version}")
                else:
                    print(f"pip install --upgrade bolor")
            else:
                return 1
        else:
            print("\n📦 Package built but not uploaded (--build-only specified)")
            print("To upload manually, run:")
            print("twine upload dist/*")
    else:
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
