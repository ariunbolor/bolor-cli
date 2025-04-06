"""
Candidate module for Bolor code repair evolution.

This module provides the base class for fix candidates used in evolutionary algorithms.
"""

import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any, Union

from bolor.agent.models import Issue


class Candidate:
    """
    Base class for evolutionary candidates.
    
    This class serves as the base for all types of candidates that can be evolved
    in the Bolor system, such as code fixes or refactorings.
    """
    
    def __init__(
        self,
        generation: int = 0,
        parent_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        fitness: float = 0.0,
        is_valid: bool = True
    ):
        """
        Initialize a new Candidate instance.
        
        Args:
            generation: Generation number of this candidate.
            parent_ids: List of parent IDs if this candidate is a result of reproduction.
            metadata: Additional metadata for the candidate.
            fitness: Fitness score of the candidate.
            is_valid: Whether the candidate is valid.
        """
        self.id = uuid.uuid4().hex
        self.generation = generation
        self.parent_ids = parent_ids or []
        self.metadata = metadata or {}
        self.fitness = fitness
        self.is_valid = is_valid
        self.errors: List[str] = []
    
    def mutate(self) -> 'Candidate':
        """
        Mutate this candidate to create a new variant.
        
        Returns:
            A new mutated candidate.
        """
        # Base implementation just creates a clone
        new_candidate = Candidate(
            generation=self.generation + 1,
            parent_ids=[self.id],
            metadata=self.metadata.copy(),
            fitness=0.0  # Reset fitness for the new candidate
        )
        
        return new_candidate
    
    def crossover(self, other: 'Candidate') -> 'Candidate':
        """
        Perform crossover with another candidate.
        
        Args:
            other: Other candidate to crossover with.
            
        Returns:
            A new candidate resulting from the crossover.
        """
        # Base implementation just creates a clone with combined parents
        new_candidate = Candidate(
            generation=max(self.generation, other.generation) + 1,
            parent_ids=[self.id, other.id],
            metadata={**self.metadata, **other.metadata},
            fitness=0.0  # Reset fitness for the new candidate
        )
        
        return new_candidate
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the candidate to a dictionary representation."""
        return {
            "id": self.id,
            "generation": self.generation,
            "parent_ids": self.parent_ids,
            "metadata": self.metadata,
            "fitness": self.fitness,
            "is_valid": self.is_valid,
            "errors": self.errors
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Candidate':
        """Create a candidate from a dictionary representation."""
        candidate = cls(
            generation=data.get("generation", 0),
            parent_ids=data.get("parent_ids", []),
            metadata=data.get("metadata", {}),
            fitness=data.get("fitness", 0.0),
            is_valid=data.get("is_valid", True)
        )
        
        candidate.id = data.get("id", candidate.id)
        candidate.errors = data.get("errors", [])
        
        return candidate


class FixCandidate(Candidate):
    """
    A candidate for a code fix.
    
    This class represents a potential fix for a code issue.
    """
    
    def __init__(
        self,
        issue: Issue,
        modified_code: str,
        generation: int = 0,
        parent_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        fitness: float = 0.0,
        is_valid: bool = True
    ):
        """
        Initialize a new FixCandidate instance.
        
        Args:
            issue: The issue this candidate attempts to fix.
            modified_code: The modified code that represents the fix.
            generation: Generation number of this candidate.
            parent_ids: List of parent IDs if this candidate is a result of reproduction.
            metadata: Additional metadata for the candidate.
            fitness: Fitness score of the candidate.
            is_valid: Whether the candidate is valid.
        """
        super().__init__(generation, parent_ids, metadata, fitness, is_valid)
        self.issue = issue
        self.modified_code = modified_code
    
    def mutate(self) -> 'FixCandidate':
        """
        Mutate this fix candidate to create a new variant.
        
        Returns:
            A new mutated fix candidate.
        """
        # Create a new fix candidate with the same issue and code
        new_candidate = FixCandidate(
            issue=self.issue,
            modified_code=self.modified_code,
            generation=self.generation + 1,
            parent_ids=[self.id],
            metadata=self.metadata.copy()
        )
        
        return new_candidate
    
    def crossover(self, other: 'FixCandidate') -> 'FixCandidate':
        """
        Perform crossover with another fix candidate.
        
        Args:
            other: Other fix candidate to crossover with.
            
        Returns:
            A new fix candidate resulting from the crossover.
        """
        # Simple implementation: use the original code
        new_candidate = FixCandidate(
            issue=self.issue,
            modified_code=self.modified_code,
            generation=max(self.generation, other.generation) + 1,
            parent_ids=[self.id, other.id],
            metadata={**self.metadata, **other.metadata}
        )
        
        return new_candidate
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the fix candidate to a dictionary representation."""
        data = super().to_dict()
        data.update({
            "issue": self.issue.to_dict(),
            "modified_code": self.modified_code
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FixCandidate':
        """Create a fix candidate from a dictionary representation."""
        from bolor.agent.models import Issue  # Import here to avoid circular imports
        
        issue = Issue.from_dict(data["issue"])
        
        candidate = cls(
            issue=issue,
            modified_code=data["modified_code"],
            generation=data.get("generation", 0),
            parent_ids=data.get("parent_ids", []),
            metadata=data.get("metadata", {}),
            fitness=data.get("fitness", 0.0),
            is_valid=data.get("is_valid", True)
        )
        
        candidate.id = data.get("id", candidate.id)
        candidate.errors = data.get("errors", [])
        
        return candidate
