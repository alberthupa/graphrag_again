"""Pydantic models for entities, relationships, and triplets."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class EntityType(str, Enum):
    """Enumeration of supported entity types."""
    KPI = "KPI"
    TABLE = "Table"
    COLUMN = "Column"
    METRIC = "Metric"
    DATA_SOURCE = "DataSource"
    DOMAIN = "Domain"
    FORMULA = "Formula"
    DEFINITION = "Definition"


class Entity(BaseModel):
    """Base entity model with type, name, description, and confidence."""
    
    id: str = Field(description="Unique identifier for the entity")
    type: EntityType = Field(description="Type of the entity")
    name: str = Field(description="Name of the entity")
    description: Optional[str] = Field(default=None, description="Description of the entity")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score for entity extraction")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Additional entity-specific attributes")
    source_chunk_id: Optional[str] = Field(default=None, description="ID of the chunk this entity was extracted from")
    
    def __hash__(self):
        return hash((self.id, self.type, self.name))


class PredicateType(str, Enum):
    """Enumeration of relationship predicate types."""
    HAS_DEFINITION = "hasDefinition"
    CALCULATED_BY = "calculatedBy"
    BELONGS_TO = "belongsTo"
    CONTAINS = "contains"
    HAS_TYPE = "hasType"
    DEPENDS_ON = "dependsOn"
    DERIVED_FROM = "derivedFrom"
    MEASURES = "measures"
    LOCATED_IN = "locatedIn"


class Relationship(BaseModel):
    """Subject-predicate-object relationship model."""
    
    id: str = Field(description="Unique identifier for the relationship")
    subject_id: str = Field(description="ID of the subject entity")
    predicate: PredicateType = Field(description="Type of relationship")
    object_id: str = Field(description="ID of the object entity")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score for relationship extraction")
    context: Optional[str] = Field(default=None, description="Context in which relationship was identified")
    source_chunk_id: Optional[str] = Field(default=None, description="ID of the chunk this relationship was extracted from")


class Triplet(BaseModel):
    """Final triplet structure with temporal context and metadata."""
    
    id: str = Field(description="Unique identifier for the triplet")
    subject: Entity = Field(description="Subject entity")
    predicate: PredicateType = Field(description="Relationship predicate")
    object: Entity = Field(description="Object entity")
    confidence: float = Field(ge=0.0, le=1.0, description="Overall confidence score for the triplet")
    temporal_context: Optional[datetime] = Field(default=None, description="Temporal context when available")
    source_text: Optional[str] = Field(default=None, description="Original text from which triplet was extracted")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ExtractionResult(BaseModel):
    """Container for entities, relationships, and extraction metadata."""
    
    entities: List[Entity] = Field(description="List of extracted entities")
    relationships: List[Relationship] = Field(description="List of identified relationships")
    triplets: List[Triplet] = Field(description="List of generated triplets")
    extraction_timestamp: datetime = Field(default_factory=datetime.now, description="When extraction was performed")
    source_document: Optional[str] = Field(default=None, description="Source document identifier")
    total_chunks_processed: int = Field(default=0, description="Number of chunks processed")
    extraction_stats: Dict[str, Any] = Field(default_factory=dict, description="Statistics about the extraction process")
    
    def get_entities_by_type(self, entity_type: EntityType) -> List[Entity]:
        """Get all entities of a specific type."""
        return [entity for entity in self.entities if entity.type == entity_type]
    
    def get_relationships_by_predicate(self, predicate: PredicateType) -> List[Relationship]:
        """Get all relationships with a specific predicate."""
        return [rel for rel in self.relationships if rel.predicate == predicate]