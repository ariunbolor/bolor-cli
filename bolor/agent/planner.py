"""
Planner module for Bolor code repair.

This module provides functionality for analyzing code and suggesting improvements.
"""

import os
import re
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any, Union

from bolor.utils.config import Config
from bolor.agent.models import Suggestion
from bolor.agent.scanner import Scanner
from bolor.agent.llm_wrapper import LLMWrapper


class Planner:
    """
    Planner class for suggesting code improvements.
    
    This class analyzes codebases and provides suggestions for improvements
    without directly modifying the code.
    """
    
    def __init__(self, config: Config):
        """
        Initialize a new Planner instance.
        
        Args:
            config: Configuration object containing planner settings.
        """
        self.config = config
        self.verbose = config.get("verbose", False)
        
        # Create Scanner instance for detecting issues
        self.scanner = Scanner(config)
        
        # Create LLMWrapper instance for generating suggestions
        self.llm = LLMWrapper(config)
        
        # Output format
        self.output_format = config.get("output_format", "text")
        
        # Initialize logger
        self.logger = logging.getLogger("bolor.planner")
        if self.verbose:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)
    
    def analyze_project(self, project_path: Path) -> List[Suggestion]:
        """
        Analyze a project and generate improvement suggestions.
        
        Args:
            project_path: Path to the project to analyze.
            
        Returns:
            List of improvement suggestions.
        """
        self.logger.info(f"Analyzing project: {project_path}")
        
        # Collect all suggestions
        suggestions = []
        
        # Step 1: Scan for issues using the scanner
        issues = self.scanner.scan_directory(project_path)
        
        # Convert issues to suggestions
        for issue in issues:
            # Skip issues that are unlikely to be improved by planning
            if issue.issue_type.value in ["syntax_error", "runtime_error"]:
                continue
            
            # Create a suggestion from the issue
            suggestion = Suggestion(
                title=f"Fix {issue.issue_type.value} in {issue.file_path.name}",
                type="issue",
                description=issue.description,
                file_path=issue.file_path,
                line_number=issue.line_number,
                priority="medium"
            )
            
            suggestions.append(suggestion)
        
        # Step 2: Check for deployment issues
        deployment_issues = self.scanner.scan_ci_config(project_path)
        
        # Convert deployment issues to suggestions
        for issue in deployment_issues:
            suggestion = Suggestion(
                title=f"Deployment issue: {issue.description}",
                type="deployment",
                description=issue.details or issue.description,
                file_path=issue.file_path,
                priority="high" if issue.severity == "critical" else "medium",
                references=issue.suggestions
            )
            
            suggestions.append(suggestion)
        
        # Step 3: Analyze project structure and organization
        structure_suggestions = self._analyze_project_structure(project_path)
        suggestions.extend(structure_suggestions)
        
        # Step 4: Analyze specific files for potential improvements
        file_suggestions = self._analyze_files(project_path)
        suggestions.extend(file_suggestions)
        
        # Format suggestions based on output_format
        if self.output_format == "json":
            return self._format_json(suggestions)
        elif self.output_format == "markdown":
            return self._format_markdown(suggestions)
        else:
            return suggestions
    
    def _analyze_project_structure(self, project_path: Path) -> List[Suggestion]:
        """
        Analyze the project structure and suggest improvements.
        
        Args:
            project_path: Path to the project to analyze.
            
        Returns:
            List of structure-related suggestions.
        """
        suggestions = []
        
        # Check for common files
        common_files = {
            "README.md": "Add a README file with project documentation",
            ".gitignore": "Add a .gitignore file for version control",
            "requirements.txt": "Add a requirements.txt file for Python dependencies",
            "package.json": "Add a package.json file for JavaScript dependencies",
            "LICENSE": "Add a LICENSE file for the project"
        }
        
        for filename, description in common_files.items():
            if not (project_path / filename).exists():
                suggestion = Suggestion(
                    title=f"Add {filename}",
                    type="structure",
                    description=description,
                    priority="low"
                )
                suggestions.append(suggestion)
        
        # Check for tests directory
        test_dirs = ["tests", "test"]
        has_tests = any((project_path / d).exists() for d in test_dirs)
        if not has_tests:
            suggestion = Suggestion(
                title="Add tests directory",
                type="structure",
                description="Add a tests directory for unit and integration tests",
                priority="medium"
            )
            suggestions.append(suggestion)
        
        # Check for docs directory
        docs_dirs = ["docs", "doc", "documentation"]
        has_docs = any((project_path / d).exists() for d in docs_dirs)
        if not has_docs:
            suggestion = Suggestion(
                title="Add documentation directory",
                type="structure",
                description="Add a docs directory for project documentation",
                priority="low"
            )
            suggestions.append(suggestion)
        
        return suggestions
    
    def _analyze_files(self, project_path: Path) -> List[Suggestion]:
        """
        Analyze individual files and suggest improvements.
        
        Args:
            project_path: Path to the project to analyze.
            
        Returns:
            List of file-specific suggestions.
        """
        suggestions = []
        
        # Limit to specific number of files for performance
        max_files = 10
        file_count = 0
        
        # Get file extensions from scanner config
        file_extensions = self.scanner.file_extensions
        
        # Walk through project directory
        for root, dirs, files in os.walk(project_path):
            # Skip directories that should be excluded
            dirs[:] = [d for d in dirs if not self.scanner._should_exclude(d)]
            
            for file in files:
                file_path = Path(os.path.join(root, file))
                
                # Skip files that shouldn't be analyzed
                if not file_path.suffix in file_extensions:
                    continue
                
                # Skip files that are too large
                if not self.scanner._check_file_size(file_path):
                    continue
                
                # Generate improvement suggestions for this file
                file_suggestions = self._generate_suggestions_for_file(file_path)
                suggestions.extend(file_suggestions)
                
                # Increment file count
                file_count += 1
                if file_count >= max_files:
                    break
            
            if file_count >= max_files:
                break
        
        return suggestions
    
    def _generate_suggestions_for_file(self, file_path: Path) -> List[Suggestion]:
        """
        Generate improvement suggestions for a specific file.
        
        Args:
            file_path: Path to the file to analyze.
            
        Returns:
            List of suggestions for the file.
        """
        suggestions = []
        
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            # Skip empty files
            if not content.strip():
                return []
            
            # Use LLM to generate improvement suggestions
            llm_suggestions = self._generate_llm_suggestions(file_path, content)
            
            # Process LLM suggestions
            for i, suggestion in enumerate(llm_suggestions):
                if 'title' not in suggestion or 'description' not in suggestion:
                    continue
                
                sugg = Suggestion(
                    title=suggestion['title'],
                    type="improvement",
                    description=suggestion['description'],
                    file_path=file_path,
                    code_example=suggestion.get('example'),
                    priority="medium",
                    references=[]
                )
                
                suggestions.append(sugg)
            
        except Exception as e:
            self.logger.warning(f"Error generating suggestions for {file_path}: {str(e)}")
        
        return suggestions
    
    def _generate_llm_suggestions(self, file_path: Path, content: str) -> List[Dict[str, str]]:
        """
        Use the LLM to generate improvement suggestions.
        
        Args:
            file_path: Path to the file to analyze.
            content: Content of the file.
            
        Returns:
            List of suggestion dictionaries from the LLM.
        """
        try:
            # Determine improvement type based on file extension
            improvement_type = None
            if file_path.suffix == '.py':
                improvement_type = "Python"
            elif file_path.suffix in ['.js', '.ts']:
                improvement_type = "JavaScript/TypeScript"
            elif file_path.suffix == '.java':
                improvement_type = "Java"
            elif file_path.suffix in ['.c', '.cpp', '.h', '.hpp']:
                improvement_type = "C/C++"
            
            # Generate suggestions using the LLM
            suggestions = self.llm.generate_code_improvements(
                code=content,
                improvement_type=improvement_type
            )
            
            return suggestions
            
        except Exception as e:
            self.logger.warning(f"Error using LLM for suggestions: {str(e)}")
            return []
    
    def _format_json(self, suggestions: List[Suggestion]) -> List[Suggestion]:
        """
        Format suggestions for JSON output.
        
        Args:
            suggestions: List of suggestions to format.
            
        Returns:
            Formatted list of suggestions.
        """
        # For JSON output, just return the suggestions as they are
        # The Suggestion class has a to_dict method for conversion
        return suggestions
    
    def _format_markdown(self, suggestions: List[Suggestion]) -> List[Suggestion]:
        """
        Format suggestions for Markdown output.
        
        Args:
            suggestions: List of suggestions to format.
            
        Returns:
            Formatted list of suggestions.
        """
        # For Markdown output, add markdown formatting to the descriptions
        for suggestion in suggestions:
            # Add markdown formatting to the description
            if suggestion.description:
                suggestion.description = f"{suggestion.description}\n\n"
            
            # Add code block formatting to the code example
            if suggestion.code_example:
                language = ""
                if suggestion.file_path:
                    if suggestion.file_path.suffix == '.py':
                        language = "python"
                    elif suggestion.file_path.suffix in ['.js', '.ts']:
                        language = "javascript"
                    elif suggestion.file_path.suffix == '.java':
                        language = "java"
                    elif suggestion.file_path.suffix in ['.c', '.cpp', '.h', '.hpp']:
                        language = "cpp"
                
                suggestion.code_example = f"```{language}\n{suggestion.code_example}\n```"
            
            # Add bullet points for references
            if suggestion.references:
                references_md = "\n\n**References:**\n"
                for ref in suggestion.references:
                    references_md += f"- {ref}\n"
                suggestion.description += references_md
        
        return suggestions
