#!/usr/bin/env python3
"""
This script patches the requests library to silence the annoying urllib3 warnings.
"""

import os
import sys
import site

def find_requests_init():
    """Find the requests __init__.py file."""
    # Check common locations
    potential_locations = []
    
    # User site-packages
    user_site = site.getusersitepackages()
    potential_locations.append(os.path.join(user_site, 'requests', '__init__.py'))
    
    # System site-packages
    for site_path in site.getsitepackages():
        potential_locations.append(os.path.join(site_path, 'requests', '__init__.py'))
    
    # Check if any location exists
    for location in potential_locations:
        if os.path.exists(location):
            return location
    
    return None

def patch_file(file_path):
    """Patch the requests __init__.py file to remove the warning."""
    if not file_path:
        print("Could not find requests/__init__.py")
        return False
    
    print(f"Found requests/__init__.py at: {file_path}")
    
    # Read the content
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if the warning line exists
    warning_line = 'warnings.warn(f"urllib3 ({urllib3.__version__}) or chardet ({charset_normalizer.__version__})/charset_normalizer ({charset_normalizer.__version__}) doesn\'t match a supported version!",'
    if warning_line not in content:
        print("Warning line not found. The pattern may have changed.")
        return False
    
    # Create a backup
    backup_path = file_path + '.bak'
    with open(backup_path, 'w') as f:
        f.write(content)
    print(f"Created backup at: {backup_path}")
    
    # Replace the warning with a pass
    modified_content = content.replace(
        'warnings.warn(f"urllib3 ({urllib3.__version__}) or chardet ({charset_normalizer.__version__})/charset_normalizer ({charset_normalizer.__version__}) doesn\'t match a supported version!",',
        '# Patched by Bolor to remove annoying warning\n            pass # '
    )
    
    # Write the modified content
    with open(file_path, 'w') as f:
        f.write(modified_content)
    
    print("Successfully patched requests/__init__.py to remove the warning")
    return True

def main():
    """Main function."""
    print("Patching requests library to silence urllib3 warnings...")
    
    # Find the requests __init__.py file
    requests_init = find_requests_init()
    
    # Patch the file
    if patch_file(requests_init):
        print("\nThe annoying urllib3 warning has been permanently silenced!")
        print("You should no longer see it when running bolor.")
    else:
        print("\nFailed to patch requests library.")
        print("As an alternative, you can run bolor with:")
        print("PYTHONWARNINGS=ignore bolor [commands]")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
