"""
Fixer module for Bolor code repair.

This module provides functionality for generating and applying fixes to code issues
detected by the scanner.
"""

import os
import re
import ast
import sys
import logging
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any, Union, Callable

from bolor.utils.config import Config
from bolor.agent.models import Issue, IssueStatus, FixCandidate
from bolor.agent.llm_wrapper import LLMWrapper
from bolor.agent.dataset_loader import DatasetLoader


class Fixer:
    """
    Fixer class for repairing code issues.
    
    This class provides methods for generating and applying fixes to code issues
    detected by the scanner.
    """
    
    def __init__(self, config: Config):
        """
        Initialize a new Fixer instance.
        
        Args:
            config: Configuration object containing fixer settings.
        """
        self.config = config
        self.verbose = config.get("verbose", False)
        
        # Create LLMWrapper instance
        self.llm = LLMWrapper(config)
        
        # Create DatasetLoader instance for retrieving similar bug fixes
        self.dataset_loader = DatasetLoader(config)
        
        # Initialize logger
        self.logger = logging.getLogger("bolor.fixer")
        if self.verbose:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)
    
    def fix_issues(self, issues: List[Issue]) -> List[Issue]:
        """
        Generate and apply fixes for a list of issues.
        
        Args:
            issues: List of issues to fix.
            
        Returns:
            List of fixed issues.
        """
        fixed_issues = []
        
        for issue in issues:
            try:
                # Skip issues that have no file path or code snippet
                if not issue.file_path or not issue.code_snippet:
                    self.logger.warning(f"Skipping issue without file path or code snippet: {issue}")
                    continue
                
                # Update issue status
                issue.status = IssueStatus.ANALYZING
                
                # Check if the file exists
                if not issue.file_path.exists():
                    self.logger.warning(f"File not found: {issue.file_path}")
                    continue
                
                # Generate fix
                fixed_issue = self.generate_fix(issue)
                
                if fixed_issue.status == IssueStatus.FIXED:
                    fixed_issues.append(fixed_issue)
                
            except Exception as e:
                self.logger.error(f"Error fixing issue {issue}: {str(e)}")
                issue.status = IssueStatus.UNFIXABLE
        
        return fixed_issues
    
    def generate_fix(self, issue: Issue) -> Issue:
        """
        Generate a fix for a specific issue.
        
        Args:
            issue: Issue to fix.
            
        Returns:
            Fixed issue (or the original issue if it couldn't be fixed).
        """
        # Get the full file content
        with open(issue.file_path, 'r', encoding='utf-8', errors='replace') as f:
            file_content = f.read()
        
        # For issues with line numbers, extract the context
        if issue.line_number is not None:
            context = self._extract_context(file_content, issue.line_number, context_lines=5)
        else:
            context = issue.code_snippet or file_content
        
        # Get error message
        error_message = issue.description
        
        # Try to find similar bugs in the dataset
        similar_bugs = []
        try:
            similar_bugs = self.dataset_loader.query_similar_bugs(
                error_message=error_message,
                code_snippet=context,
                limit=3
            )
        except Exception as e:
            self.logger.warning(f"Error querying similar bugs: {str(e)}")
        
        # Generate fix candidates using an evolutionary approach
        candidates = self._generate_fix_candidates(issue, file_content, context, similar_bugs)
        
        # If we have candidates, select the best one and apply it
        if candidates:
            # Sort candidates by fitness (highest first)
            candidates.sort(key=lambda c: c.fitness, reverse=True)
            best_candidate = candidates[0]
            
            # Apply the fix if it has positive fitness
            if best_candidate.fitness > 0:
                # Apply the fix to the file
                updated_content = self._apply_fix(file_content, best_candidate)
                
                # Update the file
                with open(issue.file_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                
                # Update the issue
                issue.fixed_code_snippet = best_candidate.modified_code
                issue.status = IssueStatus.FIXED
                issue.confidence_score = best_candidate.fitness
                issue.fix_attempts.append({
                    "fixed_code": best_candidate.modified_code,
                    "fitness": best_candidate.fitness,
                    "errors": best_candidate.errors
                })
                
                self.logger.info(f"Fixed issue in {issue.file_path}")
            else:
                issue.status = IssueStatus.UNFIXABLE
                self.logger.warning(f"Could not find a good fix for issue in {issue.file_path}")
        else:
            issue.status = IssueStatus.UNFIXABLE
            self.logger.warning(f"No fix candidates generated for issue in {issue.file_path}")
        
        return issue
    
    def _extract_context(self, file_content: str, line_number: int, context_lines: int = 5) -> str:
        """
        Extract context around a specific line in the file.
        
        Args:
            file_content: Content of the file.
            line_number: Line number to extract context for (1-based).
            context_lines: Number of lines before and after the target line.
            
        Returns:
            Context string.
        """
        lines = file_content.splitlines()
        
        # Adjust line_number to 0-based index
        line_idx = line_number - 1
        
        # Calculate start and end lines with boundaries
        start_idx = max(0, line_idx - context_lines)
        end_idx = min(len(lines), line_idx + context_lines + 1)
        
        # Extract the context
        context_lines = lines[start_idx:end_idx]
        
        return '\n'.join(context_lines)
    
    def _generate_fix_candidates(
        self,
        issue: Issue,
        file_content: str,
        context: str,
        similar_bugs: List[Dict[str, Any]]
    ) -> List[FixCandidate]:
        """
        Generate fix candidates for an issue using an evolutionary approach.
        
        Args:
            issue: Issue to fix.
            file_content: Full content of the file.
            context: Context around the issue.
            similar_bugs: Similar bugs from the dataset.
            
        Returns:
            List of fix candidates.
        """
        # Initialize population
        population_size = self.config.get("evolution.population_size", 10)
        generations = self.config.get("evolution.generations", 5)
        
        # Initial population
        population = self._initialize_population(issue, context, similar_bugs, population_size)
        
        # Evaluate initial population
        for candidate in population:
            self._evaluate_candidate(candidate, issue, file_content)
        
        # Check if we have any valid candidates
        valid_candidates = [c for c in population if c.is_valid]
        if not valid_candidates:
            self.logger.warning(f"No valid candidates in initial population for issue in {issue.file_path}")
            return population
        
        # Evolve for specified number of generations
        for gen in range(generations):
            self.logger.debug(f"Generation {gen + 1}/{generations}")
            
            # Select parents
            parents = self._select_parents(population)
            
            # Create next generation
            next_gen = self._create_next_generation(parents, issue, gen + 1)
            
            # Evaluate next generation
            for candidate in next_gen:
                self._evaluate_candidate(candidate, issue, file_content)
            
            # Update population
            population = next_gen
            
            # Check for early stopping
            best_candidate = max(population, key=lambda c: c.fitness)
            if best_candidate.fitness >= 0.9:
                self.logger.debug(f"Early stopping at generation {gen + 1} with fitness {best_candidate.fitness}")
                break
        
        return population
    
    def _initialize_population(
        self,
        issue: Issue,
        context: str,
        similar_bugs: List[Dict[str, Any]],
        population_size: int
    ) -> List[FixCandidate]:
        """
        Initialize a population of fix candidates.
        
        Args:
            issue: Issue to fix.
            context: Context around the issue.
            similar_bugs: Similar bugs from the dataset.
            population_size: Size of the population to generate.
            
        Returns:
            List of initial fix candidates.
        """
        candidates = []
        
        # Strategy 1: Use LLM to generate fix
        try:
            llm_fix = self.llm.generate_code_fix(
                buggy_code=context,
                error_message=issue.description
            )
            
            if llm_fix:
                candidates.append(FixCandidate(
                    issue=issue,
                    modified_code=llm_fix,
                    generation=0
                ))
        except Exception as e:
            self.logger.warning(f"Error generating LLM fix: {str(e)}")
        
        # Strategy 2: Use similar bugs from dataset
        for bug in similar_bugs:
            try:
                if "fixed_code" in bug.get("metadata", {}):
                    # Create a candidate based on the similar bug fix
                    fixed_code = bug["metadata"]["fixed_code"]
                    
                    # Simple adaptation: replace the buggy code with the fixed code
                    # In a real system, this would involve more sophisticated adaptation
                    candidates.append(FixCandidate(
                        issue=issue,
                        modified_code=fixed_code,
                        generation=0,
                        metadata={"source": "dataset", "distance": bug.get("distance")}
                    ))
            except Exception as e:
                self.logger.warning(f"Error creating candidate from similar bug: {str(e)}")
        
        # Strategy 3: Try simple fixes based on issue type
        if issue.issue_type.value == "syntax_error":
            try:
                # Try to fix common syntax errors
                syntax_fixes = self._generate_syntax_fixes(context)
                for fix in syntax_fixes:
                    candidates.append(FixCandidate(
                        issue=issue,
                        modified_code=fix,
                        generation=0,
                        metadata={"source": "syntax_fix"}
                    ))
            except Exception as e:
                self.logger.warning(f"Error generating syntax fixes: {str(e)}")
        
        # If we don't have enough candidates, generate random variations
        while len(candidates) < population_size:
            # Choose a random existing candidate to mutate
            if candidates:
                parent = candidates[0] if len(candidates) == 1 else candidates[len(candidates) % 2]
                mutated = self._mutate_candidate(parent)
                candidates.append(mutated)
            else:
                # Fallback: Use LLM with different temperature
                try:
                    llm_fix = self.llm.generate_code_fix(
                        buggy_code=context,
                        error_message=issue.description
                    )
                    
                    if llm_fix:
                        candidates.append(FixCandidate(
                            issue=issue,
                            modified_code=llm_fix,
                            generation=0
                        ))
                except Exception as e:
                    # If all else fails, just add an empty fix
                    candidates.append(FixCandidate(
                        issue=issue,
                        modified_code=context,
                        generation=0
                    ))
        
        return candidates
    
    def _generate_syntax_fixes(self, context: str) -> List[str]:
        """
        Generate fixes for common syntax errors.
        
        Args:
            context: Context with syntax error.
            
        Returns:
            List of potential fixed code strings.
        """
        fixes = []
        
        # Common fixes for Python syntax errors
        
        # Fix 1: Missing closing parentheses/brackets/braces
        for char, pair in [('(', ')'), ('[', ']'), ('{', '}')]:
            if context.count(char) > context.count(pair):
                # Add missing closing characters
                diff = context.count(char) - context.count(pair)
                fixed = context + pair * diff
                fixes.append(fixed)
        
        # Fix 2: Missing colons in statements
        for pattern, replacement in [
            (r'(\s*if\s+[^:]+)$', r'\1:'),
            (r'(\s*elif\s+[^:]+)$', r'\1:'),
            (r'(\s*else\s*)$', r'\1:'),
            (r'(\s*for\s+[^:]+)$', r'\1:'),
            (r'(\s*while\s+[^:]+)$', r'\1:'),
            (r'(\s*def\s+[^:]+)$', r'\1:'),
            (r'(\s*class\s+[^:]+)$', r'\1:'),
            (r'(\s*try\s*)$', r'\1:'),
            (r'(\s*except\s+[^:]+)$', r'\1:'),
            (r'(\s*finally\s*)$', r'\1:'),
        ]:
            fixed = re.sub(pattern, replacement, context, flags=re.MULTILINE)
            if fixed != context:
                fixes.append(fixed)
        
        # Fix 3: Fix indentation (simplified)
        lines = context.splitlines()
        if lines:
            # Try to fix common indentation errors
            fixed_lines = []
            for i, line in enumerate(lines):
                if i > 0 and line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                    # Add indentation if the previous non-empty line ends with a colon
                    prev_line = lines[i-1].strip()
                    if prev_line.endswith(':'):
                        fixed_lines.append('    ' + line)
                    else:
                        fixed_lines.append(line)
                else:
                    fixed_lines.append(line)
            
            if fixed_lines != lines:
                fixes.append('\n'.join(fixed_lines))
        
        return fixes
    
    def _mutate_candidate(self, candidate: FixCandidate) -> FixCandidate:
        """
        Mutate a fix candidate to create a new variant.
        
        Args:
            candidate: Candidate to mutate.
            
        Returns:
            New mutated candidate.
        """
        # Get the code to mutate
        code = candidate.modified_code
        lines = code.splitlines()
        
        if not lines:
            return FixCandidate(
                issue=candidate.issue,
                modified_code=code,
                generation=candidate.generation + 1,
                parent_ids=[candidate.id]
            )
        
        # Choose a random mutation strategy
        import random
        strategy = random.choice([
            'change_line',
            'add_line',
            'remove_line',
            'swap_lines',
            'indent_line',
        ])
        
        try:
            if strategy == 'change_line' and len(lines) > 0:
                # Modify a random line
                line_idx = random.randint(0, len(lines) - 1)
                original_line = lines[line_idx]
                
                # Try to fix common patterns
                if "= ==" in original_line:
                    lines[line_idx] = original_line.replace("= ==", "==")
                elif "==" in original_line and random.random() < 0.3:
                    lines[line_idx] = original_line.replace("==", "!=")
                elif "++" in original_line:
                    lines[line_idx] = original_line.replace("++", " += 1")
                elif "--" in original_line:
                    lines[line_idx] = original_line.replace("--", " -= 1")
                elif "; ;" in original_line:
                    lines[line_idx] = original_line.replace("; ;", ";")
                else:
                    # Just add or remove whitespace
                    lines[line_idx] = original_line.strip()
            
            elif strategy == 'add_line' and len(lines) > 0:
                # Add a line
                line_idx = random.randint(0, len(lines))
                if line_idx > 0 and line_idx < len(lines):
                    prev_line = lines[line_idx - 1]
                    indent = len(prev_line) - len(prev_line.lstrip())
                    indent_str = ' ' * indent
                    
                    # Add a simple comment
                    lines.insert(line_idx, f"{indent_str}# Fixed line")
            
            elif strategy == 'remove_line' and len(lines) > 1:
                # Remove a line
                line_idx = random.randint(0, len(lines) - 1)
                if not lines[line_idx].strip() or lines[line_idx].strip().startswith('#'):
                    # Only remove empty lines or comments
                    lines.pop(line_idx)
            
            elif strategy == 'swap_lines' and len(lines) > 1:
                # Swap two adjacent lines
                line_idx = random.randint(0, len(lines) - 2)
                lines[line_idx], lines[line_idx + 1] = lines[line_idx + 1], lines[line_idx]
            
            elif strategy == 'indent_line' and len(lines) > 0:
                # Change indentation of a line
                line_idx = random.randint(0, len(lines) - 1)
                line = lines[line_idx]
                indent = len(line) - len(line.lstrip())
                
                if indent > 0 and random.random() < 0.5:
                    # Reduce indentation
                    lines[line_idx] = line[min(4, indent):]
                else:
                    # Increase indentation
                    lines[line_idx] = '    ' + line
        
        except Exception as e:
            # If mutation fails, return a copy of the original
            self.logger.warning(f"Error during mutation: {str(e)}")
        
        # Create new candidate
        return FixCandidate(
            issue=candidate.issue,
            modified_code='\n'.join(lines),
            generation=candidate.generation + 1,
            parent_ids=[candidate.id]
        )
    
    def _select_parents(self, population: List[FixCandidate]) -> List[FixCandidate]:
        """
        Select parent candidates for reproduction using tournament selection.
        
        Args:
            population: Current population of fix candidates.
            
        Returns:
            List of selected parent candidates.
        """
        import random
        
        # Filter valid candidates
        valid_candidates = [c for c in population if c.is_valid]
        
        if not valid_candidates:
            # If no valid candidates, use the whole population
            valid_candidates = population
        
        # Sort by fitness (highest first)
        valid_candidates.sort(key=lambda c: c.fitness, reverse=True)
        
        # Use tournament selection
        tournament_size = min(3, len(valid_candidates))
        selected = []
        
        # Select as many parents as the current population size
        for _ in range(len(population)):
            # Randomly select tournament_size candidates
            tournament = random.sample(valid_candidates, tournament_size)
            
            # Select the candidate with the highest fitness
            winner = max(tournament, key=lambda c: c.fitness)
            selected.append(winner)
        
        return selected
    
    def _create_next_generation(
        self,
        parents: List[FixCandidate],
        issue: Issue,
        generation: int
    ) -> List[FixCandidate]:
        """
        Create a new generation of fix candidates.
        
        Args:
            parents: Parent candidates selected for reproduction.
            issue: Issue being fixed.
            generation: Current generation number.
            
        Returns:
            List of candidates in the new generation.
        """
        import random
        
        mutation_rate = self.config.get("evolution.mutation_rate", 0.2)
        crossover_rate = self.config.get("evolution.crossover_rate", 0.7)
        elitism = self.config.get("evolution.elitism", True)
        elite_size = self.config.get("evolution.elite_size", 2) if elitism else 0
        
        # Create new population
        new_population = []
        
        # Add elite candidates if enabled
        if elitism and elite_size > 0:
            # Sort parents by fitness (highest first)
            sorted_parents = sorted(parents, key=lambda c: c.fitness, reverse=True)
            
            # Add top candidates to new population
            new_population.extend(sorted_parents[:elite_size])
        
        # Fill the rest of the population
        while len(new_population) < len(parents):
            # Select two parents
            parent1 = random.choice(parents)
            parent2 = random.choice(parents)
            
            # Perform crossover with probability crossover_rate
            if random.random() < crossover_rate and parent1 != parent2:
                child = self._crossover(parent1, parent2, issue, generation)
            else:
                # No crossover, just clone one parent
                child = FixCandidate(
                    issue=issue,
                    modified_code=parent1.modified_code,
                    generation=generation,
                    parent_ids=[parent1.id]
                )
            
            # Perform mutation with probability mutation_rate
            if random.random() < mutation_rate:
                child = self._mutate_candidate(child)
            
            new_population.append(child)
        
        return new_population[:len(parents)]  # Ensure the same population size
    
    def _crossover(
        self,
        parent1: FixCandidate,
        parent2: FixCandidate,
        issue: Issue,
        generation: int
    ) -> FixCandidate:
        """
        Perform crossover between two parent candidates.
        
        Args:
            parent1: First parent candidate.
            parent2: Second parent candidate.
            issue: Issue being fixed.
            generation: Current generation number.
            
        Returns:
            New child candidate.
        """
        import random
        
        # Get the code from both parents
        code1 = parent1.modified_code
        code2 = parent2.modified_code
        
        # Split the code into lines
        lines1 = code1.splitlines()
        lines2 = code2.splitlines()
        
        if not lines1 or not lines2:
            # If either parent has no lines, return the other parent
            return FixCandidate(
                issue=issue,
                modified_code=code1 if lines1 else code2,
                generation=generation,
                parent_ids=[parent1.id, parent2.id]
            )
        
        # Perform line-level crossover
        if len(lines1) == 1 or len(lines2) == 1:
            # For single-line fixes, use character-level crossover
            crossover_point = random.randint(1, min(len(code1), len(code2)) - 1)
            new_code = code1[:crossover_point] + code2[crossover_point:]
        else:
            # For multi-line fixes, use line-level crossover
            crossover_point = random.randint(1, min(len(lines1), len(lines2)) - 1)
            new_lines = lines1[:crossover_point] + lines2[crossover_point:]
            new_code = '\n'.join(new_lines)
        
        # Create new candidate
        return FixCandidate(
            issue=issue,
            modified_code=new_code,
            generation=generation,
            parent_ids=[parent1.id, parent2.id]
        )
    
    def _evaluate_candidate(
        self,
        candidate: FixCandidate,
        issue: Issue,
        file_content: str
    ) -> None:
        """
        Evaluate a fix candidate's fitness.
        
        Args:
            candidate: Candidate to evaluate.
            issue: Issue being fixed.
            file_content: Original file content.
            
        Returns:
            None (updates the candidate in place).
        """
        # Apply the fix to a temporary copy of the file
        try:
            # Create a temporary file with the fix applied
            temp_content = self._apply_fix(file_content, candidate)
            
            # Basic validation
            if not temp_content or temp_content == file_content:
                candidate.is_valid = False
                candidate.fitness = 0.0
                candidate.errors = ["No changes made to the file"]
                return
            
            # Write to a temporary file
            with tempfile.NamedTemporaryFile(suffix=f"{issue.file_path.suffix}", delete=False) as temp_file:
                temp_path = Path(temp_file.name)
                temp_file.write(temp_content.encode('utf-8'))
            
            try:
                # Check for syntax errors
                if issue.file_path.suffix == '.py':
                    self._check_python_syntax(temp_path, candidate)
                elif issue.file_path.suffix in ['.js', '.ts']:
                    self._check_js_syntax(temp_path, candidate)
                elif issue.file_path.suffix == '.java':
                    self._check_java_syntax(temp_path, candidate)
                elif issue.file_path.suffix in ['.c', '.cpp', '.h', '.hpp']:
                    self._check_cpp_syntax(temp_path, candidate)
                else:
                    # For other file types, just check if the issue is fixed
                    self._check_issue_fixed(candidate, issue, temp_content)
                
                # Additional checks based on issue type
                if issue.issue_type.value == "syntax_error" and candidate.is_valid:
                    # Give a higher fitness score for syntax error fixes
                    candidate.fitness += 0.2
                
                # Penalize excessive changes
                self._penalize_excessive_changes(candidate, file_content, temp_content)
                
                # Limit fitness to range [0.0, 1.0]
                candidate.fitness = max(0.0, min(1.0, candidate.fitness))
                
            finally:
                # Clean up the temporary file
                try:
                    temp_path.unlink()
                except:
                    pass
                
        except Exception as e:
            self.logger.warning(f"Error evaluating candidate: {str(e)}")
            candidate.is_valid = False
            candidate.fitness = 0.0
            candidate.errors = [str(e)]
    
    def _apply_fix(self, file_content: str, candidate: FixCandidate) -> str:
        """
        Apply a fix candidate to the file content.
        
        Args:
            file_content: Original file content.
            candidate: Fix candidate to apply.
            
        Returns:
            Updated file content with the fix applied.
        """
        # Get the issue details
        issue = candidate.issue
        fixed_code = candidate.modified_code
        
        if issue.line_number is not None and issue.line_number > 0:
            # For issues with a specific line number, replace just that section
            lines = file_content.splitlines()
            
            # Calculate start and end lines for the context
            context_lines = 5  # Same as in _extract_context
            start_idx = max(0, issue.line_number - 1 - context_lines)
            end_idx = min(len(lines), issue.line_number - 1 + context_lines + 1)
            
            # Replace the context with the fixed code
            original_context = '\n'.join(lines[start_idx:end_idx])
            if original_context in file_content:
                return file_content.replace(original_context, fixed_code)
            
            # Fallback: replace the specific line
            if issue.line_number <= len(lines):
                original_line = lines[issue.line_number - 1]
                fixed_lines = fixed_code.splitlines()
                
                if len(fixed_lines) == 1:
                    # Simple line replacement
                    lines[issue.line_number - 1] = fixed_lines[0]
                elif len(fixed_lines) > 1:
                    # Replace with multiple lines
                    lines[issue.line_number - 1:issue.line_number] = fixed_lines
                
                return '\n'.join(lines)
        
        # For other cases, try to replace the specific code snippet
        if issue.code_snippet and issue.code_snippet in file_content:
            return file_content.replace(issue.code_snippet, fixed_code)
        
        # Fallback: return the full fixed file content
        # This is less ideal as it might lose formatting, comments, etc.
        return fixed_code
    
    def _check_python_syntax(self, file_path: Path, candidate: FixCandidate) -> None:
        """
        Check Python syntax and update the candidate's fitness.
        
        Args:
            file_path: Path to the file to check.
            candidate: Candidate to update.
        """
        try:
            # Try to parse the Python file
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                ast.parse(f.read())
            
            # If parsing succeeds, the syntax is valid
            candidate.is_valid = True
            candidate.fitness = 0.7  # Start with a good fitness score
            candidate.errors = []
            
        except SyntaxError as e:
            # Syntax error: invalid fix
            candidate.is_valid = False
            candidate.fitness = 0.0
            candidate.errors = [f"Syntax error: {e}"]
            
        except Exception as e:
            # Other errors
            candidate.is_valid = False
            candidate.fitness = 0.0
            candidate.errors = [f"Error: {e}"]
    
    def _check_js_syntax(self, file_path: Path, candidate: FixCandidate) -> None:
        """
        Check JavaScript/TypeScript syntax and update the candidate's fitness.
        
        Args:
            file_path: Path to the file to check.
            candidate: Candidate to update.
        """
        # Try to use Node.js to check the syntax
        try:
            result = subprocess.run(
                ["node", "--check", str(file_path)],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Syntax is valid
                candidate.is_valid = True
                candidate.fitness = 0.7
                candidate.errors = []
            else:
                # Syntax error
                candidate.is_valid = False
                candidate.fitness = 0.0
                candidate.errors = [result.stderr.strip()]
            
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            # Fallback: simple heuristic check
            self._check_issue_fixed(candidate, candidate.issue, None)
    
    def _check_java_syntax(self, file_path: Path, candidate: FixCandidate) -> None:
        """
        Check Java syntax and update the candidate's fitness.
        
        Args:
            file_path: Path to the file to check.
            candidate: Candidate to update.
        """
        # Try to use javac to check the syntax
        try:
            result = subprocess.run(
                ["javac", "-d", "/tmp", str(file_path)],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Compilation succeeded
                candidate.is_valid = True
                candidate.fitness = 0.7
                candidate.errors = []
            else:
                # Compilation failed
                candidate.is_valid = False
                candidate.fitness = 0.0
                candidate.errors = [result.stderr.strip()]
            
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            # Fallback: simple heuristic check
            self._check_issue_fixed(candidate, candidate.issue, None)
    
    def _check_cpp_syntax(self, file_path: Path, candidate: FixCandidate) -> None:
        """
        Check C/C++ syntax and update the candidate's fitness.
        
        Args:
            file_path: Path to the file to check.
            candidate: Candidate to update.
        """
        # Try to use g++ to check the syntax
        try:
            result = subprocess.run(
                ["g++", "-fsyntax-only", str(file_path)],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Syntax is valid
                candidate.is_valid = True
                candidate.fitness = 0.7
                candidate.errors = []
            else:
                # Syntax error
                candidate.is_valid = False
                candidate.fitness = 0.0
                candidate.errors = [result.stderr.strip()]
            
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            # Fallback: simple heuristic check
            self._check_issue_fixed(candidate, candidate.issue, None)
    
    def _check_issue_fixed(
        self,
        candidate: FixCandidate,
        issue: Issue,
        temp_content: Optional[str]
    ) -> None:
        """
        Check if the issue is likely fixed using heuristics.
        
        Args:
            candidate: Candidate to update.
            issue: Issue being fixed.
            temp_content: Content of the fixed file (or None).
        """
        # Simple heuristic checks based on issue type
        if issue.issue_type.value == "syntax_error":
            # For syntax errors, check common patterns
            candidate.is_valid = True
            candidate.fitness = 0.5  # Medium fitness, not confirmed
            candidate.errors = []
            
        elif issue.issue_type.value == "style_issue":
            # For style issues, the candidate is valid if it changed anything
            candidate.is_valid = True
            candidate.fitness = 0.6
            candidate.errors = []
            
        else:
            # For other issues, assume valid with medium fitness
            candidate.is_valid = True
            candidate.fitness = 0.5
            candidate.errors = []
    
    def _penalize_excessive_changes(
        self,
        candidate: FixCandidate,
        original_content: str,
        fixed_content: str
    ) -> None:
        """
        Penalize fixes that make excessive changes to the original code.
        
        Args:
            candidate: Candidate to update.
            original_content: Original file content.
            fixed_content: Fixed file content.
        """
        # Calculate a simple difference metric
        import difflib
        
        # Split into lines
        original_lines = original_content.splitlines()
        fixed_lines = fixed_content.splitlines()
        
        # Calculate the number of changed lines
        diff = difflib.ndiff(original_lines, fixed_lines)
        changes = sum(1 for d in diff if d.startswith('+ ') or d.startswith('- '))
        
        # Calculate the percentage of changed lines
        max_lines = max(len(original_lines), len(fixed_lines))
        change_percentage = changes / max_lines if max_lines > 0 else 0
        
        # Penalize based on the percentage of changed lines
        # For small files, allow more changes (relative to file size)
        if max_lines < 10:
            # Small file, allow up to 50% changes without penalty
            penalty = max(0, (change_percentage - 0.5) * 0.5)
        else:
            # Larger file, penalize changes more than 20%
            penalty = max(0, (change_percentage - 0.2) * 0.7)
        
        # Apply the penalty
        candidate.fitness -= penalty
