#!/usr/bin/env python3
"""
Example demonstrating the natural language interface of Bolor.

This example shows how to use Bolor's natural language interface to generate code.
This is a patched version that mocks the code generation to avoid model loading issues.
"""

import os
from pathlib import Path

# Add parent directory to path to be able to import bolor
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bolor.utils.config import Config


class MockGenerator:
    """
    Mock Generator class that returns canned responses instead of using the LLM.
    """
    
    def __init__(self, config):
        """Initialize a new MockGenerator instance."""
        self.config = config
    
    def generate_from_prompt(self, prompt, language=None, add_comments=True):
        """
        Generate mock code based on the prompt and language.
        
        Args:
            prompt: Description of what to generate
            language: Programming language
            add_comments: Whether to add comments
            
        Returns:
            Generated code string (mocked)
        """
        if "weather" in prompt.lower():
            return """import requests

def get_weather_data(city, api_key="YOUR_API_KEY"):
    # Get weather data for a given city from OpenWeatherMap API.
    #
    # Args:
    #     city: Name of the city to get weather data for
    #     api_key: OpenWeatherMap API key (get one at https://openweathermap.org/api)
    #
    # Returns:
    #     Dictionary containing weather data
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric"  # Use metric units (Celsius)
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        # Parse JSON response
        weather_data = response.json()
        
        return {
            "city": city,
            "temperature": weather_data["main"]["temp"],
            "description": weather_data["weather"][0]["description"],
            "humidity": weather_data["main"]["humidity"],
            "wind_speed": weather_data["wind"]["speed"],
            "country": weather_data["sys"]["country"]
        }
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return None
"""
        elif "github" in prompt.lower():
            return """name: Deploy to AWS Elastic Beanstalk

on:
  push:
    branches: [ main ]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '16'
        cache: 'npm'
    
    - name: Install dependencies
      run: npm ci
    
    - name: Build application
      run: npm run build
    
    - name: Run tests
      run: npm test
    
    - name: Generate deployment package
      run: zip -r deploy.zip . -x "*.git*" node_modules/\\*
    
    - name: Deploy to AWS Elastic Beanstalk
      uses: einaregilsson/beanstalk-deploy@v21
      with:
        aws_access_key: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws_secret_key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        application_name: my-node-app
        environment_name: my-node-app-production
        version_label: ${{ github.sha }}
        region: us-east-1
        deployment_package: deploy.zip
"""
        elif "express" in prompt.lower():
            return """const express = require('express');
const router = express.Router();

// Import user controller
const userController = require('../controllers/userController');

// GET all users
router.get('/', userController.getAllUsers);

// GET a single user by ID
router.get('/:id', userController.getUserById);

// POST create a new user
router.post('/', userController.createUser);

// PUT update a user
router.put('/:id', userController.updateUser);

// DELETE a user
router.delete('/:id', userController.deleteUser);

module.exports = router;

// --- userController.js (implementation) ---
// const User = require('../models/user');

// exports.getAllUsers = async (req, res) => {
//   try {
//     const users = await User.find();
//     res.status(200).json(users);
//   } catch (err) {
//     res.status(500).json({ message: err.message });
//   }
// };

// exports.getUserById = async (req, res) => {
//   try {
//     const user = await User.findById(req.params.id);
//     if (!user) return res.status(404).json({ message: 'User not found' });
//     res.status(200).json(user);
//   } catch (err) {
//     res.status(500).json({ message: err.message });
//   }
// };

// exports.createUser = async (req, res) => {
//   const user = new User(req.body);
//   try {
//     const newUser = await user.save();
//     res.status(201).json(newUser);
//   } catch (err) {
//     res.status(400).json({ message: err.message });
//   }
// };

// exports.updateUser = async (req, res) => {
//   try {
//     const user = await User.findByIdAndUpdate(req.params.id, req.body, { new: true });
//     if (!user) return res.status(404).json({ message: 'User not found' });
//     res.status(200).json(user);
//   } catch (err) {
//     res.status(400).json({ message: err.message });
//   }
// };

// exports.deleteUser = async (req, res) => {
//   try {
//     const user = await User.findByIdAndDelete(req.params.id);
//     if (!user) return res.status(404).json({ message: 'User not found' });
//     res.status(200).json({ message: 'User deleted' });
//   } catch (err) {
//     res.status(500).json({ message: err.message });
//   }
// };
"""
        else:
            return """def fibonacci(n):
    # Calculate the Fibonacci number at position n.
    #
    # The Fibonacci sequence starts with 0 and 1,
    # and each subsequent number is the sum of the two previous ones.
    #
    # Args:
    #     n: Position in the Fibonacci sequence (0-indexed)
    #        Must be a non-negative integer
    #
    # Returns:
    #     The Fibonacci number at position n
    #
    # Raises:
    #     ValueError: If n is negative
    if n < 0:
        raise ValueError("Input must be a non-negative integer")
    
    if n <= 1:
        return n
        
    # Initialize first two numbers
    a, b = 0, 1
    
    # Calculate fib(n) by iteration
    for _ in range(2, n + 1):
        a, b = b, a + b
        
    return b
"""
    
    def generate_file(self, prompt, file_path):
        """
        Generate code and save it to a file (mocked).
        
        Args:
            prompt: Description of what to generate
            file_path: Path to save the file to
            
        Returns:
            Path object pointing to the created file
        """
        # Convert to Path object
        file_path = Path(file_path)
        
        # Generate code
        generated_code = self.generate_from_prompt(prompt)
        
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to file
        with open(file_path, 'w') as f:
            f.write(generated_code)
        
        return file_path


def main():
    """
    Main function to demonstrate Bolor's NLP capabilities.
    """
    print("=" * 80)
    print("Bolor Natural Language Interface Example (MOCK VERSION)")
    print("=" * 80)
    print("Note: This is a patched version that uses canned responses instead of loading the model")
    print("      to avoid model loading issues. The actual implementation would use the LLM.")
    
    # Initialize config
    config = Config()
    config.set("verbose", True)
    
    # Initialize generator
    generator = MockGenerator(config)
    
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
