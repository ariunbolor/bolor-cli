"""
Runtime validator module for Bolor.

This module validates Python code by executing it in a subprocess
and capturing any errors that occur during execution.
"""

import tempfile
import subprocess
import os
import sys
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List


def validate_code(code: str) -> Tuple[bool, Optional[str]]:
    """
    Validate Python code by running it in a subprocess.
    
    Args:
        code: Python code to validate
        
    Returns:
        Tuple of (success, error_message)
    """
    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as temp:
        temp_path = temp.name
        temp.write(code.encode('utf-8'))
    
    try:
        # Run the code in a subprocess
        result = subprocess.run(
            [sys.executable, temp_path],
            capture_output=True,
            text=True,
            timeout=5  # Timeout after 5 seconds to prevent hanging
        )
        
        if result.returncode == 0:
            return True, None
        else:
            return False, result.stderr
    except subprocess.TimeoutExpired:
        return False, "Code execution timed out after 5 seconds"
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def validate_file(file_path: str or Path) -> Tuple[bool, Optional[str]]:
    """
    Validate a Python file by running it in a subprocess.
    
    Args:
        file_path: Path to the Python file to validate
        
    Returns:
        Tuple of (success, error_message)
    """
    file_path = Path(file_path)
    if not file_path.exists():
        return False, f"File not found: {file_path}"
    
    try:
        # Run the file in a subprocess
        result = subprocess.run(
            [sys.executable, str(file_path)],
            capture_output=True,
            text=True,
            timeout=5  # Timeout after 5 seconds to prevent hanging
        )
        
        if result.returncode == 0:
            return True, None
        else:
            return False, result.stderr
    except subprocess.TimeoutExpired:
        return False, "Code execution timed out after 5 seconds"


def parse_traceback(error_message: str) -> Dict[str, Any]:
    """
    Parse a Python traceback to extract useful information.
    
    Args:
        error_message: Error message from Python execution
        
    Returns:
        Dictionary with parsed information:
        {
            'error_type': 'NameError',
            'error_message': 'name 'x' is not defined',
            'file': 'example.py',
            'line': 10,
            'code': 'print(x)'
        }
    """
    if not error_message:
        return {'error_type': 'Unknown', 'error_message': 'No error message provided'}
    
    lines = error_message.strip().split('\n')
    result = {
        'error_type': 'Unknown',
        'error_message': '',
        'file': '',
        'line': 0,
        'code': ''
    }
    
    # Extract error type and message (usually the last line)
    if lines:
        last_line = lines[-1]
        if ':' in last_line:
            error_parts = last_line.split(':', 1)
            result['error_type'] = error_parts[0].strip()
            result['error_message'] = error_parts[1].strip() if len(error_parts) > 1 else ''
    
    # Look for file and line information
    for line in lines:
        if 'File "' in line and '", line ' in line:
            parts = line.split('File "', 1)[1]
            file_line_parts = parts.split('", line ', 1)
            if len(file_line_parts) == 2:
                result['file'] = file_line_parts[0]
                
                # Extract line number
                line_parts = file_line_parts[1].split(',', 1)
                try:
                    result['line'] = int(line_parts[0])
                except ValueError:
                    pass
                
                # Try to extract the code from the next line if it exists
                if lines.index(line) + 1 < len(lines):
                    code_line = lines[lines.index(line) + 1]
                    result['code'] = code_line.strip()
    
    return result


def fix_code_with_error(code: str, error_info: Dict[str, Any]) -> str:
    """
    Generate a fix for code based on error information.
    
    Args:
        code: Original code
        error_info: Error information from parse_traceback
        
    Returns:
        Code with attempted fix
    """
    lines = code.split('\n')
    
    if error_info['line'] <= 0 or error_info['line'] > len(lines):
        return code  # Can't fix if line number is invalid
    
    line_index = error_info['line'] - 1
    error_line = lines[line_index]
    fixed_line = error_line
    
    # Apply fixes based on error type
    if error_info['error_type'] == 'NameError' and "is not defined" in error_info['error_message']:
        # Try to extract the undefined variable name
        import re
        match = re.search(r"'([^']+)'", error_info['error_message'])
        if match:
            var_name = match.group(1)
            # Simple fix: define the variable as None
            fixed_line = f"{var_name} = None  # TODO: Define this variable properly\n{error_line}"
            lines[line_index] = fixed_line
    
    elif error_info['error_type'] == 'IndexError' and "list index out of range" in error_info['error_message']:
        # Try to add a bounds check
        # This is a simplistic approach - a real implementation would be more sophisticated
        fixed_line = f"# TODO: Add bounds check for the list index\n{error_line}"
        lines[line_index] = fixed_line
    
    elif error_info['error_type'] == 'ModuleNotFoundError':
        # Suggest installing the missing module
        match = re.search(r"No module named '([^']+)'", error_info['error_message'])
        if match:
            module_name = match.group(1)
            comment = f"# TODO: Install the missing module: pip install {module_name}\n"
            lines.insert(line_index, comment)
    
    # Return the fixed code
    return '\n'.join(lines)
