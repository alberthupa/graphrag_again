"""Database schema definitions for entity extraction results storage."""

from sqlalchemy import (
    Column, String, Integer, Float, JSON, DateTime, Text,
    ForeignKey, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

Base = declarative_base()


class ExtractionRun(Base):
    """Represents a complete extraction run with metadata."""
    __tablename__ = "extraction_runs"
    
    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    total_chunks_processed = Column(Integer, default=0, nullable=False)
    source_document = Column(String)
    extraction_stats = Column(JSON)
    config_used = Column(JSON)  # Store extraction configuration
    
    # Relationships
    entities = relationship("EntityDB", back_populates="extraction_run", cascade="all, delete-orphan")
    relationships = relationship("RelationshipDB", back_populates="extraction_run", cascade="all, delete-orphan")
    triplets = relationship("TripletDB", back_populates="extraction_run", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_extraction_runs_timestamp', 'timestamp'),
    )


class EntityDB(Base):
    """Database representation of an extracted entity."""
    __tablename__ = "entities"
    
    id = Column(String, primary_key=True)
    extraction_run_id = Column(String, ForeignKey("extraction_runs.id"), nullable=False)
    type = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    confidence = Column(Float, nullable=False)
    attributes = Column(JSON)
    source_chunk_id = Column(String)
    
    # Relationships
    extraction_run = relationship("ExtractionRun", back_populates="entities")
    subject_relationships = relationship("RelationshipDB", foreign_keys="[RelationshipDB.subject_id]", back_populates="subject_entity")
    object_relationships = relationship("RelationshipDB", foreign_keys="[RelationshipDB.object_id]", back_populates="object_entity")
    subject_triplets = relationship("TripletDB", foreign_keys="[TripletDB.subject_id]", back_populates="subject_entity")
    object_triplets = relationship("TripletDB", foreign_keys="[TripletDB.object_id]", back_populates="object_entity")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_entities_extraction_run', 'extraction_run_id'),
        Index('idx_entities_type', 'type'),
        Index('idx_entities_name', 'name'),
        Index('idx_entities_confidence', 'confidence'),
    )


class RelationshipDB(Base):
    """Database representation of an extracted relationship."""
    __tablename__ = "relationships"
    
    id = Column(String, primary_key=True)
    extraction_run_id = Column(String, ForeignKey("extraction_runs.id"), nullable=False)
    subject_id = Column(String, ForeignKey("entities.id"), nullable=False)
    predicate = Column(String, nullable=False)
    object_id = Column(String, ForeignKey("entities.id"), nullable=False)
    confidence = Column(Float, nullable=False)
    context = Column(Text)
    source_chunk_id = Column(String)
    
    # Relationships
    extraction_run = relationship("ExtractionRun", back_populates="relationships")
    subject_entity = relationship("EntityDB", foreign_keys="[RelationshipDB.subject_id]", back_populates="subject_relationships")
    object_entity = relationship("EntityDB", foreign_keys="[RelationshipDB.object_id]", back_populates="object_relationships")
    triplets = relationship("TripletDB", back_populates="source_relationship")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_relationships_extraction_run', 'extraction_run_id'),
        Index('idx_relationships_subject', 'subject_id'),
        Index('idx_relationships_object', 'object_id'),
        Index('idx_relationships_predicate', 'predicate'),
        Index('idx_relationships_confidence', 'confidence'),
    )


class TripletDB(Base):
    """Database representation of a generated triplet."""
    __tablename__ = "triplets"
    
    id = Column(String, primary_key=True)
    extraction_run_id = Column(String, ForeignKey("extraction_runs.id"), nullable=False)
    relationship_id = Column(String, ForeignKey("relationships.id"), nullable=True)
    subject_id = Column(String, ForeignKey("entities.id"), nullable=False)
    predicate = Column(String, nullable=False)
    object_id = Column(String, ForeignKey("entities.id"), nullable=False)
    confidence = Column(Float, nullable=False)
    temporal_context = Column(DateTime)
    source_text = Column(Text)
    triplet_metadata = Column(JSON)
    
    # Relationships
    extraction_run = relationship("ExtractionRun", back_populates="triplets")
    source_relationship = relationship("RelationshipDB", back_populates="triplets")
    subject_entity = relationship("EntityDB", foreign_keys="[TripletDB.subject_id]", back_populates="subject_triplets")
    object_entity = relationship("EntityDB", foreign_keys="[TripletDB.object_id]", back_populates="object_triplets")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_triplets_extraction_run', 'extraction_run_id'),
        Index('idx_triplets_subject', 'subject_id'),
        Index('idx_triplets_object', 'object_id'),
        Index('idx_triplets_predicate', 'predicate'),
        Index('idx_triplets_confidence', 'confidence'),
        Index('idx_triplets_temporal_context', 'temporal_context'),
    )


