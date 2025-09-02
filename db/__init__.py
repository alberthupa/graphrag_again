"""Database package for entity extraction results storage."""

from .interface import DatabaseInterface, create_database_interface
from .schema import Base, ExtractionRun, EntityDB, RelationshipDB, TripletDB, ChunkDB
from .models import (
    DatabaseExtractionRun, DatabaseEntity, DatabaseRelationship, DatabaseTriplet,
    convert_extraction_result_to_db_models, convert_db_models_to_extraction_result
)

__all__ = [
    'DatabaseInterface',
    'create_database_interface',
    'Base',
    'ExtractionRun',
    'EntityDB', 
    'RelationshipDB',
    'TripletDB',
    'ChunkDB',
    'DatabaseExtractionRun',
    'DatabaseEntity',
    'DatabaseRelationship', 
    'DatabaseTriplet',
    'convert_extraction_result_to_db_models',
    'convert_db_models_to_extraction_result'
]