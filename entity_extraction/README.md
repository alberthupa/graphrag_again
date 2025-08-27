# Entity Extraction Pipeline

This directory contains scripts for extracting entities and relationships from text chunks, then generating knowledge graph triplets. The pipeline is designed for data engineering domains, focusing on KPIs, tables, columns, and metrics.

## Scripts

### Main Usage Scripts

**`run_extraction.py`** - Primary entity extraction script
- Processes text chunks using the existing chunker
- Extracts entities and relationships via OpenAI API
- Saves extraction data to JSONL log file (`extraction_data.jsonl`)
- Outputs results to JSON file (`extraction_results.json`)
- Usage: `uv run entity_extraction/run_extraction.py -n 6`

**`triplet_generator.py`** - Standalone triplet generation script  
- Reads extraction data from the JSONL log file
- Generates structured knowledge graph triplets
- Outputs triplets to JSON file (`triplet_results.json`)
- Usage: `uv run entity_extraction/triplet_generator.py`

### Implementation Files

**`models.py`** - Pydantic models for entities, relationships, and triplets
**`extractor.py`** - OpenAI-based entity extraction logic
**`entity_types.py`** - Configurable entity type definitions
**`triplet_generator_class.py`** - TripletGenerator class implementation

## Quick Start

1. Run entity extraction:
```bash
uv run entity_extraction/run_extraction.py -n 6
```

2. Generate triplets:
```bash
uv run entity_extraction/triplet_generator.py
```

## Output Files

- `extraction_data.jsonl` - Detailed extraction log (chunk by chunk)
- `extraction_results.json` - Final extraction results with metadata
- `triplet_results.json` - Generated knowledge graph triplets

## Entity Types

Supports 8 configurable entity types:
- **KPI** - Key Performance Indicators
- **Table** - Database tables and data structures  
- **Column** - Individual fields within tables
- **Metric** - Calculated measures and values
- **DataSource** - Origin systems for data
- **Domain** - Business areas grouping entities
- **Formula** - Mathematical expressions
- **Definition** - Explanations and specifications