# GraphRAG Again - Knowledge Graph Extraction and Processing

A comprehensive knowledge graph extraction pipeline that processes text documents to extract entities, relationships, and triplets, with advanced data resolution capabilities for deduplication and connection discovery.

## Project Overview

### Directory Structure
```
graphrag_again/
├── chunking/                    # Text chunking module
│   ├── chunker.py              # Core chunking implementation
│   ├── run_chunker.py          # Standalone execution script
│   └── __init__.py             # Module initialization
├── entity_extraction/          # Entity extraction pipeline
│   ├── models.py               # Pydantic data models
│   ├── entity_types.py         # Entity type configurations
│   ├── extractor.py            # Core extraction engine
│   ├── run_extraction.py       # Orchestration script
│   ├── triplet_generator.py    # Triplet generation
│   ├── triplet_generator_class.py  # TripletGenerator class
│   └── __init__.py             # Package initialization
├── db/                         # Database layer
│   ├── models.py               # Pydantic database models
│   ├── schema.py               # SQLAlchemy schema
│   ├── interface.py            # Database interface
│   ├── peek_database.py        # Database inspection tool
│   ├── visualize_graph.py      # Static visualization
│   ├── visualize_graph_interactive.py  # Interactive visualization
│   └── __init__.py             # Package initialization
├── data_resolution/            # Data resolution pipeline
│   ├── run_resolution.py       # Main orchestration script
│   ├── entity_resolver.py      # Entity deduplication
│   ├── relationship_resolver.py # Relationship consolidation
│   ├── connection_discoverer.py # Connection discovery
│   ├── show_last_run.py        # Resolution analysis
│   ├── models.py               # Resolution data models
│   └── __init__.py             # Module initialization
├── sources/                    # Text source files
├── inspirations/               # Documentation and notes
├── pyproject.toml              # Project configuration
├── .python-version             # Python version specification
├── CLAUDE.md                   # Claude Code instructions
└── README.md                   # Project documentation
```

This project implements a full-stack knowledge graph processing system designed for data engineering domains, focusing on KPIs, tables, columns, metrics, and business intelligence entities. The pipeline includes text chunking, entity extraction, relationship discovery, data resolution, and interactive visualization.

## Project Structure

### Core Directories

#### 📄 `chunking/`
**Text Chunking Module** - Processes text files and breaks them into paragraph-based chunks suitable for GraphRAG systems.

**Script Files:**

**`chunker.py`** - Core chunking implementation containing:
- `Chunk` dataclass: Represents text chunks with id, text, and metadata
- `Chunker` class: Main processing engine with document discovery, paragraph extraction, and metadata generation
- Smart paragraph detection using multi-criteria approach (double line breaks, size filtering, content merging)
- Support for nested directory structures and document name inference

**`run_chunker.py`** - Standalone execution script that:
- Demonstrates Chunker usage with practical examples  
- Provides detailed output including chunk samples and document summaries
- Shows processing statistics and document organization
- Can be run directly from project root or chunking directory

**`__init__.py`** - Module initialization file that:
- Exports `Chunk` and `Chunker` classes for easy importing
- Provides clean module interface for external usage

**Key Features:**
- Document discovery from `sources/` directory with recursive file traversal
- Paragraph-based text splitting with intelligent merging of short fragments
- Comprehensive metadata generation (document_name, source_file, chunk_index, file_size, chunk_length)
- Support for `.txt` and `.md` files with content validation
- Nested directory structure handling with smart document naming
- Error handling for malformed or inaccessible files

**Usage:**
```bash
# Run chunker directly from project root
uv run chunking/run_chunker.py

# Run from chunking directory  
cd chunking && uv run python run_chunker.py

# As a module
from chunking import Chunker
chunker = Chunker(sources_dir="sources")
chunks = chunker.generate_chunks()
```

#### 🔍 `entity_extraction/`
**Entity Extraction Pipeline** - Comprehensive system for extracting entities, relationships, and triplets from text chunks using OpenAI API with structured outputs and validation.

