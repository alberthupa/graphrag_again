"""Database interface for entity extraction results storage and retrieval."""

import os
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import logging

from entity_extraction.models import ExtractionResult
from .schema import (
    Base, ExtractionRun, EntityDB, RelationshipDB, TripletDB,
    ResolutionRun, EntityResolutionDecisionDB, RelationshipResolutionDecisionDB, ConnectionDiscoveryDB
)
from .models import (
    convert_extraction_result_to_db_models, convert_db_models_to_extraction_result
)

logger = logging.getLogger(__name__)


class DatabaseInterface:
    """Interface for database operations related to entity extraction."""
    
    def __init__(self, database_url: Optional[str] = None, echo: bool = False):
        """Initialize database interface."""
        if database_url is None:
            # Default to SQLite database in project root
            database_url = "sqlite:///db/knowledge_graph.db"
        
        self.database_url = database_url
        self.engine = create_engine(database_url, echo=echo)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables if they don't exist
        self.create_tables()
    
    def create_tables(self):
        """Create all database tables."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except SQLAlchemyError as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    def drop_tables(self):
        """Drop all database tables (use with caution)."""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.info("Database tables dropped successfully")
        except SQLAlchemyError as e:
            logger.error(f"Failed to drop database tables: {e}")
            raise
    
    @contextmanager
    def get_session(self):
        """Get database session with automatic cleanup."""
        session = self.SessionLocal()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def save_extraction_result(
        self, 
        extraction_result: ExtractionResult,
        extraction_run_id: Optional[str] = None,
        config_used: Optional[Dict[str, Any]] = None
    ) -> str:
        """Save extraction result to database."""
        try:
            # Convert to database models
            db_extraction_run, db_entities, db_relationships, db_triplets = convert_extraction_result_to_db_models(
                extraction_result, extraction_run_id, config_used
            )
            
            with self.get_session() as session:
                # Save extraction run
                extraction_run = ExtractionRun(
                    id=db_extraction_run.id,
                    timestamp=db_extraction_run.timestamp,
                    total_chunks_processed=db_extraction_run.total_chunks_processed,
                    source_document=db_extraction_run.source_document,
                    extraction_stats=db_extraction_run.extraction_stats,
                    config_used=db_extraction_run.config_used
                )
                session.add(extraction_run)
                
                # Save entities (skip duplicates by checking if entity ID already exists)
                saved_entity_ids = set()
                for db_entity in db_entities:
                    if db_entity.id not in saved_entity_ids:
                        entity = EntityDB(
                            id=db_entity.id,
                            extraction_run_id=db_entity.extraction_run_id,
                            type=db_entity.type,
                            name=db_entity.name,
                            description=db_entity.description,
                            confidence=db_entity.confidence,
                            attributes=db_entity.attributes,
                            source_chunk_id=db_entity.source_chunk_id
                        )
                        session.add(entity)
                        saved_entity_ids.add(db_entity.id)
                
                # Save relationships (skip duplicates)
                saved_relationship_ids = set()
                for db_relationship in db_relationships:
                    if db_relationship.id not in saved_relationship_ids:
                        relationship = RelationshipDB(
                            id=db_relationship.id,
                            extraction_run_id=db_relationship.extraction_run_id,
                            subject_id=db_relationship.subject_id,
                            predicate=db_relationship.predicate,
                            object_id=db_relationship.object_id,
                            confidence=db_relationship.confidence,
                            context=db_relationship.context,
                            source_chunk_id=db_relationship.source_chunk_id
                        )
                        session.add(relationship)
                        saved_relationship_ids.add(db_relationship.id)
                
                # Save triplets (skip duplicates)
                saved_triplet_ids = set()
                for db_triplet in db_triplets:
                    if db_triplet.id not in saved_triplet_ids:
                        triplet = TripletDB(
                            id=db_triplet.id,
                            extraction_run_id=db_triplet.extraction_run_id,
                            relationship_id=db_triplet.relationship_id,
                            subject_id=db_triplet.subject_id,
                            predicate=db_triplet.predicate,
                            object_id=db_triplet.object_id,
                            confidence=db_triplet.confidence,
                            temporal_context=db_triplet.temporal_context,
                            source_text=db_triplet.source_text,
                            triplet_metadata=db_triplet.triplet_metadata
                        )
                        session.add(triplet)
                        saved_triplet_ids.add(db_triplet.id)
                
                session.commit()
                logger.info(f"Saved extraction result with run ID: {db_extraction_run.id}")
                return db_extraction_run.id
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to save extraction result: {e}")
            raise
    
    def get_extraction_result(self, extraction_run_id: str) -> Optional[ExtractionResult]:
        """Retrieve extraction result by run ID."""
        try:
            with self.get_session() as session:
                # Get extraction run
                extraction_run = session.query(ExtractionRun).filter(
                    ExtractionRun.id == extraction_run_id
                ).first()
                
                if not extraction_run:
                    return None
                
                # Get related entities, relationships, and triplets
                entities = session.query(EntityDB).filter(
                    EntityDB.extraction_run_id == extraction_run_id
                ).all()
                
                relationships = session.query(RelationshipDB).filter(
                    RelationshipDB.extraction_run_id == extraction_run_id
                ).all()
                
                triplets = session.query(TripletDB).filter(
                    TripletDB.extraction_run_id == extraction_run_id
                ).all()
                
                # Convert back to extraction result
                return convert_db_models_to_extraction_result(
                    extraction_run, entities, relationships, triplets
                )
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to retrieve extraction result: {e}")
            raise
    
    def list_extraction_runs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List recent extraction runs with basic info."""
        try:
            with self.get_session() as session:
                runs = session.query(ExtractionRun).order_by(
                    ExtractionRun.timestamp.desc()
                ).limit(limit).all()
                
                return [
                    {
                        "id": run.id,
                        "timestamp": run.timestamp.isoformat(),
                        "total_chunks_processed": run.total_chunks_processed,
                        "source_document": run.source_document,
                        "entities_count": len(run.entities),
                        "relationships_count": len(run.relationships),
                        "triplets_count": len(run.triplets)
                    }
                    for run in runs
                ]
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to list extraction runs: {e}")
            raise
    
    def delete_extraction_run(self, extraction_run_id: str) -> bool:
        """Delete extraction run and all related data."""
        try:
            with self.get_session() as session:
                # Delete extraction run (cascade will handle related records)
                extraction_run = session.query(ExtractionRun).filter(
                    ExtractionRun.id == extraction_run_id
                ).first()
                
                if extraction_run:
                    session.delete(extraction_run)
                    session.commit()
                    logger.info(f"Deleted extraction run: {extraction_run_id}")
                    return True
                else:
                    logger.warning(f"Extraction run not found: {extraction_run_id}")
                    return False
                    
        except SQLAlchemyError as e:
            logger.error(f"Failed to delete extraction run: {e}")
            raise
    
    def search_entities(
        self, 
        name_pattern: Optional[str] = None,
        entity_type: Optional[str] = None,
        min_confidence: Optional[float] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search entities by various criteria."""
        try:
            with self.get_session() as session:
                query = session.query(EntityDB)
                
                if name_pattern:
                    query = query.filter(EntityDB.name.like(f"%{name_pattern}%"))
                
                if entity_type:
                    query = query.filter(EntityDB.type == entity_type)
                
                if min_confidence is not None:
                    query = query.filter(EntityDB.confidence >= min_confidence)
                
                entities = query.order_by(EntityDB.confidence.desc()).limit(limit).all()
                
                return [
                    {
                        "id": entity.id,
                        "extraction_run_id": entity.extraction_run_id,
                        "type": entity.type,
                        "name": entity.name,
                        "description": entity.description,
                        "confidence": entity.confidence,
                        "attributes": entity.attributes,
                        "source_chunk_id": entity.source_chunk_id
                    }
                    for entity in entities
                ]
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to search entities: {e}")
            raise
    
    def search_triplets(
        self,
        subject_name: Optional[str] = None,
        predicate: Optional[str] = None,
        object_name: Optional[str] = None,
        min_confidence: Optional[float] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search triplets by various criteria."""
        try:
            with self.get_session() as session:
                # Create aliases for the entities table to avoid ambiguous joins
                from sqlalchemy.orm import aliased
                SubjectEntity = aliased(EntityDB)
                ObjectEntity = aliased(EntityDB)
                
                query = session.query(
                    TripletDB,
                    SubjectEntity.name.label('subject_name'),
                    ObjectEntity.name.label('object_name')
                ).join(
                    SubjectEntity, TripletDB.subject_id == SubjectEntity.id
                ).join(
                    ObjectEntity, TripletDB.object_id == ObjectEntity.id
                )
                
                if subject_name:
                    query = query.filter(SubjectEntity.name.like(f"%{subject_name}%"))
                
                if predicate:
                    query = query.filter(TripletDB.predicate == predicate)
                
                if object_name:
                    query = query.filter(ObjectEntity.name.like(f"%{object_name}%"))
                
                if min_confidence is not None:
                    query = query.filter(TripletDB.confidence >= min_confidence)
                
                results = query.order_by(TripletDB.confidence.desc()).limit(limit).all()
                
                return [
                    {
                        "id": result.TripletDB.id,
                        "extraction_run_id": result.TripletDB.extraction_run_id,
                        "subject_name": result.subject_name,
                        "predicate": result.TripletDB.predicate,
                        "object_name": result.object_name,
                        "confidence": result.TripletDB.confidence,
                        "temporal_context": result.TripletDB.temporal_context.isoformat() if result.TripletDB.temporal_context else None,
                        "source_text": result.TripletDB.source_text
                    }
                    for result in results
                ]
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to search triplets: {e}")
            raise
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get basic statistics about the database contents."""
        try:
            with self.get_session() as session:
                stats = {}
                
                # Count extraction runs
                stats['extraction_runs_count'] = session.query(ExtractionRun).count()
                
                # Count entities
                stats['entities_count'] = session.query(EntityDB).count()
                
                # Count relationships
                stats['relationships_count'] = session.query(RelationshipDB).count()
                
                # Count triplets
                stats['triplets_count'] = session.query(TripletDB).count()
                
                # Entity types distribution
                from sqlalchemy import func
                entity_types = session.query(EntityDB.type, func.count(EntityDB.type)).group_by(EntityDB.type).all()
                stats['entity_types_distribution'] = {entity_type: count for entity_type, count in entity_types}
                
                # Relationship predicates distribution
                predicates = session.query(RelationshipDB.predicate, func.count(RelationshipDB.predicate)).group_by(RelationshipDB.predicate).all()
                stats['predicates_distribution'] = {predicate: count for predicate, count in predicates}
                
                return stats
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to get database stats: {e}")
            raise
    
    def save_resolution_result(self, resolution_result) -> str:
        """Save resolution result to database."""
        try:
            with self.get_session() as session:
                # Convert ResolutionResult to database models
                resolution_run = ResolutionRun(
                    id=resolution_result.run_id,
                    timestamp=resolution_result.timestamp,
                    source_extraction_run_ids=resolution_result.source_extraction_run_ids,
                    resolution_stats=resolution_result.stats.dict(),
                    config_used=resolution_result.config_used,
                    resolution_duration_seconds=resolution_result.stats.resolution_duration_seconds
                )
                session.add(resolution_run)
                
                # Save entity resolution decisions
                for decision in resolution_result.entity_decisions:
                    db_decision = EntityResolutionDecisionDB(
                        id=decision.id,
                        resolution_run_id=resolution_result.run_id,
                        canonical_entity_id=decision.canonical_entity_id,
                        duplicate_entity_ids=decision.duplicate_entity_ids,
                        similarity_score=decision.similarity_score,
                        resolution_method=decision.resolution_method,
                        confidence=decision.confidence,
                        decision_metadata=decision.metadata,
                        timestamp=decision.timestamp
                    )
                    session.add(db_decision)
                
                # Save relationship resolution decisions
                for decision in resolution_result.relationship_decisions:
                    db_decision = RelationshipResolutionDecisionDB(
                        id=decision.id,
                        resolution_run_id=resolution_result.run_id,
                        action=decision.action.value,
                        canonical_relationship_id=decision.canonical_relationship_id,
                        merged_relationship_ids=decision.merged_relationship_ids,
                        consolidated_confidence=decision.consolidated_confidence,
                        consolidation_method=decision.consolidation_method,
                        decision_metadata=decision.metadata,
                        timestamp=decision.timestamp
                    )
                    session.add(db_decision)
                
                # Save discovered connections
                for discovery in resolution_result.discovered_connections:
                    db_discovery = ConnectionDiscoveryDB(
                        id=discovery.id,
                        resolution_run_id=resolution_result.run_id,
                        subject_entity_id=discovery.subject_entity_id,
                        object_entity_id=discovery.object_entity_id,
                        suggested_predicate=discovery.suggested_predicate.value,
                        confidence=discovery.confidence,
                        discovery_method=discovery.discovery_method,
                        supporting_evidence=discovery.supporting_evidence,
                        similarity_features=discovery.similarity_features,
                        discovery_metadata=discovery.metadata,
                        timestamp=discovery.timestamp,
                        status="discovered"
                    )
                    session.add(db_discovery)
                
                session.commit()
                logger.info(f"Saved resolution result: {resolution_result.run_id}")
                return resolution_result.run_id
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to save resolution result: {e}")
            raise
    
    def get_resolution_result(self, resolution_run_id: str):
        """Get resolution result by run ID."""
        try:
            with self.get_session() as session:
                resolution_run = session.query(ResolutionRun).filter(
                    ResolutionRun.id == resolution_run_id
                ).first()
                
                if not resolution_run:
                    return None
                
                # TODO: Convert back to ResolutionResult object if needed
                return {
                    "run_id": resolution_run.id,
                    "timestamp": resolution_run.timestamp,
                    "source_extraction_run_ids": resolution_run.source_extraction_run_ids,
                    "resolution_stats": resolution_run.resolution_stats,
                    "config_used": resolution_run.config_used,
                    "entity_decisions_count": len(resolution_run.entity_decisions),
                    "relationship_decisions_count": len(resolution_run.relationship_decisions),
                    "discovered_connections_count": len(resolution_run.discovered_connections)
                }
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to get resolution result: {e}")
            raise
    
    def list_resolution_runs(self) -> List[Dict[str, Any]]:
        """List all resolution runs with summary information."""
        try:
            with self.get_session() as session:
                runs = session.query(ResolutionRun).order_by(ResolutionRun.timestamp.desc()).all()
                
                return [
                    {
                        "id": run.id,
                        "timestamp": run.timestamp,
                        "source_extraction_runs": run.source_extraction_run_ids,
                        "resolution_duration_seconds": run.resolution_duration_seconds,
                        "entity_decisions_count": len(run.entity_decisions),
                        "relationship_decisions_count": len(run.relationship_decisions),
                        "discovered_connections_count": len(run.discovered_connections),
                        "stats": run.resolution_stats
                    }
                    for run in runs
                ]
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to list resolution runs: {e}")
            raise
    
    def search_discoveries(
        self,
        resolution_run_id: Optional[str] = None,
        discovery_method: Optional[str] = None,
        min_confidence: Optional[float] = None,
        status: str = "discovered",
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search discovered connections by various criteria."""
        try:
            with self.get_session() as session:
                query = session.query(ConnectionDiscoveryDB)
                
                if resolution_run_id:
                    query = query.filter(ConnectionDiscoveryDB.resolution_run_id == resolution_run_id)
                
                if discovery_method:
                    query = query.filter(ConnectionDiscoveryDB.discovery_method == discovery_method)
                
                if min_confidence is not None:
                    query = query.filter(ConnectionDiscoveryDB.confidence >= min_confidence)
                
                query = query.filter(ConnectionDiscoveryDB.status == status)
                
                discoveries = query.order_by(ConnectionDiscoveryDB.confidence.desc()).limit(limit).all()
                
                return [
                    {
                        "id": d.id,
                        "resolution_run_id": d.resolution_run_id,
                        "subject_entity_id": d.subject_entity_id,
                        "object_entity_id": d.object_entity_id,
                        "suggested_predicate": d.suggested_predicate,
                        "confidence": d.confidence,
                        "discovery_method": d.discovery_method,
                        "supporting_evidence": d.supporting_evidence,
                        "similarity_features": d.similarity_features,
                        "status": d.status,
                        "timestamp": d.timestamp
                    }
                    for d in discoveries
                ]
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to search discoveries: {e}")
            raise


def create_database_interface(database_url: Optional[str] = None, echo: bool = False) -> DatabaseInterface:
    """Factory function to create database interface."""
    if database_url is None:
        # Try to get from environment variable
        database_url = os.getenv("DATABASE_URL", "sqlite:///db/knowledge_graph.db")
    
    return DatabaseInterface(database_url=database_url, echo=echo)