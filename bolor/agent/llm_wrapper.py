"""
LLM wrapper module for Bolor code repair.

This module provides a wrapper around the Phi-2 model for text generation
and other LLM-based functionalities.
"""

import os
import logging
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple

from bolor.utils.config import Config
from bolor.agent.dataset_loader import DatasetLoader


class LLMWrapper:
    """
    LLM wrapper class for Phi-2 model.
    
    This class provides methods for interacting with the Phi-2 model
    and generating text completions.
    """
    
    def __init__(self, config: Config):
        """
        Initialize a new LLMWrapper instance.
        
        Args:
            config: Configuration object containing LLM settings.
        """
        self.config = config
        self.verbose = config.get("verbose", False)
        
        # Initialize logger
        self.logger = logging.getLogger("bolor.llm_wrapper")
        if self.verbose:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)
        
        # Initialize model
        self.model = None
        self.model_path = None
        
        # Get model information from config
        self.model_name = config.get("model.name", "phi-2")
        self.model_type = config.get("model.type", "phi")
        self.model_file = config.get("model.file", "phi-2.Q4_K_M.gguf")
        self.max_length = config.get("model.max_length", 512)
        self.temperature = config.get("model.temperature", 0.7)
        self.top_p = config.get("model.top_p", 0.9)
    
    def initialize(self, force_download: bool = False) -> None:
        """
        Initialize the LLM model.
        
        This method ensures the model file is downloaded and loads it into memory.
        It includes robust error handling and fallback to smaller models if needed.
        
        Args:
            force_download: If True, force re-download even if the model exists.
        """
        # Define fallback models in order of preference
        model_options = [
            {"file": "phi-2.Q2_K.gguf", "url": "https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q2_K.gguf"},
            {"file": "phi-2.Q4_K_M.gguf", "url": "https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q4_K_M.gguf"},
            {"file": "phi-2.Q5_K_M.gguf", "url": "https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q5_K_M.gguf"},
        ]
        
        # Model types to try (in order of likelihood)
        model_types = ["llama", "gpt2", "phi", "gptj", "mpt", "falcon", "starcoder"]
        
        # Create a mock model as last resort
        class MockModel:
            def __call__(self, prompt, **kwargs):
                return "Mock response (limited functionality mode)"
                
        try:
            # Import ctransformers
            try:
                from ctransformers import AutoModelForCausalLM
            except ImportError:
                self.logger.error("ctransformers not installed")
                self.model = MockModel()
                return
            
            # Ensure models directory exists
            models_dir = self.config.get_path("models_dir")
            model_dir = models_dir / self.model_name
            model_dir.mkdir(parents=True, exist_ok=True)
            
            # Loop through existing model files
            for option in model_options:
                model_path = model_dir / option["file"]
                
                # Skip if model doesn't exist
                if not model_path.exists():
                    continue
                    
                self.logger.info(f"Trying to load {model_path}")
                
                # Try each model type
                for model_type in model_types:
                    try:
                        self.logger.info(f"Attempting with model_type={model_type}")
                        
                        # Try with CPU-only config first
                        try:
                            model = AutoModelForCausalLM.from_pretrained(
                                str(model_dir),
                                model_file=option["file"],
                                model_type=model_type,
                                gpu_layers=0
                            )
                            
                            # Test if the model works with a simple input
                            test_result = model("Hello", max_new_tokens=5)
                            self.logger.info(f"Model loaded successfully: {test_result}")
                            
                            # Store model and return
                            self.model = model
                            self.model_path = model_path
                            self.model_file = option["file"]
                            self.model_type = model_type
                            return
                            
                        except Exception as e:
                            self.logger.debug(f"CPU mode failed: {str(e)}")
                            
                        # Try with default config
                        model = AutoModelForCausalLM.from_pretrained(
                            str(model_dir),
                            model_file=option["file"],
                            model_type=model_type
                        )
                        
                        # Test if the model works with a simple input
                        test_result = model("Hello", max_new_tokens=5)
                        self.logger.info(f"Model loaded successfully: {test_result}")
                        
                        # Store model and return
                        self.model = model
                        self.model_path = model_path
                        self.model_file = option["file"]
                        self.model_type = model_type
                        return
                        
                    except Exception as e:
                        self.logger.debug(f"Failed with model_type {model_type}: {str(e)}")
                        continue
            
            # If we're here, no existing models worked, use mock model
            self.logger.warning("Failed to load any model - using mock model instead")
            self.model = MockModel()
            
        except Exception as e:
            # Catch any unexpected errors
            self.logger.error(f"Unexpected error in model loading: {str(e)}")
            self.model = MockModel()
    
    def _initialize_with_langchain(self, model_path):
        """Initialize using langchain as a fallback."""
        try:
            from langchain_community.llms import LlamaCpp
        except ImportError:
            self.logger.warning("langchain-community not installed, can't use as fallback.")
            raise ImportError("langchain-community not installed")
        
        # Create the LlamaCpp model
        model = LlamaCpp(
            model_path=str(model_path),
            temperature=0.7,
            max_tokens=512,
            n_ctx=2048,
            verbose=self.verbose,
            n_gpu_layers=0  # CPU only for better compatibility
        )
        
        # Test if it works
        test_input = "Hello, this is a test."
        try:
            test_output = model.invoke(test_input)
            self.logger.info(f"Test output with langchain: '{test_output}'")
        except Exception as e:
            self.logger.error(f"Langchain model test failed: {str(e)}")
            raise
        
        # Create a wrapper for the langchain model
        class LangchainWrapper:
            def __init__(self, llm):
                self.llm = llm
                
            def __call__(self, prompt, **kwargs):
                max_new_tokens = kwargs.get("max_new_tokens", 512)
                temperature = kwargs.get("temperature", 0.7)
                
                # Set model parameters
                self.llm.temperature = temperature
                self.llm.max_tokens = max_new_tokens
                
                # Call the model
                result = self.llm.invoke(prompt)
                return result
        
        # Store model information
        self.model = LangchainWrapper(model)
        self.model_path = model_path
        self.model_file = model_path.name
        self.model_type = "langchain"
        
        # Update config
        self.config.set("model.file", model_path.name)
        self.config.set("model.type", "langchain")
        
        self.logger.info(f"Successfully loaded {model_path.name} with langchain")
    
    def generate(
        self,
        prompt: str,
        max_length: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        repetition_penalty: Optional[float] = None,
        stop: Optional[List[str]] = None
    ) -> str:
        """
        Generate text using the LLM.
        
        Args:
            prompt: Input prompt for the model.
            max_length: Maximum length of the generated text (in tokens).
            temperature: Sampling temperature, lower values make the model more deterministic.
            top_p: Nucleus sampling parameter, filters out low-probability tokens.
            top_k: Top-k sampling parameter, filters to only the top-k tokens.
            repetition_penalty: Penalty for repeating tokens, higher values reduce repetition.
            stop: List of strings that will stop generation if encountered.
            
        Returns:
            Generated text string.
            
        Raises:
            RuntimeError: If the model is not initialized.
        """
        if self.model is None:
            self.initialize()
        
        # Set default values
        max_length = max_length or self.max_length
        temperature = temperature or self.temperature
        top_p = top_p or self.top_p
        
        try:
            # Generate text
            if self.verbose:
                self.logger.debug(f"Generating text with prompt: {prompt[:50]}...")
            
            kwargs = {
                "max_new_tokens": max_length,
                "temperature": temperature,
                "top_p": top_p,
            }
            
            if top_k is not None:
                kwargs["top_k"] = top_k
            
            if repetition_penalty is not None:
                kwargs["repetition_penalty"] = repetition_penalty
            
            if stop is not None:
                kwargs["stop"] = stop
            
            generated_text = self.model(prompt, **kwargs)
            
            if self.verbose:
                self.logger.debug(f"Generated text: {generated_text[:50]}...")
            
            return generated_text
            
        except Exception as e:
            self.logger.error(f"Error generating text: {str(e)}")
            return ""
    
    def generate_code_fix(self, buggy_code: str, error_message: Optional[str] = None) -> str:
        """
        Generate a fix for buggy code.
        
        Args:
            buggy_code: Buggy code to fix.
            error_message: Optional error message to help guide the fix.
            
        Returns:
            Fixed code string.
        """
        # Create a prompt for code fixing
        prompt = self._create_code_fix_prompt(buggy_code, error_message)
        
        # Generate fixed code
        generated_text = self.generate(
            prompt=prompt,
            temperature=0.2,  # Lower temperature for more deterministic output
            stop=["```", "FIXED CODE END"]
        )
        
        # Extract the fixed code from the response
        fixed_code = self._extract_code_from_response(generated_text)
        
        return fixed_code
    
    def generate_code_improvements(self, code: str, improvement_type: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Generate improvement suggestions for code.
        
        Args:
            code: Code to improve.
            improvement_type: Optional type of improvement to focus on (e.g., 'performance', 'security').
            
        Returns:
            List of improvement suggestions with title, description, and example.
        """
        # Create a prompt for code improvement
        prompt = self._create_code_improvement_prompt(code, improvement_type)
        
        # Generate improvement suggestions
        generated_text = self.generate(
            prompt=prompt,
            temperature=0.7,  # Higher temperature for more diverse suggestions
            max_length=1024,  # Allow for longer output
        )
        
        # Parse the suggestions from the response
        suggestions = self._parse_improvement_suggestions(generated_text)
        
        return suggestions
    
    def _create_code_fix_prompt(self, buggy_code: str, error_message: Optional[str] = None) -> str:
        """
        Create a prompt for code fixing.
        
        Args:
            buggy_code: Buggy code to fix.
            error_message: Optional error message to help guide the fix.
            
        Returns:
            Prompt string.
        """
        prompt = "You are an expert software engineer tasked with fixing bugs in code. "
        prompt += "You are given buggy code and need to provide a fixed version.\n\n"
        
        prompt += "BUGGY CODE:\n```\n"
        prompt += buggy_code.strip()
        prompt += "\n```\n\n"
        
        if error_message:
            prompt += "ERROR MESSAGE:\n```\n"
            prompt += error_message.strip()
            prompt += "\n```\n\n"
        
        prompt += "Fix the bug in the code. Do not explain, just provide the corrected code.\n\n"
        prompt += "FIXED CODE:\n```\n"
        
        return prompt
    
    def _extract_code_from_response(self, response: str) -> str:
        """
        Extract code from the model's response.
        
        Args:
            response: Response from the model.
            
        Returns:
            Extracted code string.
        """
        lines = response.strip().split('\n')
        
        # Start collecting code after "FIXED CODE:" if present
        collecting = True
        code_lines = []
        
        for line in lines:
            if '```' in line:
                break
            if 'FIXED CODE END' in line:
                break
            if collecting:
                code_lines.append(line)
        
        return '\n'.join(code_lines)
    
    def _create_code_improvement_prompt(self, code: str, improvement_type: Optional[str] = None) -> str:
        """
        Create a prompt for code improvement suggestions.
        
        Args:
            code: Code to improve.
            improvement_type: Optional type of improvement to focus on.
            
        Returns:
            Prompt string.
        """
        prompt = "You are an expert software engineer tasked with improving code quality. "
        prompt += "You are given code and need to suggest improvements.\n\n"
        
        prompt += "CODE:\n```\n"
        prompt += code.strip()
        prompt += "\n```\n\n"
        
        if improvement_type:
            prompt += f"Focus on {improvement_type} improvements. "
        
        prompt += "Provide specific suggestions for improving the code. "
        prompt += "For each suggestion, include a title, description, and example code.\n\n"
        
        prompt += "Format your response as follows:\n"
        prompt += "SUGGESTION 1: [Title]\nDESCRIPTION: [Description]\nEXAMPLE: [Example code]\n\n"
        prompt += "SUGGESTION 2: [Title]\nDESCRIPTION: [Description]\nEXAMPLE: [Example code]\n\n"
        
        prompt += "SUGGESTIONS:\n"
        
        return prompt
    
    def _parse_improvement_suggestions(self, response: str) -> List[Dict[str, str]]:
        """
        Parse improvement suggestions from the model's response.
        
        Args:
            response: Response from the model.
            
        Returns:
            List of suggestion dictionaries.
        """
        suggestions = []
        current_suggestion = {}
        current_field = None
        
        lines = response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            
            if line.startswith("SUGGESTION ") and ":" in line:
                # Save the previous suggestion if it exists
                if current_suggestion and "title" in current_suggestion:
                    suggestions.append(current_suggestion)
                
                # Start a new suggestion
                current_suggestion = {"title": line.split(":", 1)[1].strip()}
                current_field = None
                
            elif line.startswith("DESCRIPTION:"):
                current_suggestion["description"] = line[len("DESCRIPTION:"):].strip()
                current_field = "description"
                
            elif line.startswith("EXAMPLE:"):
                current_suggestion["example"] = line[len("EXAMPLE:"):].strip()
                current_field = "example"
                
            elif current_field in ["description", "example"] and line:
                # Append to the current field
                current_suggestion[current_field] += "\n" + line
        
        # Add the last suggestion
        if current_suggestion and "title" in current_suggestion:
            suggestions.append(current_suggestion)
        
        return suggestions
    
    def get_embedding(self, text: str) -> List[float]:
        """
        Get a vector embedding for the given text.
        
        Args:
            text: Text to get embedding for.
            
        Returns:
            List of floats representing the embedding.
            
        Raises:
            NotImplementedError: Currently not implemented for Phi-2 with ctransformers.
        """
        # Note: This is not directly supported by ctransformers for phi-2.
        # In a real implementation, you might use a separate embedding model or service.
        raise NotImplementedError("Embeddings are not directly supported with ctransformers. Use langchain or another embedding provider.")
    
    def unload(self) -> None:
        """
        Unload the model from memory.
        """
        if self.model is not None:
            del self.model
            self.model = None
            self.logger.info("Model unloaded from memory")
