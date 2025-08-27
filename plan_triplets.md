# Entity Extraction Pipeline Implementation Plan

## Overview
Implementation plan for adding entity extraction and triplet generation to the existing text chunking pipeline, following guidelines from `inspirations/temporal_agents_with_knowledge_graphs.ipynb`.

## Requirements Analysis
- **Separation of Concerns**: Keep entity extraction separate from chunking code
- **Flexible Entity Types**: Configurable entity definitions for data engineering domain
- **Focus Domain**: KPIs, tables, columns, metrics, and their relationships
- **Triplet Structure**: Subject-Predicate-Object relationships connecting KPIs to definitions and recipes

## 1. Create `entity_extraction/` Directory Structure
```
entity_extraction/
├── __init__.py                 # Package initialization
├── models.py                   # Pydantic models for entities and triplets  
├── entity_types.py            # Configurable entity type definitions
├── extractor.py               # Main extraction logic
├── triplet_generator.py       # Triplet creation from entities
└── run_extraction.py          # Standalone script to run extraction
```

## 2. Entity Type Configuration (`entity_types.py`)
Define flexible, configurable entity types focusing on data engineering:

### Primary Entity Types
- **KPI**: name, definition, calculation_method, unit, domain
- **Table**: name, description, source_system, columns
- **Column**: name, type, description, table_reference
- **Metric**: name, formula, dependencies
- **DataSource**: name, type, connection_info

### Design Principles
- Easy to modify and extend entity types
- Configuration-driven approach
- Domain-specific but flexible structure

## 3. Core Models (`models.py`)
Define Pydantic models following the temporal agents pattern:

### Key Model Classes
- `Entity` - Base entity with type, name, description, confidence
- `Relationship` - Subject-predicate-object relationships
- `Triplet` - Final triplet structure with temporal context
- `ExtractionResult` - Container for entities, relationships, and metadata

### Model Features
- Type safety with Pydantic
- Validation and parsing
- Serialization support
- Metadata tracking

## 4. Extraction Logic (`extractor.py`)
Core extraction functionality:

### `EntityExtractor` Class
- Processes chunks from the existing chunker
- Uses OpenAI API with structured prompts (similar to temporal agents)
- Extracts entities based on configurable types
- Identifies relationships between entities

### Key Features
- Integration with existing `Chunk` objects
- Configurable entity type recognition
- Relationship identification
- Confidence scoring

## 5. Triplet Generation (`triplet_generator.py`)
Convert entities and relationships to structured triplets:

### `TripletGenerator` Class
- Focus on KPI-definition-recipe connections
- Generate Subject-Predicate-Object structures
- Add confidence scores and source references
- Temporal context when available

### Triplet Types
- KPI → hasDefinition → Definition
- KPI → calculatedBy → Formula
- KPI → belongsTo → Domain
- Table → contains → Column
- Column → hasType → DataType

## 6. Integration Script (`run_extraction.py`)
Orchestration script that maintains separation:

### Pipeline Flow
1. **Input**: Use existing chunker to process sources
2. **Entity Extraction**: Process chunks to extract entities
3. **Triplet Generation**: Convert entities/relationships to triplets
4. **Output**: Structured triplets with metadata

### Design Principles
- Clean separation between chunking and extraction
- Reusable components
- Error handling and logging
- Progress tracking

## 7. Dependencies
Utilize existing project dependencies:
- `pydantic>=2.0.0` - Data models and validation
- `openai>=1.0.0` - Entity extraction via LLM
- `langchain-openai>=0.1.0` - Additional OpenAI integration
- Existing chunking module for input processing

## 8. Integration Points
- **Input**: Consume `Chunk` objects from existing chunker
- **Configuration**: Entity types easily modifiable in separate file
- **Output**: Structured triplets ready for knowledge graph construction
- **Extensibility**: Framework supports adding new entity types and relationships

## Next Steps
1. Create directory structure and base files
2. Implement core models with Pydantic
3. Define initial entity types for data engineering domain
4. Implement entity extractor with OpenAI integration
5. Create triplet generator
6. Build integration script
7. Test with existing source data