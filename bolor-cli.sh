#!/bin/bash

# Robust shell wrapper for Bolor CLI
# This ensures the command name is always displayed as 'bolor'

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Set environment variable to override command name
export BOLOR_CLI_COMMAND_NAME="bolor"

# Execute the Python module directly, forwarding all arguments
exec python3 -m bolor.cli "$@"
