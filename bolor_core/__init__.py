"""
The bolor_core module provides functionality for code analysis, 
repair, and optimization using local GGUF models.
"""

__version__ = "0.1.0"

# Import core modules for easier access
from bolor_core.code_checker import analyze_file_and_suggest_fixes, explain_file, optimize_file
from bolor_core.git_utils import apply_patch
from bolor_core.llm_runner import get_default_llm, LocalLLM, create_code_prompt
from bolor_core.gguf_downloader import ensure_models
from bolor_core.symbol_map import build_symbol_map, build_symbol_map_recursive, find_symbol_references
from bolor_core.validator import validate_code, validate_file, parse_traceback, fix_code_with_error