**Script Files:**

**`models.py`** - Core Pydantic data models and type definitions that:
- **Entity model**: Represents extracted entities with id, type, name, description, confidence, attributes, and source chunk reference
- **EntityType enum**: Defines 8 business-focused entity types (KPI, Table, Column, Metric, DataSource, Domain, Formula, Definition)
- **Relationship model**: Captures subject-predicate-object relationships with confidence scores and context
- **PredicateType enum**: Defines 9 relationship types (hasDefinition, calculatedBy, belongsTo, contains, hasType, dependsOn, derivedFrom, measures, locatedIn)
- **Triplet model**: Complete knowledge graph triplet with subject/object entities, predicate, confidence, temporal context, and source text
- **ExtractionResult**: Container for complete extraction pipeline results with entities, relationships, triplets, timestamps, and statistics
- **Utility methods**: Entity filtering by type, relationship filtering by predicate, and hash support for uniqueness

**`entity_types.py`** - Configurable entity type definitions for data engineering domain that:
- **EntityTypeConfig dataclass**: Structured configuration including name, description, required/optional attributes, extraction hints, and example patterns
- **ENTITY_TYPE_CONFIGS**: Complete configuration dictionary for all 8 entity types with detailed business intelligence focus
- **Extraction guidance**: Comprehensive hints and patterns for each entity type to improve OpenAI extraction accuracy
- **Context generation**: Creates structured prompts with entity type descriptions and examples for the extraction pipeline
- **Utility functions**: Configuration retrieval, entity type listing, and prompt context generation for consistent extractions

**`extractor.py`** - Core entity extraction engine using OpenAI API that:
- **EntityExtractor class**: Main extraction engine with configurable OpenAI model and API key management
- **Structured prompt generation**: Creates detailed extraction prompts with entity type guidance, relationship definitions, and JSON format requirements
- **OpenAI API integration**: Handles API calls with proper error handling, temperature control, and token management
- **Response parsing**: Robust JSON parsing with validation, error recovery, and type checking for entities and relationships
- **Chunk processing**: Single-chunk and multi-chunk extraction with progress tracking and debug mode support
- **Statistics generation**: Entity and relationship counting by type/predicate with comprehensive extraction metadata
- **Confidence filtering**: Built-in confidence threshold support and validation for reliable extractions

**`run_extraction.py`** - Standalone orchestration script for complete extraction pipeline that:
- **Environment configuration**: Loads settings from .env file including OpenAI credentials, confidence thresholds, and file paths
- **Chunking integration**: Uses existing chunker to process text files from sources directory with automatic chunk generation
- **Incremental processing**: Processes chunks individually with real-time logging and progress tracking
- **JSONL logging**: Saves detailed extraction data for each chunk including full text, entities, relationships, and metadata
- **Comprehensive error handling**: Graceful failure recovery, API error handling, and user-friendly error messages
- **Debug mode support**: Command-line argument to limit chunk processing for testing and development
- **Statistics and summaries**: Detailed extraction statistics, entity/relationship counts, and processing performance metrics
- **Next-step guidance**: Clear instructions for running triplet generation and accessing results

**`triplet_generator_class.py`** - TripletGenerator class for converting entities and relationships into structured knowledge graph triplets:
- **TripletGenerator class**: Core triplet generation engine with configurable confidence thresholds
- **Entity-relationship linking**: Matches relationship subject/object IDs to actual entity objects for complete triplet construction
- **Confidence filtering**: Applies minimum confidence thresholds to ensure high-quality triplet generation
- **KPI-focused specialization**: Generates specialized triplets focusing on KPI entities and their business relationships
- **Triplet statistics**: Comprehensive summary generation including confidence averages, unique entity counts, and predicate distribution
- **Source context integration**: Links triplets back to original source text and chunk context for traceability

