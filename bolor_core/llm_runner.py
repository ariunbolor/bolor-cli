"""
LLM runner module for Bolor.

This module handles loading and running local GGUF models 
for code understanding, explanation, and optimization.
"""

def create_code_prompt(code: str, instruction: str) -> str:
    """
    Create a prompt for code-related tasks with proper formatting.
    
    Args:
        code: The source code to analyze
        instruction: What the LLM should do with the code
        
    Returns:
        A formatted prompt string
    """
    return f"""
# INSTRUCTION
{instruction}

# CODE
```python
{code}
```

# RESPONSE
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple, List, Any, Union
from llama_cpp import Llama

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default configuration values
DEFAULT_MODEL = "phi-2"
DEFAULT_CONTEXT_SIZE = 2048
DEFAULT_MAX_TOKENS = 512
DEFAULT_TEMPERATURE = 0.2
DEFAULT_TOP_P = 0.9
DEFAULT_THREADS = 4

CONFIG_PATH = Path.home() / ".bolor" / "config" / "config.json"
MODELS_DIR = Path.home() / ".bolor" / "models"


def get_config() -> Dict[str, Any]:
    """Load configuration from the config file, falling back to defaults."""
    if not CONFIG_PATH.exists():
        logger.info(f"No config file found at {CONFIG_PATH}. Using defaults.")
        return {
            "model": {"name": DEFAULT_MODEL},
            "mode": "fast",
            "parameters": {
                "context_size": DEFAULT_CONTEXT_SIZE,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "temperature": DEFAULT_TEMPERATURE,
                "top_p": DEFAULT_TOP_P,
                "threads": DEFAULT_THREADS
            }
        }
    
    try:
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
            return config
    except json.JSONDecodeError:
        logger.error(f"Error parsing config file at {CONFIG_PATH}. Using defaults.")
        return {
            "model": {"name": DEFAULT_MODEL},
            "mode": "fast"
        }


def get_default_llm() -> "LocalLLM":
    """Get a LocalLLM instance with the default configuration."""
    config = get_config()
    model_name = config.get("model", {}).get("name", DEFAULT_MODEL)
    mode = config.get("mode", "fast")
    
    # Set parameters based on the mode
    if mode == "accurate":
        max_tokens = 1024
        temperature = 0.3
    else:  # fast mode
        max_tokens = 512
        temperature = 0.2
    
    # Override with specific parameters if provided
    params = config.get("parameters", {})
    max_tokens = params.get("max_tokens", max_tokens)
    temperature = params.get("temperature", temperature)
    context_size = params.get("context_size", DEFAULT_CONTEXT_SIZE)
    threads = params.get("threads", DEFAULT_THREADS)
    
    model_path = MODELS_DIR / f"{model_name}.gguf"
    
    return LocalLLM(
        model_path=model_path,
        max_tokens=max_tokens,
        temperature=temperature,
        context_size=context_size,
        threads=threads
    )


class LocalLLM:
    """Class for local GGUF model inference using llama-cpp-python."""
    
    def __init__(
        self, 
        model_path: Path, 
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        context_size: int = DEFAULT_CONTEXT_SIZE,
        threads: int = DEFAULT_THREADS
    ):
        """Initialize the LLM with the given model and parameters."""
        self.model_path = model_path
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.context_size = context_size
        self.threads = threads
        self.llm = None
        self._load_model()
    
    def _load_model(self):
        """Load the model from disk."""
        if not self.model_path.exists():
            logger.error(f"Model file not found: {self.model_path}")
            self._use_mock_implementation()
            return
        
        # Check if this is a mock model (less than 100KB)
        if self.model_path.stat().st_size < 100 * 1024:  # Less than 100KB
            logger.warning(f"Mock model detected at {self.model_path}. Using mock implementation.")
            self._use_mock_implementation()
            return
        
        try:
            logger.info(f"🚀 Loading model from {self.model_path}...")
            self.llm = Llama(
                model_path=str(self.model_path),
                n_ctx=self.context_size,
                n_threads=self.threads,
                use_mlock=False
            )
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self._use_mock_implementation()
    
    def _use_mock_implementation(self):
        """Use a mock implementation when the model can't be loaded."""
        logger.warning("Falling back to mock implementation")
        self.llm = None
    
    def ask(
        self, 
        prompt: str, 
        temperature: Optional[float] = None, 
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None
    ) -> str:
        """Run inference on the model with the given prompt."""
        if self.llm is None:
            logger.warning("Using mock LLM implementation!")
            return "I'm unable to provide a specific response without the LLM model loaded."
        
        logger.info("🧠 Running inference...")
        result = self.llm(
            prompt,
            max_tokens=max_tokens or self.max_tokens,
            temperature=temperature or self.temperature,
            stop=stop or ["\n\n", "\n#", "\n```"],
            echo=False
        )
        return result["choices"][0]["text"].strip()
    
    def analyze_code(self, code: str) -> List[Tuple[int, str, str]]:
        """Analyze code and return suggestions as (line, issue, fix) tuples."""
        if self.llm is None:
            logger.warning("Using mock LLM implementation!")
            # Mock some basic issues
            issues = []
            lines = code.split('\n')
            for i, line in enumerate(lines):
                if "def " in line and ":" in line and i + 1 < len(lines) and not lines[i + 1].strip().startswith('"""'):
                    issues.append((i + 1, "Missing docstring in function", 
                                  "This code is attempting to process data but has potential issues."))
                
                if "_temp_value" in line:
                    issues.append((i + 1, "'_temp_value' might be undefined", 
                                  "I'm unable to provide a specific response without the LLM model loaded."))
            return issues
        
        prompt = f"""
        Analyze the following Python code and find issues or improvements:
        
        ```python
        {code}
        ```
        
        For each issue, provide:
        1. The line number
        2. A description of the issue
        3. A suggested fix
        
        Format your response as:
        Line: <number>
        Issue: <description>
        Fix: <suggestion>
        """
        
        result = self.ask(prompt, temperature=0.1)
        
        suggestions = []
        current_line = None
        current_issue = None
        current_fix = None
        
        for line in result.split('\n'):
            line = line.strip()
            if line.startswith("Line:"):
                if current_line is not None and current_issue is not None:
                    suggestions.append((current_line, current_issue, current_fix or "No specific fix provided"))
                
                try:
                    current_line = int(line[5:].strip())
                    current_issue = None
                    current_fix = None
                except ValueError:
                    continue
            
            elif line.startswith("Issue:"):
                current_issue = line[6:].strip()
            
            elif line.startswith("Fix:"):
                current_fix = line[4:].strip()
        
        if current_line is not None and current_issue is not None:
            suggestions.append((current_line, current_issue, current_fix or "No specific fix provided"))
        
        return suggestions

    def explain_code(self, code: str) -> str:
        """Explain what the code does in plain English."""
        if self.llm is None:
            logger.warning("Using mock LLM implementation!")
            return "I'm unable to provide a detailed explanation without the LLM model loaded. This code appears to define some functions and contains potential issues like missing docstrings and undefined variables."
        
        prompt = f"""
        Explain the following Python code in plain English for a developer:
        
        ```python
        {code}
        ```
        
        Your explanation should:
        1. Describe the overall purpose
        2. Explain the key functions and their relationships
        3. Highlight any potential issues or inefficiencies
        """
        
        return self.ask(prompt, temperature=0.3, max_tokens=1024)
    
    def optimize_code(self, code: str) -> Tuple[str, str]:
        """Optimize the given code and return an explanation and the optimized code."""
        if self.llm is None:
            logger.warning("Using mock LLM implementation!")
            return (
                "I'm unable to optimize the code without the LLM model loaded.",
                code
            )
        
        prompt = f"""
        Optimize the following Python code:
        
        ```python
        {code}
        ```
        
        Provide:
        1. An explanation of your optimizations
        2. The optimized code
        
        Format your response as:
        
        ## Explanation
        <your explanation here>
        
        ## Optimized Code
        ```python
        <optimized code here>
        ```
        """
        
        result = self.ask(prompt, temperature=0.2, max_tokens=1536)
        
        parts = result.split("## Optimized Code")
        if len(parts) != 2:
            return ("Could not parse optimization result properly.", code)
        
        explanation = parts[0].replace("## Explanation", "").strip()
        
        optimized_code = parts[1].strip()
        if optimized_code.startswith("```python"):
            optimized_code = optimized_code[len("```python"):].strip()
        if optimized_code.endswith("```"):
            optimized_code = optimized_code[:-3].strip()
        
        return (explanation, optimized_code)
