"""
Schema-Aware Semantic Chunker

A powerful document chunking system that uses schemas to guide intelligent
text segmentation and structured metadata extraction.

Key Features:
- Schema-driven chunking strategies
- Dual input system (documents + schemas)
- LLM-powered metadata extraction
- Multiple chunking algorithms (semantic, fixed-size, sentence-based, etc.)
- Built-in schema templates for common document types
- Batch processing capabilities
- Rich metadata output with entities, relationships, and temporal information
"""

from .chunking import (
    SchemaAwareChunker,
    quick_chunk, 
    create_chunker,
    Document,
    Schema,
    Chunk,
    ChunkingResult,
    EntityType,
    RelationshipType,
    ExtractedEntity,
    ExtractedRelationship,
    TemporalInfo,
    ChunkingStrategy,
    SchemaParser,
    SchemaTemplates,
    SchemaAwareSemanticChunker,
    MetadataExtractor
)

__version__ = "0.1.0"
__author__ = "Schema-Aware Chunker Team"

__all__ = [
    # Main interfaces
    "SchemaAwareChunker",
    "quick_chunk",
    "create_chunker",
    
    # Core models
    "Document",
    "Schema", 
    "Chunk",
    "ChunkingResult",
    "EntityType",
    "RelationshipType",
    "ExtractedEntity",
    "ExtractedRelationship",
    "TemporalInfo",
    "ChunkingStrategy",
    
    # Components
    "SchemaParser",
    "SchemaTemplates",
    "SchemaAwareSemanticChunker",
    "MetadataExtractor",
]