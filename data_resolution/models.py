"""Pydantic models for data resolution results and tracking."""

from typing import List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

from entity_extraction.models import Entity, Relationship, PredicateType


class ResolutionActionType(str, Enum):
    """Types of resolution actions that can be taken."""
    MERGE = "merge"
    KEEP_CANONICAL = "keep_canonical"  
    MARK_DUPLICATE = "mark_duplicate"
    CREATE_NEW_RELATIONSHIP = "create_new_relationship"
    CONSOLIDATE_RELATIONSHIPS = "consolidate_relationships"


class EntityResolutionDecision(BaseModel):
    """Records a decision made during entity resolution."""
    
    id: str = Field(description="Unique ID for this resolution decision")
    canonical_entity_id: str = Field(description="ID of the canonical (kept) entity")
    duplicate_entity_ids: List[str] = Field(description="IDs of entities marked as duplicates")
    similarity_score: float = Field(ge=0.0, le=1.0, description="Similarity score that triggered the merge")
    resolution_method: str = Field(description="Method used for resolution (fuzzy_match, acronym_match, etc.)")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in the resolution decision")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional resolution metadata")
    timestamp: datetime = Field(default_factory=datetime.now, description="When resolution was performed")


class RelationshipResolutionDecision(BaseModel):
    """Records a decision made during relationship resolution."""
    
    id: str = Field(description="Unique ID for this resolution decision") 
    action: ResolutionActionType = Field(description="Action taken during resolution")
    canonical_relationship_id: str = Field(description="ID of the canonical (kept) relationship")
    merged_relationship_ids: List[str] = Field(default_factory=list, description="IDs of relationships that were merged")
    consolidated_confidence: float = Field(ge=0.0, le=1.0, description="Final consolidated confidence score")
    consolidation_method: str = Field(description="Method used for consolidation")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional consolidation metadata")
    timestamp: datetime = Field(default_factory=datetime.now, description="When resolution was performed")


class ConnectionDiscovery(BaseModel):
    """Represents a newly discovered potential connection between entities."""
    
    id: str = Field(description="Unique ID for this discovery")
    subject_entity_id: str = Field(description="ID of the subject entity")
    object_entity_id: str = Field(description="ID of the object entity") 
    suggested_predicate: PredicateType = Field(description="Suggested relationship type")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in the suggested connection")
    discovery_method: str = Field(description="Method that discovered this connection")
    supporting_evidence: List[str] = Field(default_factory=list, description="Evidence supporting this connection")
    similarity_features: Dict[str, float] = Field(default_factory=dict, description="Feature similarities that led to discovery")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional discovery metadata")
    timestamp: datetime = Field(default_factory=datetime.now, description="When discovery was made")


class ResolutionStats(BaseModel):
    """Statistics about the resolution process."""
    
    entities_processed: int = Field(description="Total entities processed")
    entities_merged: int = Field(description="Number of entities merged")
    relationships_processed: int = Field(description="Total relationships processed") 
    relationships_consolidated: int = Field(description="Number of relationships consolidated")
    new_connections_discovered: int = Field(description="Number of new connections discovered")
    resolution_duration_seconds: float = Field(description="Time taken for resolution")
    duplicate_entities_removed: int = Field(description="Number of duplicate entities removed")
    
    @property
    def entity_merge_rate(self) -> float:
        """Calculate the rate of entity merging."""
        return self.entities_merged / self.entities_processed if self.entities_processed > 0 else 0.0
    
    @property  
    def relationship_consolidation_rate(self) -> float:
        """Calculate the rate of relationship consolidation."""
        return self.relationships_consolidated / self.relationships_processed if self.relationships_processed > 0 else 0.0


class ResolutionResult(BaseModel):
    """Complete result of a data resolution run."""
    
    run_id: str = Field(description="Unique identifier for this resolution run")
    timestamp: datetime = Field(default_factory=datetime.now, description="When resolution was performed")
    
    # Resolution decisions
    entity_decisions: List[EntityResolutionDecision] = Field(description="All entity resolution decisions made")
    relationship_decisions: List[RelationshipResolutionDecision] = Field(description="All relationship resolution decisions made")
    discovered_connections: List[ConnectionDiscovery] = Field(description="All newly discovered potential connections")
    
    # Final resolved data
    canonical_entities: List[Entity] = Field(description="Final set of canonical entities after resolution")
    consolidated_relationships: List[Relationship] = Field(description="Final set of relationships after consolidation")
    
    # Statistics and metadata
    stats: ResolutionStats = Field(description="Statistics about the resolution process")
    config_used: Dict[str, Any] = Field(default_factory=dict, description="Configuration parameters used")
    source_extraction_run_ids: List[str] = Field(description="Extraction run IDs that were processed")
    
    def get_merged_entity_mapping(self) -> Dict[str, str]:
        """Get a mapping from duplicate entity IDs to their canonical entity IDs."""
        mapping = {}
        for decision in self.entity_decisions:
            for duplicate_id in decision.duplicate_entity_ids:
                mapping[duplicate_id] = decision.canonical_entity_id
        return mapping
    
    def get_discovery_by_method(self, method: str) -> List[ConnectionDiscovery]:
        """Get all discoveries made by a specific method."""
        return [d for d in self.discovered_connections if d.discovery_method == method]
    
    def get_high_confidence_discoveries(self, min_confidence: float = 0.7) -> List[ConnectionDiscovery]:
        """Get all discoveries with confidence above threshold."""
        return [d for d in self.discovered_connections if d.confidence >= min_confidence]