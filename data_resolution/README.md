# Data Resolution Pipeline

The data resolution pipeline is the next step after entity extraction that operates on the database to deduplicate entities, consolidate relationships, and discover new potential connections between entities.

## What Data Resolution Does

### 1. Entity Deduplication
- **Fuzzy name matching** using rapidfuzz to identify duplicate entities (e.g., "AI" and "Artificial Intelligence")
- **Medoid selection** chooses the best representative entity from duplicates
- **Acronym matching** merges entities like "ML" ↔ "Machine Learning"
- **Type-aware clustering** only merges entities of the same type
- **Configurable similarity thresholds** for fine-tuning aggressiveness

### 2. Relationship Consolidation
- **Exact duplicate removal** for identical subject-predicate-object triplets
- **Confidence consolidation** using max, average, or weighted methods
- **Context merging** preserves information from consolidated relationships
- **Entity mapping updates** when entities are merged during resolution

### 3. Connection Discovery
- **Similarity-based discovery** analyzes entity names and descriptions
- **Transitive relationship inference** (A→B, B→C suggests A→C)
- **Domain-specific rules** for KPI→Metric, Metric→Table connections
- **Pattern-based discovery** learns from existing relationship patterns

## Running Data Resolution

### Basic Usage
```bash
# Run resolution on all extraction data with default settings
uv run data_resolution/run_resolution.py

# Run with custom similarity thresholds
uv run data_resolution/run_resolution.py --entity-threshold 85.0 --connection-threshold 0.7

# Dry run without saving to database (for testing)
uv run data_resolution/run_resolution.py --dry-run

# Limit number of discoveries returned
uv run data_resolution/run_resolution.py --max-discoveries 20
```

### Database Storage
```bash
# Enable database storage of resolution results
export ENABLE_DATABASE_STORAGE=true
uv run data_resolution/run_resolution.py
```

### Configuration Options
The pipeline can be configured via environment variables:

```bash
# Entity resolution settings
export ENTITY_SIMILARITY_THRESHOLD=80.0        # Fuzzy matching threshold (0-100)
export ENTITY_ACRONYM_THRESHOLD=98.0           # Stricter threshold for acronyms
export ENABLE_ACRONYM_MATCHING=true            # Enable acronym-based matching

# Connection discovery settings  
export CONNECTION_SIMILARITY_THRESHOLD=0.6     # Similarity threshold for new connections (0-1)
export ENABLE_TRANSITIVE_DISCOVERY=true        # Enable A→B→C ⟹ A→C inference
export ENABLE_DOMAIN_RULES=true                # Enable domain-specific connection rules

# Output filtering
export MIN_DISCOVERY_CONFIDENCE=0.5            # Minimum confidence for discovered connections
export MAX_DISCOVERIES_PER_RUN=1000            # Limit number of discoveries returned

# Confidence consolidation method for relationships
export CONFIDENCE_CONSOLIDATION_METHOD=max     # max, average, or weighted
```

## Tracing Resolution Effects

### Quick Overview
```bash
# Show effects of the most recent resolution run
uv run data_resolution/show_last_run.py
```

This displays:
- **Configuration used** (thresholds, enabled features)
- **Processing statistics** (entities merged, relationships consolidated)
- **Database additions** (resolution decisions, discovered connections)
- **Top entity merges** with similarity scores and methods
- **Top discovered connections** with confidence and evidence
- **Discovery method breakdown** showing which techniques found what
- **Comparison with previous run** (if available)

### Detailed Database Inspection

#### List All Resolution Runs
```python
from db import create_database_interface

db = create_database_interface()
runs = db.list_resolution_runs()

for run in runs:
    print(f"Run: {run['id']} at {run['timestamp']}")
    print(f"Duration: {run['resolution_duration_seconds']:.2f}s")
    print(f"Decisions: {run['entity_decisions_count']} entity, {run['relationship_decisions_count']} relationship")
    print(f"Discoveries: {run['discovered_connections_count']}")
    print("---")
```

#### Inspect Specific Resolution Results
```python
# Get detailed data for a specific resolution run
resolution_data = db.get_resolution_result("resolution_1756801022")
stats = resolution_data['resolution_stats']

print(f"Entities: {stats['entities_processed']} → {stats['entities_processed'] - stats['entities_merged']} (-{stats['entities_merged']} merged)")
print(f"Merge rate: {stats['entities_merged'] / stats['entities_processed'] * 100:.1f}%")
```