class ChunkDB(Base):
    """Database representation of text chunks (optional, for future use)."""
    __tablename__ = "chunks"
    
    id = Column(String, primary_key=True)
    extraction_run_id = Column(String, ForeignKey("extraction_runs.id"), nullable=False)
    text = Column(Text, nullable=False)
    chunk_metadata = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    extraction_run = relationship("ExtractionRun")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_chunks_extraction_run', 'extraction_run_id'),
        Index('idx_chunks_created_at', 'created_at'),
    )


class ResolutionRun(Base):
    """Represents a complete data resolution run with metadata."""
    __tablename__ = "resolution_runs"
    
    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    source_extraction_run_ids = Column(JSON, nullable=False)  # List of extraction run IDs processed
    resolution_stats = Column(JSON, nullable=False)  # ResolutionStats as JSON
    config_used = Column(JSON, nullable=False)  # Resolution configuration
    resolution_duration_seconds = Column(Float, nullable=False)
    
    # Relationships
    entity_decisions = relationship("EntityResolutionDecisionDB", back_populates="resolution_run", cascade="all, delete-orphan")
    relationship_decisions = relationship("RelationshipResolutionDecisionDB", back_populates="resolution_run", cascade="all, delete-orphan")
    discovered_connections = relationship("ConnectionDiscoveryDB", back_populates="resolution_run", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_resolution_runs_timestamp', 'timestamp'),
    )


class EntityResolutionDecisionDB(Base):
    """Database representation of entity resolution decisions."""
    __tablename__ = "entity_resolution_decisions"
    
    id = Column(String, primary_key=True)
    resolution_run_id = Column(String, ForeignKey("resolution_runs.id"), nullable=False)
    canonical_entity_id = Column(String, nullable=False)
    duplicate_entity_ids = Column(JSON, nullable=False)  # List of duplicate entity IDs
    similarity_score = Column(Float, nullable=False)
    resolution_method = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    decision_metadata = Column(JSON)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    resolution_run = relationship("ResolutionRun", back_populates="entity_decisions")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_entity_decisions_resolution_run', 'resolution_run_id'),
        Index('idx_entity_decisions_canonical_entity', 'canonical_entity_id'),
        Index('idx_entity_decisions_method', 'resolution_method'),
        Index('idx_entity_decisions_confidence', 'confidence'),
    )


class RelationshipResolutionDecisionDB(Base):
    """Database representation of relationship resolution decisions."""
    __tablename__ = "relationship_resolution_decisions"
    
    id = Column(String, primary_key=True)
    resolution_run_id = Column(String, ForeignKey("resolution_runs.id"), nullable=False)
    action = Column(String, nullable=False)  # ResolutionActionType value
    canonical_relationship_id = Column(String, nullable=False)
    merged_relationship_ids = Column(JSON, nullable=False)  # List of merged relationship IDs
    consolidated_confidence = Column(Float, nullable=False)
    consolidation_method = Column(String, nullable=False)
    decision_metadata = Column(JSON)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    resolution_run = relationship("ResolutionRun", back_populates="relationship_decisions")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_relationship_decisions_resolution_run', 'resolution_run_id'),
        Index('idx_relationship_decisions_canonical', 'canonical_relationship_id'),
        Index('idx_relationship_decisions_action', 'action'),
        Index('idx_relationship_decisions_confidence', 'consolidated_confidence'),
    )


class ConnectionDiscoveryDB(Base):
    """Database representation of discovered potential connections."""
    __tablename__ = "connection_discoveries"
    
    id = Column(String, primary_key=True)
    resolution_run_id = Column(String, ForeignKey("resolution_runs.id"), nullable=False)
    subject_entity_id = Column(String, nullable=False)
    object_entity_id = Column(String, nullable=False)
    suggested_predicate = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    discovery_method = Column(String, nullable=False)
    supporting_evidence = Column(JSON)  # List of evidence strings
    similarity_features = Column(JSON)  # Dict of similarity features
    discovery_metadata = Column(JSON)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Status tracking for discovered connections
    status = Column(String, default="discovered")  # discovered, reviewed, accepted, rejected
    review_notes = Column(Text)
    reviewed_at = Column(DateTime)
    reviewed_by = Column(String)
    
    # Relationships
    resolution_run = relationship("ResolutionRun", back_populates="discovered_connections")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_connection_discoveries_resolution_run', 'resolution_run_id'),
        Index('idx_connection_discoveries_subject', 'subject_entity_id'),
        Index('idx_connection_discoveries_object', 'object_entity_id'),
        Index('idx_connection_discoveries_predicate', 'suggested_predicate'),
        Index('idx_connection_discoveries_confidence', 'confidence'),
        Index('idx_connection_discoveries_method', 'discovery_method'),
        Index('idx_connection_discoveries_status', 'status'),
    )