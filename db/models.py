"""Database models that map between entity extraction models and database schema."""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import uuid

from entity_extraction.models import (
    Entity, Relationship, Triplet, ExtractionResult,
    EntityType, PredicateType
)
from .schema import ExtractionRun, EntityDB, RelationshipDB, TripletDB


class DatabaseExtractionRun(BaseModel):
    """Pydantic model for database extraction run."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_chunks_processed: int = 0
    source_document: Optional[str] = None
    extraction_stats: Dict[str, Any] = Field(default_factory=dict)
    config_used: Dict[str, Any] = Field(default_factory=dict)


class DatabaseEntity(BaseModel):
    """Pydantic model for database entity."""
    id: str
    extraction_run_id: str
    type: str
    name: str
    description: Optional[str] = None
    confidence: float
    attributes: Dict[str, Any] = Field(default_factory=dict)
    source_chunk_id: Optional[str] = None
    
    @classmethod
    def from_extraction_entity(cls, entity: Entity, extraction_run_id: str) -> "DatabaseEntity":
        """Convert extraction entity to database entity."""
        return cls(
            id=entity.id,
            extraction_run_id=extraction_run_id,
            type=entity.type.value,
            name=entity.name,
            description=entity.description,
            confidence=entity.confidence,
            attributes=entity.attributes,
            source_chunk_id=entity.source_chunk_id
        )
    
    def to_entity(self) -> Entity:
        """Convert database entity back to extraction entity."""
        return Entity(
            id=self.id,
            type=EntityType(self.type),
            name=self.name,
            description=self.description,
            confidence=self.confidence,
            attributes=self.attributes,
            source_chunk_id=self.source_chunk_id
        )


class DatabaseRelationship(BaseModel):
    """Pydantic model for database relationship."""
    id: str
    extraction_run_id: str
    subject_id: str
    predicate: str
    object_id: str
    confidence: float
    context: Optional[str] = None
    source_chunk_id: Optional[str] = None
    
    @classmethod
    def from_extraction_relationship(cls, relationship: Relationship, extraction_run_id: str) -> "DatabaseRelationship":
        """Convert extraction relationship to database relationship."""
        return cls(
            id=relationship.id,
            extraction_run_id=extraction_run_id,
            subject_id=relationship.subject_id,
            predicate=relationship.predicate.value,
            object_id=relationship.object_id,
            confidence=relationship.confidence,
            context=relationship.context,
            source_chunk_id=relationship.source_chunk_id
        )
    
    def to_relationship(self) -> Relationship:
        """Convert database relationship back to extraction relationship."""
        return Relationship(
            id=self.id,
            subject_id=self.subject_id,
            predicate=PredicateType(self.predicate),
            object_id=self.object_id,
            confidence=self.confidence,
            context=self.context,
            source_chunk_id=self.source_chunk_id
        )


class DatabaseTriplet(BaseModel):
    """Pydantic model for database triplet."""
    id: str
    extraction_run_id: str
    relationship_id: Optional[str] = None
    subject_id: str
    predicate: str
    object_id: str
    confidence: float
    temporal_context: Optional[datetime] = None
    source_text: Optional[str] = None
    triplet_metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @classmethod
    def from_extraction_triplet(cls, triplet: Triplet, extraction_run_id: str, relationship_id: Optional[str] = None) -> "DatabaseTriplet":
        """Convert extraction triplet to database triplet."""
        return cls(
            id=triplet.id,
            extraction_run_id=extraction_run_id,
            relationship_id=relationship_id,
            subject_id=triplet.subject.id,
            predicate=triplet.predicate.value,
            object_id=triplet.object.id,
            confidence=triplet.confidence,
            temporal_context=triplet.temporal_context,
            source_text=triplet.source_text,
            triplet_metadata=triplet.metadata
        )
    
    def to_triplet(self, subject_entity: Entity, object_entity: Entity) -> Triplet:
        """Convert database triplet back to extraction triplet."""
        return Triplet(
            id=self.id,
            subject=subject_entity,
            predicate=PredicateType(self.predicate),
            object=object_entity,
            confidence=self.confidence,
            temporal_context=self.temporal_context,
            source_text=self.source_text,
            metadata=self.triplet_metadata
        )


def convert_extraction_result_to_db_models(
    extraction_result: ExtractionResult,
    extraction_run_id: Optional[str] = None,
    config_used: Optional[Dict[str, Any]] = None
) -> tuple[DatabaseExtractionRun, List[DatabaseEntity], List[DatabaseRelationship], List[DatabaseTriplet]]:
    """Convert an ExtractionResult to database models."""
    
    # Create extraction run
    if extraction_run_id is None:
        extraction_run_id = str(uuid.uuid4())
    
    db_extraction_run = DatabaseExtractionRun(
        id=extraction_run_id,
        timestamp=extraction_result.extraction_timestamp,
        total_chunks_processed=extraction_result.total_chunks_processed,
        source_document=extraction_result.source_document,
        extraction_stats=extraction_result.extraction_stats,
        config_used=config_used or {}
    )
    
    # Convert entities
    db_entities = [
        DatabaseEntity.from_extraction_entity(entity, extraction_run_id)
        for entity in extraction_result.entities
    ]
    
    # Convert relationships
    db_relationships = [
        DatabaseRelationship.from_extraction_relationship(relationship, extraction_run_id)
        for relationship in extraction_result.relationships
    ]
    
    # Convert triplets
    # Create a mapping from relationship to triplet for linking
    relationship_id_map = {}
    for triplet in extraction_result.triplets:
        # Find matching relationship based on subject, predicate, object
        for relationship in extraction_result.relationships:
            if (relationship.subject_id == triplet.subject.id and
                relationship.predicate == triplet.predicate and
                relationship.object_id == triplet.object.id):
                relationship_id_map[triplet.id] = relationship.id
                break
    
    db_triplets = [
        DatabaseTriplet.from_extraction_triplet(
            triplet, 
            extraction_run_id,
            relationship_id_map.get(triplet.id)
        )
        for triplet in extraction_result.triplets
    ]
    
    return db_extraction_run, db_entities, db_relationships, db_triplets


def convert_db_models_to_extraction_result(
    db_extraction_run: ExtractionRun,
    db_entities: List[EntityDB],
    db_relationships: List[RelationshipDB],
    db_triplets: List[TripletDB]
) -> ExtractionResult:
    """Convert database models back to an ExtractionResult."""
    
    # Convert entities
    entities = []
    entity_lookup = {}
    for db_entity in db_entities:
        entity = Entity(
            id=db_entity.id,
            type=EntityType(db_entity.type),
            name=db_entity.name,
            description=db_entity.description,
            confidence=db_entity.confidence,
            attributes=db_entity.attributes or {},
            source_chunk_id=db_entity.source_chunk_id
        )
        entities.append(entity)
        entity_lookup[entity.id] = entity
    
    # Convert relationships
    relationships = []
    for db_relationship in db_relationships:
        relationship = Relationship(
            id=db_relationship.id,
            subject_id=db_relationship.subject_id,
            predicate=PredicateType(db_relationship.predicate),
            object_id=db_relationship.object_id,
            confidence=db_relationship.confidence,
            context=db_relationship.context,
            source_chunk_id=db_relationship.source_chunk_id
        )
        relationships.append(relationship)
    
    # Convert triplets
    triplets = []
    for db_triplet in db_triplets:
        subject_entity = entity_lookup.get(db_triplet.subject_id)
        object_entity = entity_lookup.get(db_triplet.object_id)
        
        if subject_entity and object_entity:
            triplet = Triplet(
                id=db_triplet.id,
                subject=subject_entity,
                predicate=PredicateType(db_triplet.predicate),
                object=object_entity,
                confidence=db_triplet.confidence,
                temporal_context=db_triplet.temporal_context,
                source_text=db_triplet.source_text,
                metadata=db_triplet.triplet_metadata or {}
            )
            triplets.append(triplet)
    
    return ExtractionResult(
        entities=entities,
        relationships=relationships,
        triplets=triplets,
        extraction_timestamp=db_extraction_run.timestamp,
        source_document=db_extraction_run.source_document,
        total_chunks_processed=db_extraction_run.total_chunks_processed,
        extraction_stats=db_extraction_run.extraction_stats or {}
    )