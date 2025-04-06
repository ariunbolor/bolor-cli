#!/usr/bin/env python
"""
Main entry point for Bolor CLI.

This module handles command-line arguments and dispatches to the appropriate functionality.
"""

import os
import sys
import warnings
from pathlib import Path
from typing import List, Optional

# Do this at the very top - force command_name to be 'bolor'
if len(sys.argv) > 0:
    sys.argv[0] = "bolor"

# Suppress dependency warnings from requests library
warnings.filterwarnings("ignore", category=Warning)

# Direct import of a standalone typer app to avoid command name issues
from bolor.cli import app, main

if __name__ == "__main__":
    main()
