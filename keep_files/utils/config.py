"""
Configuration system for Bolor.

This module provides a central configuration system for the Bolor tool,
allowing different components to share settings and parameters.
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional, Union


class Config:
    """
    Configuration class for Bolor.
    
    This class manages configuration settings and parameters used across
    the Bolor system. It provides methods for setting, getting, and
    persisting configuration values.
    """
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """
        Initialize a new Config instance.
        
        Args:
            config_path: Optional path to a JSON config file to load.
                         If None, an empty configuration is created.
        """
        self.values: Dict[str, Any] = {}
        self.config_path = Path(config_path) if config_path else None
        
        # Load from file if provided
        if self.config_path and self.config_path.exists():
            self.load_from_file()
        
        # Set default values
        self._set_defaults()
    
    def _set_defaults(self):
        """Set default configuration values."""
        defaults = {
            # General settings
            "verbose": False,
            
            # Model settings
            "model": {
                "name": "phi-2",
                "type": "phi",
                "file": "phi-2.Q4_K_M.gguf",
                "url": "https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q4_K_M.gguf",
                "max_length": 512,
                "temperature": 0.7,
                "top_p": 0.9,
            },
            
            # Dataset settings
            "datasets": {
                # Disabled datasets that require authentication
                "codexglue": {
                    "enabled": False,  # Requires HuggingFace authentication
                    "url": "https://huggingface.co/datasets/codexglue/resolve/main/codexglue.tar.gz",
                },
                "mbpp": {
                    "enabled": False,  # Dataset not publicly available
                    "url": "https://huggingface.co/datasets/mbpp/resolve/main/mbpp.jsonl",
                },
                # QuixBugs is the only dataset that works without auth
                "quixbugs": {
                    "enabled": True,
                    "url": "https://github.com/jkoppel/QuixBugs/archive/refs/heads/master.zip",
                },
            },
            
            # Evolution settings
            "evolution": {
                "population_size": 20,
                "generations": 10,
                "mutation_rate": 0.2,
                "crossover_rate": 0.7,
                "selection_strategy": "tournament",
                "tournament_size": 3,
                "elitism": True,
                "elite_size": 2,
            },
            
            # Scanner settings
            "scanner": {
                "file_extensions": [".py", ".js", ".ts", ".java", ".c", ".cpp", ".h", ".hpp"],
                "exclude_patterns": ["__pycache__", "node_modules", ".git", "venv", "env", "build", "dist"],
                "max_file_size_mb": 10,
            },
            
            # Paths
            "paths": {
                "models_dir": "~/.bolor/models",
                "datasets_dir": "~/.bolor/datasets",
                "vector_store_dir": "~/.bolor/vector_store",
                "cache_dir": "~/.bolor/cache",
            },
        }
        
        # Only set defaults for keys that don't exist yet
        for key, value in self._flatten_dict(defaults).items():
            if not self.has(key):
                self.set(key, value)
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """
        Flatten a nested dictionary into a single-level dictionary with dot-separated keys.
        
        Args:
            d: The dictionary to flatten.
            parent_key: The parent key to use as prefix (used in recursion).
            sep: The separator to use between key levels.
            
        Returns:
            A flattened dictionary.
        """
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
                
        return dict(items)
    
    def _unflatten_dict(self, d: Dict[str, Any], sep: str = '.') -> Dict[str, Any]:
        """
        Convert a flattened dictionary with dot-separated keys back to a nested dictionary.
        
        Args:
            d: The flattened dictionary to convert.
            sep: The separator used between key levels.
            
        Returns:
            A nested dictionary.
        """
        result = {}
        
        for key, value in d.items():
            parts = key.split(sep)
            
            # Navigate to the correct level in the result dictionary
            current = result
            for i, part in enumerate(parts[:-1]):
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            # Set the value at the leaf
            current[parts[-1]] = value
            
        return result
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.
        
        This method supports accessing nested values using dot notation,
        e.g., "model.temperature".
        
        Args:
            key: The key to look up.
            default: Default value to return if key is not found.
            
        Returns:
            The configuration value, or default if not found.
        """
        # Handle nested keys
        if '.' in key:
            parts = key.split('.')
            current = self.values
            
            for part in parts[:-1]:
                if part not in current or not isinstance(current[part], dict):
                    return default
                current = current[part]
            
            return current.get(parts[-1], default)
        
        return self.values.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value by key.
        
        This method supports setting nested values using dot notation,
        e.g., "model.temperature".
        
        Args:
            key: The key to set.
            value: The value to set.
        """
        # Handle nested keys
        if '.' in key:
            parts = key.split('.')
            current = self.values
            
            # Navigate to the correct level, creating dictionaries as needed
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                elif not isinstance(current[part], dict):
                    current[part] = {}
                current = current[part]
            
            # Set the value at the leaf
            current[parts[-1]] = value
        else:
            self.values[key] = value
    
    def has(self, key: str) -> bool:
        """
        Check if a configuration key exists.
        
        This method supports checking nested keys using dot notation,
        e.g., "model.temperature".
        
        Args:
            key: The key to check.
            
        Returns:
            True if the key exists, False otherwise.
        """
        # Handle nested keys
        if '.' in key:
            parts = key.split('.')
            current = self.values
            
            for part in parts[:-1]:
                if part not in current or not isinstance(current[part], dict):
                    return False
                current = current[part]
            
            return parts[-1] in current
        
        return key in self.values
    
    def delete(self, key: str) -> None:
        """
        Delete a configuration key.
        
        This method supports deleting nested keys using dot notation,
        e.g., "model.temperature".
        
        Args:
            key: The key to delete.
        """
        # Handle nested keys
        if '.' in key:
            parts = key.split('.')
            current = self.values
            
            # Navigate to the correct level
            for part in parts[:-1]:
                if part not in current or not isinstance(current[part], dict):
                    return
                current = current[part]
            
            # Delete the key if it exists
            if parts[-1] in current:
                del current[parts[-1]]
        elif key in self.values:
            del self.values[key]
    
    def load_from_file(self, config_path: Optional[Union[str, Path]] = None) -> None:
        """
        Load configuration from a JSON file.
        
        Args:
            config_path: Path to the JSON file to load.
                         If None, the path provided during initialization is used.
        """
        path = Path(config_path) if config_path else self.config_path
        
        if not path:
            raise ValueError("No configuration file path provided")
        
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")
        
        with open(path, 'r') as f:
            loaded_config = json.load(f)
            
        # Convert to flattened format and update values
        flattened = self._flatten_dict(loaded_config)
        for key, value in flattened.items():
            self.set(key, value)
    
    def save_to_file(self, config_path: Optional[Union[str, Path]] = None) -> None:
        """
        Save configuration to a JSON file.
        
        Args:
            config_path: Path to save the JSON file.
                         If None, the path provided during initialization is used.
        """
        path = Path(config_path) if config_path else self.config_path
        
        if not path:
            raise ValueError("No configuration file path provided")
        
        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to nested format for better readability
        nested = self._unflatten_dict(self.values)
        
        with open(path, 'w') as f:
            json.dump(nested, f, indent=2)
    
    def get_path(self, key: str) -> Path:
        """
        Get a path from the configuration and ensure it exists.
        
        This resolves the path and creates the directory if needed.
        
        Args:
            key: The key to look up (should be a path).
            
        Returns:
            Resolved Path object.
        """
        path_str = self.get(f"paths.{key}")
        if not path_str:
            raise ValueError(f"Path not found in configuration: {key}")
        
        # Resolve ~ to home directory
        path = Path(os.path.expanduser(path_str))
        
        # Create directory if it doesn't exist
        path.mkdir(parents=True, exist_ok=True)
        
        return path
    
    def __str__(self) -> str:
        """Get a string representation of the configuration."""
        nested = self._unflatten_dict(self.values)
        return json.dumps(nested, indent=2)
