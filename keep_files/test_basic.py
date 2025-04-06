"""
Basic tests for Bolor functionality.
"""

import os
import sys
import unittest
from pathlib import Path

# Add the parent directory to the path to import bolor
sys.path.insert(0, str(Path(__file__).parent.parent))

from bolor.utils.config import Config
from bolor.agent.models import Issue, IssueType


class TestConfig(unittest.TestCase):
    """Test the Config class."""
    
    def test_config_basic(self):
        """Test basic configuration functionality."""
        config = Config()
        config.set("test_key", "test_value")
        self.assertEqual(config.get("test_key"), "test_value")
    
    def test_config_nested(self):
        """Test nested configuration functionality."""
        config = Config()
        config.set("nested.key", "nested_value")
        self.assertEqual(config.get("nested.key"), "nested_value")
    
    def test_config_default(self):
        """Test default values."""
        config = Config()
        self.assertEqual(config.get("nonexistent_key", "default"), "default")


class TestIssue(unittest.TestCase):
    """Test the Issue class."""
    
    def test_issue_creation(self):
        """Test creating an issue."""
        issue = Issue(
            file_path=Path("test.py"),
            issue_type=IssueType.SYNTAX_ERROR,
            description="Test issue",
            line_number=10
        )
        self.assertEqual(issue.file_path, Path("test.py"))
        self.assertEqual(issue.issue_type, IssueType.SYNTAX_ERROR)
        self.assertEqual(issue.description, "Test issue")
        self.assertEqual(issue.line_number, 10)
    
    def test_issue_serialization(self):
        """Test issue serialization and deserialization."""
        original = Issue(
            file_path=Path("test.py"),
            issue_type=IssueType.SYNTAX_ERROR,
            description="Test issue",
            line_number=10
        )
        
        # Convert to dict and back
        data = original.to_dict()
        reconstructed = Issue.from_dict(data)
        
        self.assertEqual(str(reconstructed.file_path), str(original.file_path))
        self.assertEqual(reconstructed.issue_type, original.issue_type)
        self.assertEqual(reconstructed.description, original.description)
        self.assertEqual(reconstructed.line_number, original.line_number)


if __name__ == "__main__":
    unittest.main()