**`triplet_generator.py`** - Standalone triplet generation script that:
- **JSONL data loading**: Reads extraction logs and reconstructs complete entity/relationship objects from JSON data
- **TripletGenerator integration**: Uses TripletGenerator class for structured triplet creation with KPI specialization
- **Database storage integration**: Optional SQLite storage for persistent triplet data with full schema support
- **Results serialization**: Comprehensive JSON output with entities, relationships, triplets, and generation metadata
- **Statistics and reporting**: Detailed summaries of triplet generation results, confidence distributions, and entity relationships
- **Command-line interface**: Flexible input/output file specification with verbose logging and error handling
- **Database configuration**: Environment-based database storage with connection management and error recovery

**`__init__.py`** - Package initialization file that:
- **Clean module interface**: Exports core classes (Entity, Relationship, Triplet, ExtractionResult, EntityExtractor, TripletGenerator)
- **Import management**: Handles relative imports and package structure for easy external usage
- **API surface definition**: Provides clear public API for entity extraction functionality

**Key Features:**
- **8 Specialized Entity Types:** KPI, Table, Column, Metric, DataSource, Domain, Formula, Definition with business intelligence focus
- **9 Relationship Types:** Comprehensive predicate system for business data relationships (hasDefinition, calculatedBy, belongsTo, etc.)
- **OpenAI-based Extraction:** Uses GPT models with structured prompts and JSON schema validation for reliable entity recognition
- **Incremental Processing:** Chunk-by-chunk processing with real-time logging and progress tracking for large document sets
- **Database Integration:** Optional SQLite storage with full schema support for persistent knowledge graph storage
- **KPI Specialization:** Special handling for Key Performance Indicators with focused relationship discovery
- **Confidence Scoring:** Built-in confidence assessment for all extractions with configurable thresholds
- **Comprehensive Logging:** Detailed JSONL logs capturing full extraction context, source text, and processing metadata

**Usage:**
```bash
# Run complete extraction pipeline with incremental logging
uv run entity_extraction/run_extraction.py -n 10

# Generate triplets from extraction log data
uv run entity_extraction/triplet_generator.py

# Enable database storage for persistent results
export ENABLE_DATABASE_STORAGE=true
uv run entity_extraction/triplet_generator.py

# Debug mode for limited chunk processing
uv run entity_extraction/run_extraction.py -n 5
```

**Input/Output Files:**
- **Input**: Text files from `sources/` directory (processed through chunking pipeline)
- **`extraction_data.jsonl`**: Comprehensive JSONL log with chunk-by-chunk extraction details, full text, and metadata
- **`extraction_results.json`**: Final extraction summary with entities, relationships, statistics, and processing metadata
- **`triplet_results.json`**: Complete knowledge graph triplets with entities, relationships, confidence scores, and generation summary
- **Database storage**: Optional SQLite database with full schema for persistent storage and querying

