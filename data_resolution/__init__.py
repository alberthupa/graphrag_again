"""
Data resolution package for deduplicating entities and discovering new relationships.

This module provides functionality for:
1. Entity deduplication using fuzzy matching
2. Relationship consolidation and deduplication  
3. Discovery of new potential connections between entities
4. Database integration for resolution tracking

Main components:
- EntityResolver: Handles entity deduplication using fuzzy matching
- RelationshipResolver: Consolidates duplicate relationships
- ConnectionDiscoverer: Finds new potential relationships
- ResolutionOrchestrator: Main pipeline orchestration
"""

from .models import (
    ResolutionResult,
    ResolutionStats,
    EntityResolutionDecision,
    RelationshipResolutionDecision,
    ConnectionDiscovery
)
from .entity_resolver import EntityResolver
from .relationship_resolver import RelationshipResolver  
from .connection_discoverer import ConnectionDiscoverer

__all__ = [
    "ResolutionResult",
    "ResolutionStats",
    "EntityResolutionDecision", 
    "RelationshipResolutionDecision",
    "ConnectionDiscovery",
    "EntityResolver",
    "RelationshipResolver",
    "ConnectionDiscoverer"
]