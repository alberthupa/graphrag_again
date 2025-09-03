# Database Layer

This folder contains the database layer for storing and managing entity extraction results, relationships, triplets, and data resolution outputs from the knowledge graph processing pipeline.

## Overview

The database layer provides persistent storage for:
- **Entity extraction results** - Extracted entities with types, confidence scores, and attributes
- **Relationships** - Subject-predicate-object relationships between entities
- **Triplets** - Knowledge graph triplets with temporal context and metadata
- **Data resolution results** - Entity deduplication, relationship consolidation, and connection discoveries

## Core Components

### Database Models and Schema

- **`models.py`** - Pydantic models that map between entity extraction models and database schema
- **`schema.py`** - SQLAlchemy database schema definitions with tables for:
  - `extraction_runs` - Metadata about extraction runs
  - `entities` - Extracted entities with types, confidence scores
  - `relationships` - Subject-predicate-object relationships  
  - `triplets` - Generated knowledge graph triplets
  - `resolution_runs` - Data resolution run metadata
  - `entity_resolution_decisions` - Entity deduplication decisions
  - `relationship_resolution_decisions` - Relationship consolidation decisions
  - `connection_discoveries` - Newly discovered potential connections

### Database Interface

- **`interface.py`** - Main database interface class providing methods for:
  - Saving and retrieving extraction results
  - Searching entities by name, type, confidence
  - Searching triplets by subject, predicate, object
  - Getting database statistics and distributions
  - Managing resolution results and discovered connections

## Visualization Scripts

### 1. Static Graph Visualization

**Script**: `visualize_graph.py`

**Purpose**: Creates a static PNG visualization of the knowledge graph using matplotlib and NetworkX.

**Usage**:
```bash
# Run from project root
uv run db/visualize_graph.py
```

**Output**: 
- Saves graph as `db/knowledge_graph_visualization.png`
- Shows entities as nodes connected by labeled relationship edges
- Uses spring layout for automatic node positioning

### 2. Interactive Graph Visualization  

**Script**: `visualize_graph_interactive.py`

**Purpose**: Creates an interactive HTML visualization with multiple layout options and customizable styling.

**Usage**:
```bash
# Run from project root  
uv run db/visualize_graph_interactive.py
```

**Features**:
- **Interactive HTML output** - Zoom, pan, hover for details
- **Multiple layout algorithms**:
  - Spring Layout (force-directed) 
  - Circular Layout
  - Random Layout
  - Kamada-Kawai Layout
  - Shell Layout
  - Spectral Layout
- **Customizable styling** - Node sizes, edge widths, colors
- **Configuration persistence** - Settings saved to `plot_config.json`

**Output**:
- Saves interactive graph as `interactive_knowledge_graph.html`  
- Configuration file: `db/plot_config.json`

## Database Utilities

### Database Inspection

**Script**: `peek_database.py`

**Purpose**: Inspect database contents and show sample data.

**Usage**:
```bash
# Run from project root
uv run db/peek_database.py
```

**Features**:
- Shows database overview with table counts
- Displays sample data from each table
- Lists top entities by confidence
- Shows sample triplets with relationships

## Configuration

### Database URL
The database location is configured via environment variable:
```bash
DATABASE_URL=sqlite:///db/knowledge_graph.db  # Default SQLite location
```

### Enable Database Storage
To use database storage in extraction pipelines:
```bash
ENABLE_DATABASE_STORAGE=true
```

## Dependencies

The database layer requires:
- `sqlalchemy` - ORM and database toolkit
- `networkx` - Graph analysis and algorithms  
- `matplotlib` - Static graph plotting
- `plotly` - Interactive graph visualization
- Standard Python libraries (json, logging, etc.)

## Database Schema

### Key Relationships
- Each `extraction_run` contains multiple `entities`, `relationships`, and `triplets`
- `relationships` link two `entities` via subject_id and object_id foreign keys
- `triplets` reference `entities` and optionally link to source `relationships`
- Resolution runs track entity deduplication and relationship consolidation decisions

### Indexes
Performance indexes are created on frequently queried columns:
- Entity names, types, and confidence scores
- Relationship predicates and entity references  
- Triplet confidence scores and temporal contexts
- Resolution run timestamps and decision metadata

## Getting Started

1. **Initialize database** (automatic on first use):
   ```bash
   uv run python -c "from db import create_database_interface; create_database_interface()"
   ```

2. **View database contents**:
   ```bash
   uv run db/peek_database.py
   ```

3. **Create visualizations**:
   ```bash
   # Static visualization
   uv run db/visualize_graph.py
   
   # Interactive visualization  
   uv run db/visualize_graph_interactive.py
   ```

4. **Open interactive graph**:
   - Open `interactive_knowledge_graph.html` in web browser
   - Interact with nodes and edges, try different layouts via config

The database layer integrates with the main entity extraction pipeline and data resolution system to provide comprehensive knowledge graph storage and visualization capabilities.