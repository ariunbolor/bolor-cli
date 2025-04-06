"""
Symbol map module for Bolor.

This module builds a map of symbols (classes, functions, methods, etc.) in Python code,
which helps with understanding code structure and relationships.
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple


def build_symbol_map(code_dir: str or Path) -> Dict[str, List[Dict[str, Any]]]:
    """
    Build a map of symbols (classes, functions, methods, etc.) in Python code.
    
    Args:
        code_dir: Directory containing Python code files
        
    Returns:
        Dictionary mapping file paths to lists of symbol information:
        {
            'file.py': [
                {'type': 'class', 'name': 'MyClass', 'line': 10, 'docstring': '...'},
                {'type': 'function', 'name': 'my_func', 'line': 30, 'docstring': '...'},
                ...
            ],
            ...
        }
    """
    code_dir = Path(code_dir)
    if not code_dir.exists():
        raise FileNotFoundError(f"Directory not found: {code_dir}")
    
    symbol_map = {}
    
    # Get all Python files in the directory (non-recursive)
    py_files = list(code_dir.glob("*.py"))
    
    for py_file in py_files:
        try:
            with open(py_file, "r") as f:
                source = f.read()
            
            # Parse the AST
            tree = ast.parse(source)
            
            # Extract symbols from the AST
            symbols = _extract_symbols_from_ast(tree)
            
            # Add to the map
            symbol_map[str(py_file.relative_to(code_dir))] = symbols
        except Exception as e:
            print(f"Error parsing {py_file}: {e}")
    
    return symbol_map


def build_symbol_map_recursive(code_dir: str or Path) -> Dict[str, List[Dict[str, Any]]]:
    """
    Build a map of symbols recursively through all subdirectories.
    
    Args:
        code_dir: Directory containing Python code files
        
    Returns:
        Dictionary mapping file paths to lists of symbol information
    """
    code_dir = Path(code_dir)
    if not code_dir.exists():
        raise FileNotFoundError(f"Directory not found: {code_dir}")
    
    symbol_map = {}
    
    # Walk through all subdirectories
    for root, _, files in os.walk(code_dir):
        root_path = Path(root)
        
        # Process Python files in this directory
        for file in files:
            if file.endswith(".py"):
                file_path = root_path / file
                try:
                    with open(file_path, "r") as f:
                        source = f.read()
                    
                    # Parse the AST
                    tree = ast.parse(source)
                    
                    # Extract symbols from the AST
                    symbols = _extract_symbols_from_ast(tree)
                    
                    # Add to the map with relative path
                    rel_path = file_path.relative_to(code_dir)
                    symbol_map[str(rel_path)] = symbols
                except Exception as e:
                    print(f"Error parsing {file_path}: {e}")
    
    return symbol_map


def _extract_symbols_from_ast(tree: ast.AST) -> List[Dict[str, Any]]:
    """
    Extract symbols from an AST.
    
    Args:
        tree: AST to extract symbols from
        
    Returns:
        List of symbol information dictionaries
    """
    symbols = []
    
    for node in ast.iter_child_nodes(tree):
        # Classes
        if isinstance(node, ast.ClassDef):
            class_info = {
                'type': 'class',
                'name': node.name,
                'line': node.lineno,
                'docstring': ast.get_docstring(node),
                'methods': []
            }
            
            # Extract methods from the class
            for method in [n for n in node.body if isinstance(n, ast.FunctionDef)]:
                method_info = {
                    'type': 'method',
                    'name': method.name,
                    'line': method.lineno,
                    'docstring': ast.get_docstring(method),
                    'args': _extract_function_args(method)
                }
                class_info['methods'].append(method_info)
            
            symbols.append(class_info)
        
        # Functions
        elif isinstance(node, ast.FunctionDef):
            func_info = {
                'type': 'function',
                'name': node.name,
                'line': node.lineno,
                'docstring': ast.get_docstring(node),
                'args': _extract_function_args(node)
            }
            symbols.append(func_info)
        
        # Global variables (constants, etc.)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    var_info = {
                        'type': 'variable',
                        'name': target.id,
                        'line': node.lineno,
                        'value': _extract_value(node.value)
                    }
                    symbols.append(var_info)
    
    return symbols


def _extract_function_args(node: ast.FunctionDef) -> List[Dict[str, str]]:
    """
    Extract function arguments.
    
    Args:
        node: Function definition node
        
    Returns:
        List of argument information dictionaries
    """
    args = []
    
    for arg in node.args.args:
        arg_info = {
            'name': arg.arg,
            'annotation': _get_annotation_name(arg.annotation)
        }
        args.append(arg_info)
    
    return args


def _get_annotation_name(annotation) -> Optional[str]:
    """
    Get the name of a type annotation.
    
    Args:
        annotation: AST node representing a type annotation
        
    Returns:
        String representation of the annotation, or None if no annotation
    """
    if annotation is None:
        return None
    
    if isinstance(annotation, ast.Name):
        return annotation.id
    elif isinstance(annotation, ast.Subscript):
        # Handle generics like List[int]
        if isinstance(annotation.value, ast.Name):
            return f"{annotation.value.id}[...]"
    
    return "complex_type"


def _extract_value(value_node) -> Optional[str]:
    """
    Extract a simple representation of a value from an AST node.
    
    Args:
        value_node: AST node representing a value
        
    Returns:
        String representation of the value, or None if complex
    """
    if isinstance(value_node, ast.Constant):
        return repr(value_node.value)
    elif isinstance(value_node, ast.Str):
        return repr(value_node.s)
    elif isinstance(value_node, ast.Num):
        return repr(value_node.n)
    elif isinstance(value_node, ast.List):
        return "[...]"
    elif isinstance(value_node, ast.Dict):
        return "{...}"
    elif isinstance(value_node, ast.Name):
        return value_node.id
    
    return "complex_value"


def find_symbol_references(code_dir: str or Path, symbol_name: str) -> List[Tuple[str, int]]:
    """
    Find all references to a symbol in the codebase.
    
    Args:
        code_dir: Directory containing Python code files
        symbol_name: Name of the symbol to find references to
        
    Returns:
        List of (file_path, line_number) tuples
    """
    code_dir = Path(code_dir)
    references = []
    
    class SymbolVisitor(ast.NodeVisitor):
        def __init__(self, symbol_name):
            self.symbol_name = symbol_name
            self.references = []
        
        def visit_Name(self, node):
            if node.id == self.symbol_name:
                self.references.append(node.lineno)
            self.generic_visit(node)
    
    # Walk through all Python files in the directory
    for root, _, files in os.walk(code_dir):
        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file
                try:
                    with open(file_path, "r") as f:
                        source = f.read()
                    
                    tree = ast.parse(source)
                    visitor = SymbolVisitor(symbol_name)
                    visitor.visit(tree)
                    
                    if visitor.references:
                        rel_path = file_path.relative_to(code_dir)
                        for line in visitor.references:
                            references.append((str(rel_path), line))
                except Exception as e:
                    print(f"Error parsing {file_path}: {e}")
    
    return references
