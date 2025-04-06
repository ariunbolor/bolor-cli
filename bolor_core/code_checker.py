"""
Code checker module - Analyze Python files and suggest improvements using LLM
"""

import ast
import inspect
import logging
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

from bolor_core.llm_runner import LocalLLM, create_code_prompt, get_default_llm

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CodeAnalyzer:
    """Analyzes Python code using AST and LLM for suggestions."""
    
    def __init__(self, llm: Optional[LocalLLM] = None):
        """
        Initialize the code analyzer.
        
        Args:
            llm: LocalLLM instance or None to use default
        """
        self.llm = llm or get_default_llm()
    
    def analyze_node(self, node: ast.AST, code: str, full_source: str) -> Optional[Tuple[int, str, str]]:
        """
        Analyze a specific AST node for issues.
        
        Args:
            node: AST node to analyze
            code: Source code snippet of this node
            full_source: Full source code of the file
            
        Returns:
            Tuple of (line_number, message, fix) or None if no issues
        """
        issue = None
        
        # Check for missing docstrings in function definitions
        if isinstance(node, ast.FunctionDef):
            if not ast.get_docstring(node):
                prompt = create_code_prompt(
                    code, 
                    f"This function '{node.name}' is missing a docstring. Generate a clear, descriptive docstring for it."
                )
                suggested_fix = self.llm.ask(prompt)
                
                # Format the fix as a proper docstring
                if not suggested_fix.startswith('"""') and not suggested_fix.startswith("'''"):
                    suggested_fix = f'"""{suggested_fix}"""'
                
                return (node.lineno, f"Missing docstring in function '{node.name}'", suggested_fix)
        
        # Check for potentially undefined variables
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            # This is a very simple check and will have false positives
            # A more robust implementation would use static analysis
            if node.id.startswith('_') and not node.id.startswith('__'):
                prompt = create_code_prompt(
                    code,
                    f"The variable '{node.id}' might be undefined or incorrectly named. Suggest a fix."
                )
                suggested_fix = self.llm.ask(prompt)
                return (node.lineno, f"'{node.id}' might be undefined", suggested_fix)
        
        # Check for complex expressions that could be simplified
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.BinOp):
            if isinstance(node.value.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)) and \
               len(code.strip().split('\n')) >= 3:  # Only check complex expressions
                prompt = create_code_prompt(
                    code,
                    "This expression is complex. Suggest a clearer or more efficient way to write it."
                )
                suggested_fix = self.llm.ask(prompt)
                return (node.lineno, "Complex expression could be simplified", suggested_fix)
                
        return issue
    
    def explain_code(self, code: str) -> str:
        """
        Generate an explanation for the given code.
        
        Args:
            code: Source code to explain
            
        Returns:
            Human-readable explanation of the code
        """
        prompt = create_code_prompt(
            code,
            "Explain this code in clear, simple terms. What does it do? How does it work?"
        )
        return self.llm.ask(prompt, max_tokens=1024)
    
    def optimize_code(self, code: str) -> Tuple[str, str]:
        """
        Suggest optimizations for the given code.
        
        Args:
            code: Source code to optimize
            
        Returns:
            Tuple of (explanation, optimized_code)
        """
        prompt = create_code_prompt(
            code,
            "Optimize this code for better performance or readability. Explain your changes."
        )
        response = self.llm.ask(prompt, max_tokens=1024)
        
        # Try to split the response into explanation and code
        # This is a simple approach - a more robust solution would parse the response more carefully
        parts = response.split("```")
        if len(parts) >= 3 and "python" in parts[1].lower():
            # Found code block
            explanation = parts[0].strip()
            optimized_code = parts[1].replace("python", "", 1).strip()
            return explanation, optimized_code
        
        # Fallback if no code block is found
        return response, code

def analyze_file_and_suggest_fixes(file_path: Path) -> List[Tuple[int, str, str]]:
    """
    Analyze Python file and suggest improvements using AST and LLM.
    
    Args:
        file_path: Path to the Python file to analyze
        
    Returns:
        A list of tuples: (line_number, issue_description, suggested_fix)
    """
    with open(file_path, "r") as f:
        source = f.read()
    
    analyzer = CodeAnalyzer()
    tree = ast.parse(source)
    suggestions = []
    
    # Get the line mapping for better source code extraction
    line_mapping = {}
    lines = source.splitlines(True)
    line_starts = [0]
    pos = 0
    for line in lines:
        pos += len(line)
        line_starts.append(pos)
    
    # Helper to extract source lines for a node
    def get_node_source(node):
        start = getattr(node, 'lineno', None)
        end = getattr(node, 'end_lineno', start)
        if start is not None and end is not None:
            # Get source lines for the node
            return ''.join(lines[start-1:end])
        return ""
    
    # Walk the AST and check each node
    for node in ast.walk(tree):
        # Skip the module node itself
        if isinstance(node, ast.Module):
            continue
            
        # Get source code for this node
        node_source = get_node_source(node)
        
        # Try to analyze it
        if hasattr(node, 'lineno'):
            issue = analyzer.analyze_node(node, node_source, source)
            if issue:
                suggestions.append(issue)
    
    return suggestions

def explain_file(file_path: Path) -> str:
    """
    Generate an explanation for a Python file.
    
    Args:
        file_path: Path to the Python file to explain
        
    Returns:
        Human-readable explanation of the code
    """
    with open(file_path, "r") as f:
        source = f.read()
    
    analyzer = CodeAnalyzer()
    return analyzer.explain_code(source)

def optimize_file(file_path: Path) -> Tuple[str, str]:
    """
    Suggest optimizations for a Python file.
    
    Args:
        file_path: Path to the Python file to optimize
        
    Returns:
        Tuple of (explanation, optimized_code)
    """
    with open(file_path, "r") as f:
        source = f.read()
    
    analyzer = CodeAnalyzer()
    return analyzer.optimize_code(source)
