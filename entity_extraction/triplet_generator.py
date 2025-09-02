#!/usr/bin/env python3
"""
Standalone triplet generator script.

This script reads extraction data from the log file created by run_extraction.py
and generates structured triplets using the existing TripletGenerator class.

Usage:
    uv run entity_extraction/triplet_generator_standalone.py [--input-log extraction_data.jsonl] [--output triplets_results.json]
"""

import sys
import json
import os
import argparse
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

# Add the parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from entity_extraction import ExtractionResult
from triplet_generator_class import TripletGenerator
from entity_extraction.models import Entity, Relationship, EntityType, PredicateType
from db import create_database_interface

load_dotenv()


def load_config() -> Dict[str, Any]:
    """Load configuration from environment variables with defaults."""
    return {
        "min_confidence": float(os.getenv("MIN_CONFIDENCE", "0.3")),
        "verbose": os.getenv("VERBOSE", "true").lower() == "true",
        "enable_database_storage": os.getenv("ENABLE_DATABASE_STORAGE", "false").lower() == "true",
        "database_url": os.getenv("DATABASE_URL", "sqlite:///db/knowledge_graph.db"),
    }


def reconstruct_entity(entity_data: Dict) -> Entity:
    """Reconstruct Entity object from JSON data."""
    return Entity(
        id=entity_data["id"],
        type=EntityType(entity_data["type"]),
        name=entity_data["name"],
        description=entity_data["description"],
        confidence=entity_data["confidence"],
        attributes=entity_data["attributes"],
        source_chunk_id=entity_data["source_chunk_id"]
    )


def reconstruct_relationship(rel_data: Dict) -> Relationship:
    """Reconstruct Relationship object from JSON data."""
    return Relationship(
        id=rel_data["id"],
        subject_id=rel_data["subject_id"],
        predicate=PredicateType(rel_data["predicate"]),
        object_id=rel_data["object_id"],
        confidence=rel_data["confidence"],
        context=rel_data["context"],
        source_chunk_id=rel_data["source_chunk_id"]
    )


