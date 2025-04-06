"""
Generator module for Bolor code creation.

This module provides functionality for generating code from natural language prompts.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple

from bolor.utils.config import Config
from bolor.agent.llm_wrapper import LLMWrapper


class Generator:
    """
    Generator class for creating code from natural language prompts.
    
    This class is responsible for taking natural language descriptions and
    generating appropriate code using the LLM.
    """
    
    def __init__(self, config: Config):
        """
        Initialize a new Generator instance.
        
        Args:
            config: Configuration object containing generator settings.
        """
        self.config = config
        self.verbose = config.get("verbose", False)
        
        # Initialize logger
        self.logger = logging.getLogger("bolor.generator")
        if self.verbose:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)
        
        # Initialize LLM wrapper
        self.llm = LLMWrapper(config)
    
    def generate_from_prompt(self, prompt: str, language: Optional[str] = None, 
                             add_comments: bool = True) -> str:
        """
        Generate code from a natural language prompt.
        
        Args:
            prompt: Natural language description of what to generate.
            language: Optional programming language to generate in (auto-detected if None).
            add_comments: Whether to add explanatory comments to the generated code.
            
        Returns:
            The generated code as a string.
        """
        # Try to infer language from prompt if not provided
        if not language:
            language = self._infer_language(prompt)
            self.logger.info(f"Inferred language: {language}")
        
        # Create the prompt for code generation
        generation_prompt = self._create_generation_prompt(prompt, language, add_comments)
        
        # Generate code
        try:
            self.logger.info(f"Generating code for: {prompt}")
            
            # We can use a longer max_length for generation
            generated_text = self.llm.generate(
                prompt=generation_prompt,
                max_length=1024,  # Allow longer output for complete code generation
                temperature=0.3,  # Lower temperature for more deterministic output
                stop=["```", "END OF CODE", "# End of implementation"]
            )
            
            # Extract the code from the response
            generated_code = self._extract_code_from_response(generated_text)
            
            return generated_code
            
        except Exception as e:
            self.logger.error(f"Error generating code: {str(e)}")
            raise
    
    def generate_file(self, prompt: str, file_path: Union[str, Path]) -> Path:
        """
        Generate code from a prompt and save it to a file.
        
        Args:
            prompt: Natural language description of what to generate.
            file_path: Path to save the generated code to.
            
        Returns:
            Path object pointing to the created file.
        """
        # Convert to Path object
        file_path = Path(file_path)
        
        # Try to infer language from file extension
        extension = file_path.suffix.lower()
        language = self._get_language_from_extension(extension)
        
        # Generate code
        generated_code = self.generate_from_prompt(prompt, language)
        
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to file
        with open(file_path, 'w') as f:
            f.write(generated_code)
        
        return file_path
    
    def _infer_language(self, prompt: str) -> str:
        """
        Infer the programming language from the prompt.
        
        Args:
            prompt: Natural language description.
            
        Returns:
            Inferred programming language.
        """
        # Simple keyword matching for common languages
        prompt_lower = prompt.lower()
        
        # Check for explicit language mentions
        if "python" in prompt_lower or "py" in prompt_lower:
            return "python"
        elif "javascript" in prompt_lower or "js" in prompt_lower:
            return "javascript"
        elif "typescript" in prompt_lower or "ts" in prompt_lower:
            return "typescript"
        elif "java" in prompt_lower:
            return "java"
        elif "c++" in prompt_lower or "cpp" in prompt_lower:
            return "cpp"
        elif "c#" in prompt_lower or "csharp" in prompt_lower:
            return "csharp"
        elif "ruby" in prompt_lower:
            return "ruby"
        elif "php" in prompt_lower:
            return "php"
        elif "go" in prompt_lower or "golang" in prompt_lower:
            return "go"
        elif "rust" in prompt_lower:
            return "rust"
        elif "swift" in prompt_lower:
            return "swift"
        elif "shell" in prompt_lower or "bash" in prompt_lower:
            return "bash"
        elif "sql" in prompt_lower:
            return "sql"
        elif "yaml" in prompt_lower or "yml" in prompt_lower:
            return "yaml"
        elif "json" in prompt_lower:
            return "json"
        elif "github action" in prompt_lower or "workflow" in prompt_lower or "ci/cd" in prompt_lower:
            return "yaml"
        elif "docker" in prompt_lower or "dockerfile" in prompt_lower:
            return "dockerfile"
        
        # Default to python if no match
        return "python"
    
    def _get_language_from_extension(self, extension: str) -> Optional[str]:
        """
        Get language name from file extension.
        
        Args:
            extension: File extension (e.g., ".py").
            
        Returns:
            Language name or None if not recognized.
        """
        extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".cpp": "cpp", ".cc": "cpp", ".h": "cpp", ".hpp": "cpp",
            ".cs": "csharp",
            ".rb": "ruby",
            ".php": "php",
            ".go": "go",
            ".rs": "rust",
            ".swift": "swift",
            ".sh": "bash", ".bash": "bash",
            ".sql": "sql",
            ".yml": "yaml", ".yaml": "yaml",
            ".json": "json",
            ".md": "markdown",
            ".html": "html",
            ".css": "css",
            ".dockerfile": "dockerfile", ".Dockerfile": "dockerfile"
        }
        
        return extension_map.get(extension, None)
    
    def _create_generation_prompt(self, prompt: str, language: str, add_comments: bool) -> str:
        """
        Create a prompt for code generation.
        
        Args:
            prompt: Natural language description.
            language: Programming language to generate in.
            add_comments: Whether to add explanatory comments.
            
        Returns:
            Formatted prompt string.
        """
        generation_prompt = f"""You are a skilled software engineer. Create code based on the following description.

TASK DESCRIPTION:
{prompt.strip()}

PROGRAMMING LANGUAGE:
{language}

REQUIREMENTS:
1. Write efficient, high-quality, production-ready code
2. Follow best practices and design patterns for {language}
3. Include proper error handling
4. {"Add explanatory comments" if add_comments else "Minimize comments"}
5. Use modern, up-to-date syntax and libraries
6. Make the code modular and reusable where appropriate

Your response should only include the code, without any explanation outside of the code comments.
Begin with any necessary imports/includes, then implement the solution.

CODE:
```{language}
"""
        
        return generation_prompt
    
    def _extract_code_from_response(self, response: str) -> str:
        """
        Extract code from the model's response.
        
        Args:
            response: Response from the model.
            
        Returns:
            Extracted code string.
        """
        # First check if this might be a mock response from the mock model
        if "mock" in response.lower() and "fallback" in response.lower():
            # This is likely from the mock model - generate a stub response
            return "# The model is currently running in fallback mode due to loading issues.\n# This is a placeholder response.\n\n# Please fix the model loading issues to get actual code generation."
        
        # Start collecting from the first line of the response
        # This works because our prompt ends with ```{language}
        # so the model's response should start with the code
        
        # Filter out any markdown code block syntax if present
        lines = []
        
        # Flag to indicate if we've found a potential ending
        ended = False
        
        for line in response.strip().split('\n'):
            # Skip the end of a code block or special tokens
            if '```' in line or "END OF CODE" in line or "# End of implementation" in line:
                ended = True
                continue
                
            # If we already ended, and now see non-empty content, this might
            # be explanation text or the start of a new section we don't want
            if ended and line.strip():
                break
                
            if not ended:
                lines.append(line)
        
        # If we got no code, return a stub response
        if not lines or (len(lines) == 1 and not lines[0].strip()):
            return "# Could not generate code. Please check your prompt and try again."
        
        return '\n'.join(lines)