#### Search Discovered Connections
```python
# Find high-confidence discoveries by method
discoveries = db.search_discoveries(
    min_confidence=0.8,
    discovery_method="similarity_analysis",
    limit=10
)

for d in discoveries:
    print(f"{d['confidence']:.3f}: {d['subject_entity_id']} --[{d['suggested_predicate']}]--> {d['object_entity_id']}")
    print(f"Evidence: {d['supporting_evidence'][0]}")
```

#### Trace Entity Merges
```python
# See which entities were considered duplicates
with db.get_session() as session:
    from db.schema import EntityResolutionDecisionDB
    
    decisions = session.query(EntityResolutionDecisionDB).filter(
        EntityResolutionDecisionDB.resolution_run_id == "your_run_id"
    ).all()
    
    for decision in decisions:
        print(f"Canonical: {decision.canonical_entity_id}")
        print(f"Merged: {decision.duplicate_entity_ids}")
        print(f"Method: {decision.resolution_method}")
        print(f"Similarity: {decision.similarity_score:.3f}")
```

### Direct SQL Queries

For power users who want to query the resolution tables directly:

```sql
-- Overview of all resolution runs
SELECT id, timestamp, resolution_duration_seconds,
       JSON_EXTRACT(resolution_stats, '$.entities_merged') as entities_merged,
       JSON_EXTRACT(resolution_stats, '$.new_connections_discovered') as discoveries
FROM resolution_runs 
ORDER BY timestamp DESC;

-- Entity resolution decisions for a specific run
SELECT canonical_entity_id, resolution_method, similarity_score, confidence,
       JSON_ARRAY_LENGTH(duplicate_entity_ids) as duplicates_count
FROM entity_resolution_decisions 
WHERE resolution_run_id = 'your_run_id'
ORDER BY confidence DESC;

-- Discovery methods performance
SELECT discovery_method, 
       COUNT(*) as count, 
       AVG(confidence) as avg_confidence,
       MAX(confidence) as max_confidence
FROM connection_discoveries
GROUP BY discovery_method
ORDER BY avg_confidence DESC;

-- High-confidence discoveries with evidence
SELECT subject_entity_id, suggested_predicate, object_entity_id, 
       confidence, discovery_method, supporting_evidence
FROM connection_discoveries 
WHERE confidence > 0.8 
ORDER BY confidence DESC;
```

## Database Schema

The resolution pipeline adds these tables to track its operations:

- **`resolution_runs`** - Metadata about each resolution run (timestamp, stats, config)
- **`entity_resolution_decisions`** - Records which entities were merged and why
- **`relationship_resolution_decisions`** - Records relationship consolidation actions
- **`connection_discoveries`** - Newly discovered potential relationships with review status

## Quality Control

### Validating Resolution Results
```python
# Check potentially problematic merges (low similarity but merged)
with db.get_session() as session:
    from db.schema import EntityResolutionDecisionDB
    risky_merges = session.query(EntityResolutionDecisionDB).filter(
        EntityResolutionDecisionDB.similarity_score < 0.85,
        EntityResolutionDecisionDB.confidence < 0.9
    ).all()
    
    print(f"Found {len(risky_merges)} potentially risky merges to review")
    for merge in risky_merges:
        print(f"- {merge.canonical_entity_id}: similarity {merge.similarity_score:.3f}")
```

### Monitoring Performance
```python
# Compare database growth before/after resolution
stats = db.get_database_stats()
print(f"Total entities in DB: {stats['entities_count']}")
print(f"Total relationships: {stats['relationships_count']}")

runs = db.list_resolution_runs()
print(f"Resolution runs: {len(runs)}")
total_discoveries = sum(run['discovered_connections_count'] for run in runs)
print(f"Total discoveries across all runs: {total_discoveries}")
```

## Typical Workflow

1. **Run entity extraction** to populate the database with raw entities and relationships
2. **Run data resolution** to clean and discover new connections:
   ```bash
   export ENABLE_DATABASE_STORAGE=true
   uv run data_resolution/run_resolution.py
   ```
3. **Check the results**:
   ```bash
   uv run data_resolution/show_last_run.py
   ```
4. **Adjust thresholds** if needed and re-run
5. **Review high-confidence discoveries** for manual validation
6. **Use the resolved, canonical entities** for downstream processing

## Expected Results

With typical text data, you can expect:
- **10-30% entity merge rate** (fewer duplicates = cleaner knowledge graph)
- **10-25% relationship consolidation rate** (removes exact duplicates)
- **Multiple discovery methods** finding different types of connections
- **High-confidence discoveries** (>0.8) suitable for automatic acceptance
- **Medium-confidence discoveries** (0.5-0.8) requiring manual review

The pipeline is designed to be conservative by default - it's better to miss some potential merges than to incorrectly merge distinct entities.