**Configuration:**
Environment variables for customization:
- `OPENAI_API_KEY`: OpenAI API key for entity extraction
- `OPENAI_MODEL`: Model selection (default: gpt-4o-mini)
- `MIN_CONFIDENCE`: Minimum confidence threshold for extractions (default: 0.3)
- `ENABLE_DATABASE_STORAGE`: Enable SQLite database storage (default: false)
- `DATABASE_URL`: Database connection string (default: sqlite:///db/knowledge_graph.db)

#### 🗄️ `db/`
**Database Layer** - Persistent storage and visualization for knowledge graph data.

**Script Files:**

**`__init__.py`** - Database package initialization that:
- Exports core database classes (`DatabaseInterface`, `create_database_interface`)
- Provides access to SQLAlchemy schema models (`Base`, `ExtractionRun`, `EntityDB`, `RelationshipDB`, `TripletDB`, `ChunkDB`)
- Exports Pydantic models for data conversion (`DatabaseExtractionRun`, `DatabaseEntity`, `DatabaseRelationship`, `DatabaseTriplet`)
- Includes conversion utilities between entity extraction models and database representations

**`models.py`** - Pydantic data models for database operations that:
- **DatabaseEntity, DatabaseRelationship, DatabaseTriplet**: Pydantic models that map entity extraction models to database schema
- **Bidirectional conversion methods**: `from_extraction_entity()` and `to_entity()` for seamless data transformation
- **`convert_extraction_result_to_db_models()`**: Converts complete ExtractionResult to database-ready models with relationship linking
- **`convert_db_models_to_extraction_result()`**: Reconstructs ExtractionResult from database records with entity lookup
- **Type safety**: Ensures proper data validation and conversion between extraction and database layers

**`schema.py`** - SQLAlchemy database schema definitions that:
- **Core extraction tables**: `ExtractionRun`, `EntityDB`, `RelationshipDB`, `TripletDB`, `ChunkDB` with foreign key relationships
- **Resolution tracking tables**: `ResolutionRun`, `EntityResolutionDecisionDB`, `RelationshipResolutionDecisionDB`, `ConnectionDiscoveryDB`
- **Performance optimization**: Comprehensive indexing on commonly queried fields (type, name, confidence, timestamps)
- **Relationship mapping**: Full SQLAlchemy relationships with cascade delete for data integrity
- **JSON storage**: Flexible metadata, attributes, and configuration storage using JSON columns

**`interface.py`** - Main database interface providing comprehensive data operations:
- **DatabaseInterface class**: Primary interface for all database operations with session management
- **CRUD operations**: Save/retrieve extraction results, search entities and triplets, manage extraction runs
- **Advanced search capabilities**: Filter by entity type, name patterns, confidence thresholds, predicate types
- **Resolution support**: Save and retrieve data resolution results, search discovered connections
- **Database utilities**: Statistics generation, table management, session handling with automatic cleanup
- **Factory function**: `create_database_interface()` for easy database setup with environment variable support

**`peek_database.py`** - Database inspection and exploration tool that:
- **Table analysis**: Shows all database tables with column information and row counts
- **Sample data display**: Displays first few rows of each table with formatted JSON fields
- **Database statistics**: Comprehensive overview of entities, relationships, triplets counts
- **Query examples**: Shows top entities by confidence and sample triplets
- **Pretty formatting**: JSON fields are formatted for readability with truncation for large values

**`visualize_graph.py`** - Static graph visualization using matplotlib and NetworkX:
- **Database integration**: Loads triplets directly from SQLite database using DatabaseInterface
- **NetworkX graph creation**: Converts triplets to directed graph with nodes and edges
- **Matplotlib visualization**: Spring layout with customizable node and edge styling
- **Export capability**: Saves high-resolution PNG files to `db/knowledge_graph_visualization.png`
- **Graph statistics**: Reports node and edge counts during visualization process

**`visualize_graph_interactive.py`** - Advanced interactive graph visualization with multiple layout options:
- **InteractiveGraphVisualizer class**: Comprehensive visualization system with customizable layouts
- **Multiple layout algorithms**: Spring, circular, random, Kamada-Kawai, shell, and spectral layouts
- **Plotly integration**: Interactive web-based visualization with zoom, pan, and hover functionality
- **Node styling**: Size and color based on node degree, with interactive hover information
- **Edge visualization**: Predicate labels and confidence scores displayed on hover
- **Configuration management**: Save/load plot settings to JSON for consistent visualization preferences
- **HTML export**: Generates standalone HTML files for sharing and web deployment

**Storage Capabilities:**
- Entity extraction results with confidence scores and metadata
- Subject-predicate-object relationships with context information
- Knowledge graph triplets with temporal context and source text
- Data resolution results including entity merging decisions
- Connection discovery results with supporting evidence and similarity features

**Visualization Tools:**
```bash
# Static graph visualization (PNG)
uv run db/visualize_graph.py

# Interactive graph visualization (HTML)
uv run db/visualize_graph_interactive.py

# Database inspection and exploration
uv run db/peek_database.py
```

**Database Schema:**
- **Core extraction tables**: `extraction_runs`, `entities`, `relationships`, `triplets`, `chunks`
- **Resolution tracking**: `resolution_runs`, `entity_resolution_decisions`, `relationship_resolution_decisions`
- **Connection discovery**: `connection_discoveries` with review status and evidence tracking
- **Performance features**: Comprehensive indexing and foreign key relationships for efficient querying

#### 🔧 `data_resolution/`
**Data Resolution Pipeline** - Post-processing system for entity deduplication, relationship consolidation, and connection discovery.

**Script Files:**

**`run_resolution.py`** - Main orchestration script that coordinates the complete data resolution pipeline:
- Loads existing entities and relationships from the database
- Executes entity deduplication using fuzzy matching and acronym detection
- Consolidates duplicate relationships and merges contexts
- Discovers new potential connections between entities using multiple methods
- Saves resolved data back to database with comprehensive tracking
- Generates detailed resolution reports with statistics and examples
- Supports command-line arguments for custom thresholds and dry-run mode

**`entity_resolver.py`** - Entity deduplication engine that implements sophisticated matching algorithms:
- **EntityResolver** class with fuzzy name matching using rapidfuzz library
- Type-aware clustering to only merge entities of the same type (KPI, Table, Column, etc.)
- Medoid selection algorithm to choose the best canonical entity from duplicates
- Acronym matching capability (e.g., merges "AI" with "Artificial Intelligence")
- Configurable similarity thresholds for different matching strategies
- Comprehensive decision tracking with confidence scores and metadata

**`relationship_resolver.py`** - Relationship consolidation system for cleaning duplicate relationships:
- **RelationshipResolver** class for deduplicating subject-predicate-object triplets
- Exact duplicate removal for identical relationships
- Intelligent confidence consolidation using max, average, or weighted methods
- Context merging that preserves information from multiple relationship instances
- Entity ID mapping updates when entities are merged during resolution
- Detailed consolidation statistics and decision tracking

**`connection_discoverer.py`** - Advanced connection discovery engine using multiple discovery methods:
- **ConnectionDiscoverer** class with similarity-based relationship discovery
- Transitive relationship inference (if A→B and B→C, suggest A→C)
- Domain-specific rules for business intelligence entities (KPI↔Metric, Metric↔Table)
- Pattern-based discovery that learns from existing relationship structures
- Configurable similarity thresholds and discovery method toggles
- Evidence tracking and confidence scoring for discovered connections

**`show_last_run.py`** - Analysis and reporting script for resolution run results:
- Displays comprehensive statistics from the most recent resolution run
- Shows configuration parameters used (thresholds, enabled features)
- Lists top entity merges and relationship consolidations with examples
- Breaks down discovered connections by discovery method
- Provides comparison with previous resolution runs
- Includes performance metrics and processing time analysis

**`models.py`** - Pydantic data models and type definitions for resolution tracking:
- **ResolutionResult** - Complete result container for resolution runs
- **EntityResolutionDecision** - Records entity merge decisions with similarity scores
- **RelationshipResolutionDecision** - Tracks relationship consolidation actions
- **ConnectionDiscovery** - Represents newly discovered potential relationships
- **ResolutionStats** - Statistics and metrics for resolution performance
- Comprehensive type safety and data validation for all resolution operations

**`__init__.py`** - Module initialization that exports core resolution classes:
- Provides clean interface for importing EntityResolver, RelationshipResolver, ConnectionDiscoverer
- Exports all data models for external usage
- Enables easy integration with other pipeline components

**Resolution Capabilities:**

1. **Entity Deduplication:**
   - Fuzzy name matching using rapidfuzz with configurable thresholds
   - Acronym matching (e.g., "AI" ↔ "Artificial Intelligence") with high-confidence scoring
   - Type-aware clustering to prevent cross-type merging (KPI won't merge with Table)
   - Medoid selection algorithm to choose the most representative canonical entity

2. **Relationship Consolidation:**
   - Exact duplicate removal for identical subject-predicate-object triplets
   - Smart confidence consolidation using max, average, or weighted methods
   - Context merging that preserves information from multiple relationship instances
   - Automatic entity ID updates when entities are merged during resolution

3. **Connection Discovery:**
   - Similarity-based discovery using name, description, and attribute analysis
   - Transitive relationship inference (A→B, B→C suggests A→C relationship)
   - Domain-specific rules for business intelligence connections (KPI→Metric, Metric→Table)
   - Pattern-based discovery that learns from existing relationship structures
   - Evidence tracking and confidence scoring for all discovered connections

**Usage:**
```bash
# Run resolution with default settings
uv run data_resolution/run_resolution.py

# Custom thresholds and options
uv run data_resolution/run_resolution.py --entity-threshold 85.0 --connection-threshold 0.7

# Dry run without saving to database
uv run data_resolution/run_resolution.py --dry-run

# View results of last resolution run with detailed analysis
uv run data_resolution/show_last_run.py

# Run with specific extraction runs
uv run data_resolution/run_resolution.py --extraction-runs run_1 run_2
```

## Additional Directories

- **`sources/`** - Text source files for processing
- **`inspirations/`** - Documentation and project notes
- **Other support files:** `pyproject.toml`, `.python-version`, `CLAUDE.md`

## Development Setup

### Dependencies
This project uses `uv` for package management and Python 3.10+.

### Installation
```bash
# Install dependencies
uv sync

# Install development dependencies
uv sync --dev
```

### Environment Configuration
Configure these environment variables in `.env`:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4

# Processing Configuration
MIN_CONFIDENCE=0.7
SOURCES_DIR=sources
OUTPUT_FILE=extraction_results.json
VERBOSE=true

# Database Configuration
DATABASE_URL=sqlite:///db/knowledge_graph.db
ENABLE_DATABASE_STORAGE=true

# Entity Resolution Settings
ENTITY_SIMILARITY_THRESHOLD=80.0
ENTITY_ACRONYM_THRESHOLD=98.0
ENABLE_ACRONYM_MATCHING=true

# Connection Discovery Settings
CONNECTION_SIMILARITY_THRESHOLD=0.6
ENABLE_TRANSITIVE_DISCOVERY=true
ENABLE_DOMAIN_RULES=true
MIN_DISCOVERY_CONFIDENCE=0.5
```

## Complete Processing Pipeline

### 1. Text Processing
```bash
# Process text files into chunks
uv run chunking/run_chunker.py
```

### 2. Entity Extraction
```bash
# Extract entities and relationships
uv run entity_extraction/run_extraction.py -n 10

# Generate knowledge graph triplets
uv run entity_extraction/triplet_generator.py
```

### 3. Data Resolution
```bash
# Enable database storage
export ENABLE_DATABASE_STORAGE=true

# Run resolution pipeline
uv run data_resolution/run_resolution.py

# Review results
uv run data_resolution/show_last_run.py
```

### 4. Visualization
```bash
# Create interactive visualization
uv run db/visualize_graph_interactive.py

# Open interactive_knowledge_graph.html in browser
```

## Key Features

- **Modular Architecture:** Each stage can be run independently or as part of a pipeline
- **Database Integration:** Optional SQLite storage with full querying capabilities
- **Interactive Visualization:** Web-based graph exploration with multiple layouts
- **Configurable Resolution:** Tunable thresholds for entity deduplication and connection discovery
- **Domain Specialization:** Tailored for data engineering and business intelligence entities
- **Comprehensive Logging:** Detailed tracking of processing decisions and confidence scores

## Expected Results

- **Entity Extraction:** ~50-200 entities per extraction run depending on text volume
- **Entity Deduplication:** 10-30% merge rate for cleaner knowledge graphs
- **Relationship Discovery:** Automatic discovery of implicit connections between entities
- **High-Quality Triplets:** Structured knowledge representation suitable for downstream applications

This pipeline is designed to transform unstructured text into a clean, queryable knowledge graph with robust deduplication and relationship discovery capabilities.