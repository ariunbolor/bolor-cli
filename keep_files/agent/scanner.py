"""
Scanner module for Bolor code repair.

This module provides functionality for scanning codebases to detect issues
that may need to be fixed.
"""

import os
import ast
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any, Union

from bolor.utils.config import Config
from bolor.agent.models import Issue, IssueType, DeploymentIssue


class Scanner:
    """
    Scanner class for detecting code issues.
    
    This class provides methods for scanning codebases to detect issues
    that may need to be fixed by Bolor.
    """
    
    def __init__(self, config: Config):
        """
        Initialize a new Scanner instance.
        
        Args:
            config: Configuration object containing scanner settings.
        """
        self.config = config
        self.verbose = config.get("verbose", False)
        
        # Get file extension filters from config
        self.file_extensions = set(config.get("scanner.file_extensions", [
            ".py", ".js", ".ts", ".java", ".c", ".cpp", ".h", ".hpp"
        ]))
        
        # Get exclude patterns from config
        self.exclude_patterns = config.get("scanner.exclude_patterns", [
            "__pycache__", "node_modules", ".git", "venv", "env", "build", "dist"
        ])
        
        # Set maximum file size (in MB) to scan
        self.max_file_size_mb = config.get("scanner.max_file_size_mb", 10)
    
    def scan_directory(self, directory: Path) -> List[Issue]:
        """
        Scan a directory recursively for code issues.
        
        Args:
            directory: Path to the directory to scan.
            
        Returns:
            List of detected issues.
        """
        issues = []
        
        if self.verbose:
            print(f"Scanning directory: {directory}")
        
        for root, dirs, files in os.walk(directory):
            # Skip directories that match exclude patterns
            dirs[:] = [d for d in dirs if not self._should_exclude(d)]
            
            for file in files:
                file_path = Path(os.path.join(root, file))
                
                # Skip files that don't match extensions or should be excluded
                if not self._should_scan_file(file_path):
                    continue
                
                # Scan the file for issues
                try:
                    file_issues = self.scan_file(file_path)
                    issues.extend(file_issues)
                    
                    if self.verbose and file_issues:
                        print(f"Found {len(file_issues)} issues in {file_path}")
                        
                except Exception as e:
                    if self.verbose:
                        print(f"Error scanning file {file_path}: {str(e)}")
        
        return issues
    
    def scan_file(self, file_path: Path) -> List[Issue]:
        """
        Scan a single file for code issues.
        
        Args:
            file_path: Path to the file to scan.
            
        Returns:
            List of detected issues.
        """
        if self.verbose:
            print(f"Scanning file: {file_path}")
        
        # Check file size
        if not self._check_file_size(file_path):
            if self.verbose:
                print(f"Skipping large file: {file_path}")
            return []
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        # Dispatch to appropriate scanner based on file extension
        issues = []
        ext = file_path.suffix.lower()
        
        if ext == '.py':
            issues.extend(self._scan_python_file(file_path, content))
        elif ext in ['.js', '.ts']:
            issues.extend(self._scan_javascript_file(file_path, content))
        elif ext in ['.java']:
            issues.extend(self._scan_java_file(file_path, content))
        elif ext in ['.c', '.cpp', '.h', '.hpp']:
            issues.extend(self._scan_cpp_file(file_path, content))
        
        # Generic checks that apply to all file types
        issues.extend(self._scan_generic(file_path, content))
        
        return issues
    
    def scan_ci_config(self, project_path: Path) -> List[DeploymentIssue]:
        """
        Scan CI/CD configuration files for deployment issues.
        
        Args:
            project_path: Path to the project root.
            
        Returns:
            List of detected deployment issues.
        """
        issues = []
        
        # Check for GitHub Actions workflows
        github_actions_dir = project_path / '.github' / 'workflows'
        if github_actions_dir.exists():
            issues.extend(self._scan_github_actions(github_actions_dir))
        
        # Check for GitLab CI configuration
        gitlab_ci_file = project_path / '.gitlab-ci.yml'
        if gitlab_ci_file.exists():
            issues.extend(self._scan_gitlab_ci(gitlab_ci_file))
        
        # Check for Jenkins configuration
        jenkins_file = project_path / 'Jenkinsfile'
        if jenkins_file.exists():
            issues.extend(self._scan_jenkins(jenkins_file))
        
        # Check for Travis CI configuration
        travis_file = project_path / '.travis.yml'
        if travis_file.exists():
            issues.extend(self._scan_travis_ci(travis_file))
        
        # Check for Circle CI configuration
        circle_ci_file = project_path / '.circleci' / 'config.yml'
        if circle_ci_file.exists():
            issues.extend(self._scan_circle_ci(circle_ci_file))
        
        # Check for Docker files
        docker_file = project_path / 'Dockerfile'
        if docker_file.exists():
            issues.extend(self._scan_docker(docker_file))
        
        # Check for Kubernetes manifests
        k8s_dir = project_path / 'k8s'
        if k8s_dir.exists() and k8s_dir.is_dir():
            issues.extend(self._scan_kubernetes(k8s_dir))
        
        return issues
    
    def _should_exclude(self, path: str) -> bool:
        """
        Check if a path should be excluded from scanning.
        
        Args:
            path: Path to check.
            
        Returns:
            True if the path should be excluded, False otherwise.
        """
        for pattern in self.exclude_patterns:
            if re.search(pattern, path):
                return True
        return False
    
    def _should_scan_file(self, file_path: Path) -> bool:
        """
        Check if a file should be scanned.
        
        Args:
            file_path: Path to the file to check.
            
        Returns:
            True if the file should be scanned, False otherwise.
        """
        # Check if file exists and is a regular file
        if not file_path.exists() or not file_path.is_file():
            return False
        
        # Check if file extension is supported
        if file_path.suffix.lower() not in self.file_extensions:
            return False
        
        # Check if file path contains excluded patterns
        if self._should_exclude(str(file_path)):
            return False
        
        return True
    
    def _check_file_size(self, file_path: Path) -> bool:
        """
        Check if a file's size is within limits.
        
        Args:
            file_path: Path to the file to check.
            
        Returns:
            True if the file size is within limits, False otherwise.
        """
        max_size_bytes = self.max_file_size_mb * 1024 * 1024
        return os.path.getsize(file_path) <= max_size_bytes
    
    def _scan_python_file(self, file_path: Path, content: str) -> List[Issue]:
        """
        Scan a Python file for issues.
        
        Args:
            file_path: Path to the file to scan.
            content: Content of the file.
            
        Returns:
            List of detected issues.
        """
        issues = []
        
        # Check for syntax errors
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            issues.append(Issue(
                file_path=file_path,
                issue_type=IssueType.SYNTAX_ERROR,
                description=f"Syntax error: {str(e)}",
                line_number=e.lineno,
                column_number=e.offset,
                code_snippet=content.splitlines()[e.lineno - 1] if e.lineno and e.lineno <= len(content.splitlines()) else None
            ))
            return issues  # Return early, can't analyze code with syntax errors
        
        # Check for various code smells and issues using AST
        issues.extend(self._analyze_python_ast(file_path, content, tree))
        
        # Check for common security vulnerabilities
        issues.extend(self._check_python_security(file_path, content))
        
        # Check for performance issues
        issues.extend(self._check_python_performance(file_path, content, tree))
        
        return issues
    
    def _analyze_python_ast(self, file_path: Path, content: str, tree: ast.AST) -> List[Issue]:
        """
        Analyze a Python AST for issues.
        
        Args:
            file_path: Path to the file being analyzed.
            content: Content of the file.
            tree: AST of the Python file.
            
        Returns:
            List of detected issues.
        """
        issues = []
        
        # Define a visitor class to find issues in the AST
        class IssueVisitor(ast.NodeVisitor):
            def __init__(self, scanner, file_path, content):
                self.scanner = scanner
                self.file_path = file_path
                self.content = content
                self.lines = content.splitlines()
                self.issues = []
            
            def visit_Try(self, node):
                # Check for overly broad except clauses
                for handler in node.handlers:
                    if handler.type is None or handler.type.id == 'Exception':
                        # Get line number and code snippet
                        line_number = handler.lineno
                        try:
                            code_snippet = self.lines[line_number - 1]
                        except IndexError:
                            code_snippet = None
                        
                        # Create issue
                        self.issues.append(Issue(
                            file_path=self.file_path,
                            issue_type=IssueType.CODE_SMELL,
                            description="Overly broad exception handling (consider catching specific exceptions)",
                            line_number=line_number,
                            code_snippet=code_snippet
                        ))
                
                # Continue recursively visiting child nodes
                self.generic_visit(node)
            
            def visit_Compare(self, node):
                # Check for comparisons with empty literals (better to use "is None" or len() == 0)
                # For now, we're only looking for simple comparisons with empty lists or dictionaries
                for i, op in enumerate(node.ops):
                    if isinstance(op, (ast.Eq, ast.NotEq)):
                        comparator = node.comparators[i]
                        if (isinstance(comparator, ast.List) and len(comparator.elts) == 0) or \
                           (isinstance(comparator, ast.Dict) and len(comparator.keys) == 0):
                            line_number = node.lineno
                            try:
                                code_snippet = self.lines[line_number - 1]
                            except IndexError:
                                code_snippet = None
                            
                            # Create issue
                            self.issues.append(Issue(
                                file_path=self.file_path,
                                issue_type=IssueType.CODE_SMELL,
                                description="Comparison with empty literal (consider using len() or checking explicitly)",
                                line_number=line_number,
                                code_snippet=code_snippet
                            ))
                
                # Continue recursively visiting child nodes
                self.generic_visit(node)
        
        # Create and run the visitor
        visitor = IssueVisitor(self, file_path, content)
        visitor.visit(tree)
        issues.extend(visitor.issues)
        
        return issues
    
    def _check_python_security(self, file_path: Path, content: str) -> List[Issue]:
        """
        Check a Python file for security vulnerabilities.
        
        Args:
            file_path: Path to the file being analyzed.
            content: Content of the file.
            
        Returns:
            List of detected issues.
        """
        issues = []
        lines = content.splitlines()
        
        # Check for potentially insecure patterns
        patterns = [
            (r"eval\s*\(", "Use of eval() can be dangerous if input is not trusted", IssueType.SECURITY_VULNERABILITY),
            (r"exec\s*\(", "Use of exec() can be dangerous if input is not trusted", IssueType.SECURITY_VULNERABILITY),
            (r"os\.system\s*\(", "Use of os.system() can be dangerous if input is not trusted", IssueType.SECURITY_VULNERABILITY),
            (r"subprocess\.call\s*\(.*shell\s*=\s*True", "Use of shell=True can be dangerous if input is not trusted", IssueType.SECURITY_VULNERABILITY),
            (r"subprocess\.Popen\s*\(.*shell\s*=\s*True", "Use of shell=True can be dangerous if input is not trusted", IssueType.SECURITY_VULNERABILITY),
            (r"pickle\.loads?\s*\(", "Unpickling untrusted data can be dangerous", IssueType.SECURITY_VULNERABILITY),
            (r"yaml\.load\s*\((?!.*Loader=yaml\.SafeLoader)", "Use yaml.safe_load() instead of yaml.load() for untrusted input", IssueType.SECURITY_VULNERABILITY),
        ]
        
        for i, line in enumerate(lines):
            for pattern, description, issue_type in patterns:
                if re.search(pattern, line):
                    issues.append(Issue(
                        file_path=file_path,
                        issue_type=issue_type,
                        description=description,
                        line_number=i + 1,
                        code_snippet=line
                    ))
        
        return issues
    
    def _check_python_performance(self, file_path: Path, content: str, tree: ast.AST) -> List[Issue]:
        """
        Check a Python file for performance issues.
        
        Args:
            file_path: Path to the file being analyzed.
            content: Content of the file.
            tree: AST of the Python file.
            
        Returns:
            List of detected issues.
        """
        issues = []
        
        # Define a visitor class to find performance issues in the AST
        class PerformanceVisitor(ast.NodeVisitor):
            def __init__(self, scanner, file_path, content):
                self.scanner = scanner
                self.file_path = file_path
                self.content = content
                self.lines = content.splitlines()
                self.issues = []
                self.loops = []
            
            def visit_For(self, node):
                # Track loop nesting level
                self.loops.append(node)
                self.generic_visit(node)
                self.loops.pop()
            
            def visit_While(self, node):
                # Track loop nesting level
                self.loops.append(node)
                self.generic_visit(node)
                self.loops.pop()
            
            def visit_ListComp(self, node):
                # Check if list comprehension contains another comprehension
                for subnode in ast.walk(node):
                    if subnode != node and isinstance(subnode, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                        line_number = node.lineno
                        try:
                            code_snippet = self.lines[line_number - 1]
                        except IndexError:
                            code_snippet = None
                        
                        # Create issue
                        self.issues.append(Issue(
                            file_path=self.file_path,
                            issue_type=IssueType.PERFORMANCE_ISSUE,
                            description="Nested comprehension can be inefficient",
                            line_number=line_number,
                            code_snippet=code_snippet
                        ))
                        break
                
                self.generic_visit(node)
        
        # Create and run the visitor
        visitor = PerformanceVisitor(self, file_path, content)
        visitor.visit(tree)
        issues.extend(visitor.issues)
        
        return issues
    
    def _scan_javascript_file(self, file_path: Path, content: str) -> List[Issue]:
        """
        Scan a JavaScript/TypeScript file for issues.
        
        Args:
            file_path: Path to the file to scan.
            content: Content of the file.
            
        Returns:
            List of detected issues.
        """
        issues = []
        lines = content.splitlines()
        
        # Simple pattern matching for common issues
        # In a real implementation, consider using a JavaScript parser for deeper analysis
        patterns = [
            (r"console\.log\s*\(", "Console logging should be removed in production code", IssueType.CODE_SMELL),
            (r"eval\s*\(", "Use of eval() can be dangerous if input is not trusted", IssueType.SECURITY_VULNERABILITY),
            (r"innerHTML\s*=", "Using innerHTML can lead to XSS vulnerabilities", IssueType.SECURITY_VULNERABILITY),
            (r"setTimeout\s*\(\s*[\"']", "Passing strings to setTimeout() or setInterval() uses eval() internally", IssueType.SECURITY_VULNERABILITY),
            (r"setInterval\s*\(\s*[\"']", "Passing strings to setTimeout() or setInterval() uses eval() internally", IssueType.SECURITY_VULNERABILITY),
        ]
        
        for i, line in enumerate(lines):
            for pattern, description, issue_type in patterns:
                if re.search(pattern, line):
                    issues.append(Issue(
                        file_path=file_path,
                        issue_type=issue_type,
                        description=description,
                        line_number=i + 1,
                        code_snippet=line
                    ))
        
        return issues
    
    def _scan_java_file(self, file_path: Path, content: str) -> List[Issue]:
        """
        Scan a Java file for issues.
        
        Args:
            file_path: Path to the file to scan.
            content: Content of the file.
            
        Returns:
            List of detected issues.
        """
        issues = []
        lines = content.splitlines()
        
        # Simple pattern matching for common issues
        # In a real implementation, consider using a Java parser for deeper analysis
        patterns = [
            (r"System\.out\.println", "System.out.println should be replaced with proper logging", IssueType.CODE_SMELL),
            (r"e\.printStackTrace\(\)", "printStackTrace() should be replaced with proper logging", IssueType.CODE_SMELL),
            (r"catch\s*\(\s*Exception\s+", "Overly broad exception handling", IssueType.CODE_SMELL),
            (r"Runtime\.getRuntime\(\)\.exec\s*\(", "Runtime.exec() can be dangerous if input is not trusted", IssueType.SECURITY_VULNERABILITY),
        ]
        
        for i, line in enumerate(lines):
            for pattern, description, issue_type in patterns:
                if re.search(pattern, line):
                    issues.append(Issue(
                        file_path=file_path,
                        issue_type=issue_type,
                        description=description,
                        line_number=i + 1,
                        code_snippet=line
                    ))
        
        return issues
    
    def _scan_cpp_file(self, file_path: Path, content: str) -> List[Issue]:
        """
        Scan a C/C++ file for issues.
        
        Args:
            file_path: Path to the file to scan.
            content: Content of the file.
            
        Returns:
            List of detected issues.
        """
        issues = []
        lines = content.splitlines()
        
        # Simple pattern matching for common issues
        # In a real implementation, consider using a C/C++ parser for deeper analysis
        patterns = [
            (r"strcpy\s*\(", "strcpy() is unsafe, consider using strncpy() or std::string", IssueType.SECURITY_VULNERABILITY),
            (r"strcat\s*\(", "strcat() is unsafe, consider using strncat() or std::string", IssueType.SECURITY_VULNERABILITY),
            (r"gets\s*\(", "gets() is unsafe and deprecated, use fgets() instead", IssueType.SECURITY_VULNERABILITY),
            (r"malloc\s*\([^)]*\);(?![^;]*free)", "Potential memory leak (malloc without free)", IssueType.CODE_SMELL),
            (r"printf\s*\([^)]*%s", "Format string vulnerability if user input is used", IssueType.SECURITY_VULNERABILITY),
        ]
        
        for i, line in enumerate(lines):
            for pattern, description, issue_type in patterns:
                if re.search(pattern, line):
                    issues.append(Issue(
                        file_path=file_path,
                        issue_type=issue_type,
                        description=description,
                        line_number=i + 1,
                        code_snippet=line
                    ))
        
        return issues
    
    def _scan_generic(self, file_path: Path, content: str) -> List[Issue]:
        """
        Perform generic scans that apply to all file types.
        
        Args:
            file_path: Path to the file to scan.
            content: Content of the file.
            
        Returns:
            List of detected issues.
        """
        issues = []
        lines = content.splitlines()
        
        # Check for TODO/FIXME comments
        for i, line in enumerate(lines):
            # Look for TODO, FIXME, or similar comments
            if re.search(r'(TODO|FIXME|XXX|BUG|HACK):', line, re.IGNORECASE):
                issues.append(Issue(
                    file_path=file_path,
                    issue_type=IssueType.CODE_SMELL,
                    description="Code contains TODO/FIXME comment",
                    line_number=i + 1,
                    code_snippet=line
                ))
        
        # Check for extremely long lines
        max_line_length = 120
        for i, line in enumerate(lines):
            if len(line) > max_line_length:
                issues.append(Issue(
                    file_path=file_path,
                    issue_type=IssueType.STYLE_ISSUE,
                    description=f"Line exceeds {max_line_length} characters",
                    line_number=i + 1,
                    code_snippet=line
                ))
        
        # Check for trailing whitespace
        for i, line in enumerate(lines):
            if line.rstrip() != line:
                issues.append(Issue(
                    file_path=file_path,
                    issue_type=IssueType.STYLE_ISSUE,
                    description="Line contains trailing whitespace",
                    line_number=i + 1,
                    code_snippet=line
                ))
        
        return issues
    
    def _scan_github_actions(self, workflows_dir: Path) -> List[DeploymentIssue]:
        """
        Scan GitHub Actions workflow files for deployment issues.
        
        Args:
            workflows_dir: Path to the .github/workflows directory.
            
        Returns:
            List of detected deployment issues.
        """
        issues = []
        
        # Iterate through workflow files
        for file_path in workflows_dir.glob('*.yml'):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                
                # Parse YAML file
                try:
                    import yaml
                    workflow = yaml.safe_load(content)
                    
                    # Check for use of deprecated Node.js versions
                    if 'jobs' in workflow:
                        for job_name, job_config in workflow['jobs'].items():
                            if 'steps' in job_config:
                                for step in job_config['steps']:
                                    # Check for setup-node action
                                    if 'uses' in step and 'actions/setup-node@' in step['uses']:
                                        if 'with' in step and 'node-version' in step['with']:
                                            node_version = step['with']['node-version']
                                            if node_version in ['10', '12', '14']:
                                                issues.append(DeploymentIssue(
                                                    file_path=file_path,
                                                    description=f"Using deprecated Node.js version {node_version}",
                                                    details=f"Node.js version {node_version} is deprecated. Consider upgrading to a supported version.",
                                                    suggestions=[f"Upgrade to Node.js 16 or higher"]
                                                ))
                    
                    # Check for hardcoded secrets
                    hardcoded_secrets = self._find_hardcoded_secrets(content)
                    if hardcoded_secrets:
                        issues.append(DeploymentIssue(
                            file_path=file_path,
                            description="Potential hardcoded secrets in workflow file",
                            details="Workflow file may contain hardcoded secrets, which is a security risk.",
                            severity="critical",
                            suggestions=["Use GitHub Secrets for sensitive data"]
                        ))
                
                except (yaml.YAMLError, ImportError):
                    # If YAML parsing fails or yaml module is not available
                    issues.append(DeploymentIssue(
                        file_path=file_path,
                        description="Could not parse GitHub Actions workflow file",
                        details="The file could not be parsed as YAML. Check for syntax errors.",
                        severity="warning"
                    ))
            
            except Exception as e:
                # Handle file reading errors
                issues.append(DeploymentIssue(
                    file_path=file_path,
                    description=f"Error reading GitHub Actions workflow file: {str(e)}",
                    severity="warning"
                ))
        
        return issues
    
    def _scan_gitlab_ci(self, file_path: Path) -> List[DeploymentIssue]:
        """
        Scan GitLab CI configuration file for deployment issues.
        
        Args:
            file_path: Path to the .gitlab-ci.yml file.
            
        Returns:
            List of detected deployment issues.
        """
        issues = []
        
        # This is a placeholder implementation
        # A real implementation would parse the YAML and check for common issues
        issues.append(DeploymentIssue(
            file_path=file_path,
            description="GitLab CI scanning is not yet fully implemented",
            details="The basic GitLab CI scanner is a placeholder and may not detect all issues.",
            severity="info"
        ))
        
        return issues
    
    def _scan_jenkins(self, file_path: Path) -> List[DeploymentIssue]:
        """
        Scan Jenkinsfile for deployment issues.
        
        Args:
            file_path: Path to the Jenkinsfile.
            
        Returns:
            List of detected deployment issues.
        """
        issues = []
        
        # This is a placeholder implementation
        # A real implementation would parse the Jenkinsfile and check for common issues
        issues.append(DeploymentIssue(
            file_path=file_path,
            description="Jenkins scanning is not yet fully implemented",
            details="The basic Jenkins scanner is a placeholder and may not detect all issues.",
            severity="info"
        ))
        
        return issues
    
    def _scan_travis_ci(self, file_path: Path) -> List[DeploymentIssue]:
        """
        Scan Travis CI configuration file for deployment issues.
        
        Args:
            file_path: Path to the .travis.yml file.
            
        Returns:
            List of detected deployment issues.
        """
        issues = []
        
        # This is a placeholder implementation
        # A real implementation would parse the YAML and check for common issues
        issues.append(DeploymentIssue(
            file_path=file_path,
            description="Travis CI scanning is not yet fully implemented",
            details="The basic Travis CI scanner is a placeholder and may not detect all issues.",
            severity="info"
        ))
        
        return issues
    
    def _scan_circle_ci(self, file_path: Path) -> List[DeploymentIssue]:
        """
        Scan Circle CI configuration file for deployment issues.
        
        Args:
            file_path: Path to the .circleci/config.yml file.
            
        Returns:
            List of detected deployment issues.
        """
        issues = []
        
        # This is a placeholder implementation
        # A real implementation would parse the YAML and check for common issues
        issues.append(DeploymentIssue(
            file_path=file_path,
            description="Circle CI scanning is not yet fully implemented",
            details="The basic Circle CI scanner is a placeholder and may not detect all issues.",
            severity="info"
        ))
        
        return issues
    
    def _scan_docker(self, file_path: Path) -> List[DeploymentIssue]:
        """
        Scan Dockerfile for deployment issues.
        
        Args:
            file_path: Path to the Dockerfile.
            
        Returns:
            List of detected deployment issues.
        """
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            lines = content.splitlines()
            
            # Check for deprecated or insecure patterns
            for i, line in enumerate(lines):
                # Check for use of latest tag
                if re.search(r'FROM\s+\S+:latest', line, re.IGNORECASE):
                    issues.append(DeploymentIssue(
                        file_path=file_path,
                        description="Using 'latest' tag in FROM instruction",
                        details="Using the 'latest' tag can lead to unexpected changes when the image is updated.",
                        suggestions=["Use a specific version tag for more predictable builds"]
                    ))
                
                # Check for use of ADD instead of COPY
                if line.strip().startswith('ADD ') and not re.search(r'ADD\s+https?://', line):
                    issues.append(DeploymentIssue(
                        file_path=file_path,
                        description="Using ADD instead of COPY",
                        details="COPY is preferred over ADD for simple file copying as it's more transparent.",
                        suggestions=["Use COPY instead of ADD for simple file copying"]
                    ))
                
                # Check for apt-get update without upgrade
                if 'apt-get update' in line and 'apt-get upgrade' not in line and 'apt-get install' in line:
                    issues.append(DeploymentIssue(
                        file_path=file_path,
                        description="apt-get update without upgrade",
                        details="Running apt-get update without upgrade may leave security vulnerabilities.",
                        suggestions=["Consider using apt-get upgrade or apt-get dist-upgrade"]
                    ))
        
        except Exception as e:
            # Handle file reading errors
            issues.append(DeploymentIssue(
                file_path=file_path,
                description=f"Error scanning Dockerfile: {str(e)}",
                severity="warning"
            ))
        
        return issues
    
    def _scan_kubernetes(self, k8s_dir: Path) -> List[DeploymentIssue]:
        """
        Scan Kubernetes manifest files for deployment issues.
        
        Args:
            k8s_dir: Path to the directory containing Kubernetes manifests.
            
        Returns:
            List of detected deployment issues.
        """
        issues = []
        
        # Find all YAML files in the directory
        for file_path in k8s_dir.glob('**/*.{yml,yaml}'):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                
                # Parse YAML file
                try:
                    import yaml
                    manifest = yaml.safe_load(content)
                    
                    # Check for missing resource limits
                    if isinstance(manifest, dict) and manifest.get('kind') in ['Deployment', 'StatefulSet', 'DaemonSet']:
                        containers = []
                        if 'spec' in manifest and 'template' in manifest['spec'] and 'spec' in manifest['spec']['template'] and 'containers' in manifest['spec']['template']['spec']:
                            containers = manifest['spec']['template']['spec']['containers']
                        
                        for container in containers:
                            if 'resources' not in container or 'limits' not in container.get('resources', {}):
                                issues.append(DeploymentIssue(
                                    file_path=file_path,
                                    description=f"Missing resource limits for container {container.get('name', 'unnamed')}",
                                    details="Containers without resource limits can consume excessive resources and affect cluster stability.",
                                    suggestions=["Add resource limits (CPU and memory) to all containers"]
                                ))
                            
                            if container.get('imagePullPolicy') == 'Always':
                                issues.append(DeploymentIssue(
                                    file_path=file_path,
                                    description=f"Container {container.get('name', 'unnamed')} uses imagePullPolicy: Always",
                                    details="Using imagePullPolicy: Always can cause unnecessary network traffic and potential rate limiting.",
                                    suggestions=["Consider using imagePullPolicy: IfNotPresent for stable releases"]
                                ))
                    
                    # Check for missing health checks
                    if isinstance(manifest, dict) and manifest.get('kind') in ['Deployment', 'StatefulSet']:
                        containers = []
                        if 'spec' in manifest and 'template' in manifest['spec'] and 'spec' in manifest['spec']['template'] and 'containers' in manifest['spec']['template']['spec']:
                            containers = manifest['spec']['template']['spec']['containers']
                        
                        for container in containers:
                            if 'livenessProbe' not in container and 'readinessProbe' not in container:
                                issues.append(DeploymentIssue(
                                    file_path=file_path,
                                    description=f"Missing health checks for container {container.get('name', 'unnamed')}",
                                    details="Containers without health checks may not be properly managed by Kubernetes.",
                                    suggestions=["Add livenessProbe and readinessProbe to ensure proper container health management"]
                                ))
                
                except (yaml.YAMLError, ImportError):
                    # If YAML parsing fails or yaml module is not available
                    issues.append(DeploymentIssue(
                        file_path=file_path,
                        description="Could not parse Kubernetes manifest file",
                        details="The file could not be parsed as YAML. Check for syntax errors.",
                        severity="warning"
                    ))
            
            except Exception as e:
                # Handle file reading errors
                issues.append(DeploymentIssue(
                    file_path=file_path,
                    description=f"Error reading Kubernetes manifest file: {str(e)}",
                    severity="warning"
                ))
        
        return issues
    
    def _find_hardcoded_secrets(self, content: str) -> List[str]:
        """
        Find potential hardcoded secrets in the content.
        
        Args:
            content: Content to search for secrets.
            
        Returns:
            List of found potential secrets.
        """
        secrets = []
        
        # Look for potential API keys, tokens, and passwords
        patterns = [
            r'(?:api|access|secret|private)_?key\s*[=:]\s*["\'`]([^"\'`]+)["\'`]',
            r'(?:auth|bearer|jwt)_?token\s*[=:]\s*["\'`]([^"\'`]+)["\'`]',
            r'password\s*[=:]\s*["\'`]([^"\'`]{8,})["\'`]',
            r'-----BEGIN [A-Z ]+ PRIVATE KEY-----',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            secrets.extend(matches)
        
        return secrets
