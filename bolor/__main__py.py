#!/usr/bin/env python
"""
Special main module entry point for Python module execution (python -m bolor).
This redirects to the main CLI entry point while ensuring proper command name display.
"""

import sys
import os
from pathlib import Path

# Modify sys.argv[0] directly for consistent command name
if len(sys.argv) > 0:
    sys.argv[0] = "bolor"

# Import the regular main function
from bolor.__main__ import main

if __name__ == "__main__":
    main()
