#!/usr/bin/env python3
"""
Example demonstrating the natural language interface of Bolor.

This example shows how to use Bolor's natural language interface to generate code.
"""

import os
from pathlib import Path

# Add parent directory to path to be able to import bolor
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bolor.utils.config import Config
from bolor.agent.generator import Generator


def main():
    """
    Main function to demonstrate Bolor's NLP capabilities.
    """
    print("=" * 80)
    print("Bolor Natural Language Interface Example")
    print("=" * 80)
    
    # Initialize config
    config = Config()
    config.set("verbose", True)
    
    # Initialize generator
    generator = Generator(config)
    
    # Example 1: Generate Python code
    print("\n\n[Example 1] Generating a Python utility function\n")
    prompt = "Create a function that fetches weather data from OpenWeatherMap API for a given city"
    language = "python"
    
    print(f"Prompt: {prompt}")
    print(f"Language: {language}")
    print("-" * 40)
    
    code = generator.generate_from_prompt(prompt, language)
    print(code)
    
    # Example 2: Generate a GitHub Actions workflow
    print("\n\n[Example 2] Generating a GitHub Actions workflow for AWS deployment\n")
    prompt = "Create GitHub action workflow for deploying a Node.js application to AWS Elastic Beanstalk"
    
    print(f"Prompt: {prompt}")
    print("-" * 40)
    
    # Auto-detect YAML for GitHub Actions
    code = generator.generate_from_prompt(prompt)
    print(code)
    
    # Example 3: Generate and save to file
    print("\n\n[Example 3] Generating code and saving to file\n")
    prompt = "Create a simple REST API using Express.js with routes for CRUD operations on a 'users' resource"
    output_file = Path("./generated_express_api.js")
    
    print(f"Prompt: {prompt}")
    print(f"Output file: {output_file}")
    print("-" * 40)
    
    # Generate and save to file
    file_path = generator.generate_file(prompt, output_file)
    print(f"Code saved to: {file_path}")
    
    print("\n\nThis is just a demonstration - in practice, you can use the CLI:")
    print("  bolor \"create a function to calculate Fibonacci numbers\"")
    print("  bolor generate \"create a React component for a login form\" --output LoginForm.jsx")


if __name__ == "__main__":
    main()
