#!/usr/bin/env python
"""
Internal module entry point for Bolor CLI.
This is used when running as 'python -m bolor.bolor'.
It ensures the command name is shown correctly.
"""

import sys
import os
import inspect
import typer

# --------- Aggressive monkey patching for Typer command name ---------

# Monkey patch typer's internal functions related to command name
if hasattr(typer, '_main'):
    # Override the function that returns the command name
    original_get_command_name = getattr(typer._main, '_get_command_name', None)
    
    if original_get_command_name:
        def new_get_command_name(*args, **kwargs):
            return "bolor"
        
        typer._main._get_command_name = new_get_command_name

# Also patch any other typer internal utils
if hasattr(typer, '_utils'):
    original_get_command_name = getattr(typer._utils, 'get_command_name', None)
    
    if original_get_command_name:
        def new_get_command_name(*args, **kwargs):
            return "bolor"
        
        typer._utils.get_command_name = new_get_command_name

# Force the command name to be 'bolor' instead of 'python -m bolor.bolor'
if len(sys.argv) > 0:
    # Save original for reference
    os.environ["ORIGINAL_ARGV0"] = sys.argv[0]
    sys.argv[0] = "bolor"

# Import directly from cli module to avoid circular issues
from bolor.cli import main

if __name__ == "__main__":
    # Run main with our patched environment
    main()
