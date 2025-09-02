# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.




## Project Structure
This project is about learning ontology setup and usage. Currently it has directories:
- inspirations - with docs and texts serving as notes in which the project has to go
- chunking - a folder with python script with working implementation of text chunker
- sources - a folder with text sources which are used as example content to be chunked and analyzed further
- entity_extraction - contains scripts for extracting entities, relationships, and triplets from text
- db - database layer for storing entity extraction results in SQLite
- data_resolution - data resolution pipeline for deduplicating entities and discovering new connections

- `pyproject.toml` - Project configuration using modern Python packaging standards
- `.python-version` - Specifies Python 3.10 as the target version
- `README.md` - Currently empty project documentation

## Development Commands

### Package Manager
This project is configured to use `uv` as the package manager. Always use `uv` for dependency management and running Python code.

### Running the Application
```bash
uv run main.py
```

### Package Management
The project uses `pyproject.toml` for dependency management with uv.

#### Adding Dependencies
```bash
# Add a new dependency
uv add package-name

# Add a development dependency
uv add --dev package-name

# Add with version constraints
uv add "package-name>=1.0.0"
```

#### Installing Dependencies
```bash
# Install all dependencies (creates virtual environment automatically)
uv sync

# Install in development mode
uv sync --dev
```

#### Running Python Scripts
scripts are always run from main directory (it is important in scope of relative imports)
```bash
# Run any Python script through uv
uv run python script.py

# Run main.py
uv run main.py

# Execute Python commands
uv run python -c "print('Hello World')"
```

#### Virtual Environment Management
uv automatically manages virtual environments, but you can also:
```bash
# Activate the virtual environment
uv run <command>
```
#### environmental variables

if env variables necessary add this:
```
from dotenv import load_dotenv
load_dotenv()
```
currently in env file there is:
OPENAI_API_KEY=...
OPENAI_MODEL=...
MIN_CONFIDENCE=...
SOURCES_DIR=...
OUTPUT_FILE=...
VERBOSE=...
DATABASE_URL=...  # Optional: SQLite database path (default: sqlite:///db/knowledge_graph.db)
ENABLE_DATABASE_STORAGE=...  # Optional: Enable database storage (default: false)


## Python Environment

- Target Python version: 3.10 (specified in `.python-version`)
- The project expects Python >=3.10 as specified in `pyproject.toml`
- uv will automatically create and manage the virtual environment in `.venv/`

## Architecture Notes

- This is a knowledge graph project for entity extraction and storage
- Entity extraction pipeline processes text chunks and extracts entities, relationships, and triplets
- Database layer (SQLite) for storing extraction results with full SQL querying capabilities
- No testing framework is currently configured
- No linting or formatting tools are set up
- Use `uv` for all Python package management and script execution

## Database Storage

### Database Configuration
The project includes an optional database layer for storing entity extraction results in SQLite. This provides persistent storage and querying capabilities beyond the JSON file outputs.

#### Database Environment Variables
- `DATABASE_URL` - SQLite database path (default: `sqlite:///db/knowledge_graph.db`)
- `ENABLE_DATABASE_STORAGE` - Enable database storage (default: false)

#### Database Usage
```bash
# Enable database storage in triplet generation
export ENABLE_DATABASE_STORAGE=true

# Run triplet generation with database storage
uv run entity_extraction/triplet_generator.py
```

#### Database Tables
- `extraction_runs` - Metadata about extraction runs
- `entities` - Extracted entities with types, confidence scores
- `relationships` - Subject-predicate-object relationships
- `triplets` - Generated knowledge graph triplets
- `chunks` - Text chunks (optional, for future use)

#### Database Queries
The database interface provides methods for:
- Saving and retrieving extraction results
- Searching entities by name, type, confidence
- Searching triplets by subject, predicate, object
- Getting database statistics and distributions

## Data Resolution Pipeline

The project includes a comprehensive data resolution system that operates on the database after entity extraction to deduplicate entities, consolidate relationships, and discover new potential connections.

### Running Data Resolution
```bash
# Run resolution on all extraction data
uv run data_resolution/run_resolution.py

# Run with custom thresholds
uv run data_resolution/run_resolution.py --entity-threshold 85.0 --connection-threshold 0.7

# Dry run without saving to database
uv run data_resolution/run_resolution.py --dry-run

# Enable database storage
export ENABLE_DATABASE_STORAGE=true
uv run data_resolution/run_resolution.py
```

### Resolution Features

#### Entity Resolution
- **Fuzzy name matching** using rapidfuzz for identifying duplicate entities
- **Medoid selection** for choosing the best canonical entity from duplicates
- **Acronym matching** to merge entities like "AI" and "Artificial Intelligence"
- **Type-aware clustering** to only merge entities of the same type

#### Relationship Resolution  
- **Exact duplicate removal** for identical subject-predicate-object triplets
- **Confidence consolidation** using max, average, or weighted methods
- **Context merging** to preserve information from consolidated relationships
- **Entity mapping updates** when entities are merged

#### Connection Discovery
- **Similarity-based discovery** using name and description analysis
- **Transitive relationship inference** (A→B, B→C suggests A→C)
- **Domain-specific rules** for KPI→Metric, Metric→Table connections
- **Pattern-based discovery** learning from existing relationship patterns

### Configuration Environment Variables
```bash
# Entity resolution settings
ENTITY_SIMILARITY_THRESHOLD=80.0        # Fuzzy matching threshold (0-100)
ENTITY_ACRONYM_THRESHOLD=98.0           # Stricter threshold for acronyms
ENABLE_ACRONYM_MATCHING=true            # Enable acronym-based matching

# Connection discovery settings  
CONNECTION_SIMILARITY_THRESHOLD=0.6     # Similarity threshold for new connections (0-1)
ENABLE_TRANSITIVE_DISCOVERY=true        # Enable A→B→C ⟹ A→C inference
ENABLE_DOMAIN_RULES=true                # Enable domain-specific connection rules

# Output filtering
MIN_DISCOVERY_CONFIDENCE=0.5            # Minimum confidence for discovered connections
MAX_DISCOVERIES_PER_RUN=1000            # Limit number of discoveries returned

# Resolution method for confidence consolidation
CONFIDENCE_CONSOLIDATION_METHOD=max     # max, average, or weighted
```

### Database Schema for Resolution
The resolution pipeline extends the database with additional tables:
- `resolution_runs` - Metadata about resolution runs
- `entity_resolution_decisions` - Records of entity merging decisions
- `relationship_resolution_decisions` - Records of relationship consolidation
- `connection_discoveries` - Newly discovered potential relationships with review status

### Resolution Output
The pipeline produces comprehensive reports showing:
- Entity merge statistics and examples
- Relationship consolidation summary
- Top discovered connections with confidence scores and evidence
- Processing time and performance metrics
- Configurable thresholds and their effects on results


## reading instructions
if you hwave file ipynb, read them with python json