def load_extraction_data_from_log(log_file: str, verbose: bool = True) -> ExtractionResult:
    """Load extraction data from JSONL log file and reconstruct ExtractionResult."""
    all_entities = []
    all_relationships = []
    chunks_processed = 0
    source_text_map = {}
    
    if verbose:
        print(f"📖 Reading extraction data from: {log_file}")
    
    with open(log_file, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            try:
                entry = json.loads(line.strip())
                
                # Extract chunk info
                chunk_info = entry["chunk_info"]
                chunk_id = chunk_info["chunk_id"]
                source_text_map[chunk_id] = chunk_info["chunk_text"]
                
                # Reconstruct entities
                for entity_data in entry["entities"]:
                    entity = reconstruct_entity(entity_data)
                    all_entities.append(entity)
                
                # Reconstruct relationships
                for rel_data in entry["relationships"]:
                    relationship = reconstruct_relationship(rel_data)
                    all_relationships.append(relationship)
                
                chunks_processed += 1
                
            except json.JSONDecodeError as e:
                print(f"⚠️ Warning: Failed to parse line {line_num} in log file: {e}")
                continue
            except KeyError as e:
                print(f"⚠️ Warning: Missing key in line {line_num}: {e}")
                continue
    
    if verbose:
        print(f"✓ Loaded data from {chunks_processed} chunks")
        print(f"✓ Found {len(all_entities)} entities and {len(all_relationships)} relationships")
    
    # Create extraction result
    extraction_result = ExtractionResult(
        entities=all_entities,
        relationships=all_relationships,
        triplets=[],  # Will be populated by TripletGenerator
        total_chunks_processed=chunks_processed,
        extraction_stats={
            "total_entities": len(all_entities),
            "total_relationships": len(all_relationships),
            "entities_by_type": _count_entities_by_type(all_entities),
            "relationships_by_predicate": _count_relationships_by_predicate(all_relationships)
        }
    )
    
    return extraction_result, source_text_map


def _count_entities_by_type(entities: List[Entity]) -> Dict[str, int]:
    """Count entities by type."""
    counts = {}
    for entity in entities:
        entity_type = entity.type.value
        counts[entity_type] = counts.get(entity_type, 0) + 1
    return counts


def _count_relationships_by_predicate(relationships: List[Relationship]) -> Dict[str, int]:
    """Count relationships by predicate."""
    counts = {}
    for rel in relationships:
        predicate = rel.predicate.value
        counts[predicate] = counts.get(predicate, 0) + 1
    return counts


def save_triplet_results(
    extraction_result: ExtractionResult,
    triplets_summary: Dict,
    output_file: str,
    verbose: bool = True,
):
    """Save triplet generation results to JSON file."""
    
    # Convert to serializable format
    output_data = {
        "generation_metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_chunks_processed": extraction_result.total_chunks_processed,
            "extraction_stats": extraction_result.extraction_stats,
        },
        "triplets_summary": triplets_summary,
        "entities": [
            {
                "id": entity.id,
                "type": entity.type.value,
                "name": entity.name,
                "description": entity.description,
                "confidence": entity.confidence,
                "attributes": entity.attributes,
                "source_chunk_id": entity.source_chunk_id,
            }
            for entity in extraction_result.entities
        ],
        "relationships": [
            {
                "id": rel.id,
                "subject_id": rel.subject_id,
                "predicate": rel.predicate.value,
                "object_id": rel.object_id,
                "confidence": rel.confidence,
                "context": rel.context,
                "source_chunk_id": rel.source_chunk_id,
            }
            for rel in extraction_result.relationships
        ],
        "triplets": [
            {
                "id": triplet.id,
                "subject": {
                    "id": triplet.subject.id,
                    "type": triplet.subject.type.value,
                    "name": triplet.subject.name,
                },
                "predicate": triplet.predicate.value,
                "object": {
                    "id": triplet.object.id,
                    "type": triplet.object.type.value,
                    "name": triplet.object.name,
                },
                "confidence": triplet.confidence,
                "source_text": triplet.source_text,
                "metadata": triplet.metadata,
            }
            for triplet in extraction_result.triplets
        ],
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    if verbose:
        print(f"✓ Triplet results saved to {output_file}")


def print_triplet_summary(
    extraction_result: ExtractionResult, triplets_summary: Dict, verbose: bool = True
):
    """Print a summary of triplet generation results."""
    if not verbose:
        return

    print("\n" + "=" * 60)
    print("TRIPLET GENERATION RESULTS")
    print("=" * 60)

    print("📊 Processing Summary:")
    print(f"  Chunks processed: {extraction_result.total_chunks_processed}")
    print(f"  Entities found: {len(extraction_result.entities)}")
    print(f"  Relationships found: {len(extraction_result.relationships)}")
    print(f"  Triplets generated: {len(extraction_result.triplets)}")

    print("🏷️ Entities by Type:")
    entity_stats = extraction_result.extraction_stats.get("entities_by_type", {})
    for entity_type, count in sorted(entity_stats.items()):
        print(f"  {entity_type}: {count}")

    print("🔗 Relationships by Predicate:")
    relationship_stats = extraction_result.extraction_stats.get(
        "relationships_by_predicate", {}
    )
    for predicate, count in sorted(relationship_stats.items()):
        print(f"  {predicate}: {count}")

    print("🎯 Triplets Summary:")
    if triplets_summary.get("total_triplets", 0) > 0:
        print(f"  Total triplets: {triplets_summary['total_triplets']}")
        print(f"  Average confidence: {triplets_summary['average_confidence']:.3f}")
        print(f"  Unique subjects: {triplets_summary['unique_subjects']}")
        print(f"  Unique objects: {triplets_summary['unique_objects']}")
    else:
        print("  No triplets generated")

    if len(extraction_result.triplets) > 0:
        print("📋 Sample Triplets (first 3):")
        for i, triplet in enumerate(extraction_result.triplets[:3]):
            print(
                f"  {i+1}. {triplet.subject.name} --[{triplet.predicate.value}]--> {triplet.object.name}"
            )
            print(f"     Confidence: {triplet.confidence:.3f}")


def main():
    """Main execution function."""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Generate triplets from extraction log data")
    parser.add_argument("--input-log", "-i", 
                       default="extraction_data.jsonl",
                       help="Input log file with extraction data (default: extraction_data.jsonl)")
    parser.add_argument("--output", "-o",
                       default="triplet_results.json", 
                       help="Output file for triplet results (default: triplet_results.json)")
    args = parser.parse_args()
    
    print("Triplet Generation Pipeline")
    print("=" * 50)

    # Load configuration
    config = load_config()
    verbose = config["verbose"]

    if verbose:
        print(f"📄 Input log file: {args.input_log}")
        print(f"📄 Output file: {args.output}")
        print(f"📏 Min confidence: {config['min_confidence']}")
        print(f"🗃️ Database storage: {'enabled' if config['enable_database_storage'] else 'disabled'}")
        if config['enable_database_storage']:
            print(f"🗃️ Database URL: {config['database_url']}")

    # Check if input log file exists
    if not os.path.exists(args.input_log):
        print(f"❌ Error: Input log file '{args.input_log}' not found")
        print("   Make sure to run run_extraction.py first to generate the log file")
        sys.exit(1)

    try:
        # Step 1: Load extraction data from log file
        if verbose:
            print("\n📖 Step 1: Loading extraction data from log file")

        extraction_result, source_text_map = load_extraction_data_from_log(args.input_log, verbose)

        # Step 2: Generate triplets
        if verbose:
            print("\n🔗 Step 2: Generating structured triplets")

        triplet_generator = TripletGenerator(min_confidence=config["min_confidence"])

        # Generate regular triplets
        triplets = triplet_generator.generate_triplets(
            extraction_result, source_text_map
        )

        # Generate KPI-focused triplets (additional specialized triplets)
        kpi_triplets = triplet_generator.generate_kpi_focused_triplets(
            extraction_result
        )

        # Add KPI triplets to the main list (avoiding duplicates)
        existing_triplet_ids = {t.id for t in triplets}
        for kpi_triplet in kpi_triplets:
            if kpi_triplet.id not in existing_triplet_ids:
                triplets.append(kpi_triplet)

        # Update extraction result with all triplets
        extraction_result.triplets = triplets

        triplets_summary = triplet_generator.export_triplets_summary(triplets)

        if verbose:
            print(
                f"✓ Generated {len(triplets)} triplets (including {len(kpi_triplets)} KPI-focused)"
            )

        # Step 3: Save results and display summary
        save_triplet_results(
            extraction_result, triplets_summary, args.output, verbose
        )
        
        # Step 4: Save to database if enabled
        if config['enable_database_storage']:
            if verbose:
                print("\n🗃️ Step 4: Saving results to database")
            
            try:
                db_interface = create_database_interface(
                    database_url=config['database_url'], 
                    echo=False
                )
                
                # Prepare config for database storage
                db_config = {
                    "min_confidence": config['min_confidence'],
                    "input_log_file": args.input_log,
                    "output_file": args.output,
                    "script": "triplet_generator.py"
                }
                
                # Save to database
                extraction_run_id = db_interface.save_extraction_result(
                    extraction_result, 
                    config_used=db_config
                )
                
                if verbose:
                    print(f"✓ Results saved to database with run ID: {extraction_run_id}")
                    
                    # Show database stats
                    stats = db_interface.get_database_stats()
                    print("📊 Database now contains:")
                    print(f"   - {stats['entities_count']} entities")
                    print(f"   - {stats['relationships_count']} relationships") 
                    print(f"   - {stats['triplets_count']} triplets")
                    print(f"   - {stats['extraction_runs_count']} extraction runs")
                    
            except Exception as e:
                print(f"⚠️ Warning: Failed to save to database: {e}")
                if verbose:
                    import traceback
                    traceback.print_exc()
        
        print_triplet_summary(extraction_result, triplets_summary, verbose)

        print("\n🎉 Triplet generation completed successfully!")
        if verbose:
            print(f"📄 Complete results saved to: {args.output}")
            if config['enable_database_storage']:
                print(f"🗃️ Results also saved to database: {config['database_url']}")

    except KeyboardInterrupt:
        print("\n⚠️ Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Pipeline failed with error: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()