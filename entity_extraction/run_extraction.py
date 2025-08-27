#!/usr/bin/env python3
"""
Standalone script to run the entity extraction pipeline.

This script orchestrates the entity extraction pipeline:
1. Uses existing chunker to process sources
2. Extracts entities and relationships from chunks
3. Saves extraction data to comprehensive log file (chunk by chunk)
4. Outputs extraction results with metadata and statistics

Note: Triplet generation is handled by a separate script (triplet_generator.py)
"""

import sys
import json
import os
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

# Add the parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from chunking import Chunker
from entity_extraction import EntityExtractor, ExtractionResult

load_dotenv()


def load_config() -> Dict[str, Any]:
    """Load configuration from environment variables with defaults."""
    return {
        "sources_dir": os.getenv("SOURCES_DIR", "sources"),
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "min_confidence": float(os.getenv("MIN_CONFIDENCE", "0.3")),
        "output_file": os.getenv("OUTPUT_FILE", "extraction_results.json"),
        "extraction_log_file": os.getenv("EXTRACTION_LOG_FILE", "extraction_data.jsonl"),
        "verbose": os.getenv("VERBOSE", "true").lower() == "true",
    }


def save_extraction_log_entry(chunk, entities: List, relationships: List, log_file: str):
    """Save extraction data for a chunk to the comprehensive log file."""
    log_entry = {
        "chunk_info": {
            "chunk_id": chunk.id,
            "chunk_text": chunk.text,
            "chunk_metadata": getattr(chunk, 'metadata', {}),
            "processed_at": datetime.now().isoformat(),
        },
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
            for entity in entities
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
            for rel in relationships
        ],
    }
    
    # Append to log file (JSONL format)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")


def save_extraction_results(
    extraction_result: ExtractionResult,
    output_file: str,
    verbose: bool = True,
):
    """Save extraction results to JSON file (without triplets)."""

    # Convert to serializable format
    output_data = {
        "extraction_metadata": {
            "timestamp": extraction_result.extraction_timestamp.isoformat(),
            "total_chunks_processed": extraction_result.total_chunks_processed,
            "extraction_stats": extraction_result.extraction_stats,
        },
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
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    if verbose:
        print(f"✓ Extraction results saved to {output_file}")




def print_extraction_summary(extraction_result: ExtractionResult, verbose: bool = True):
    """Print a summary of extraction results."""
    if not verbose:
        return

    print("\n" + "=" * 60)
    print("ENTITY EXTRACTION PIPELINE RESULTS")
    print("=" * 60)

    print("\n📊 Processing Summary:")
    print(f"  Chunks processed: {extraction_result.total_chunks_processed}")
    print(f"  Entities found: {len(extraction_result.entities)}")
    print(f"  Relationships found: {len(extraction_result.relationships)}")

    print("\n🏷️ Entities by Type:")
    entity_stats = extraction_result.extraction_stats.get("entities_by_type", {})
    for entity_type, count in sorted(entity_stats.items()):
        print(f"  {entity_type}: {count}")

    print("\n🔗 Relationships by Predicate:")
    relationship_stats = extraction_result.extraction_stats.get(
        "relationships_by_predicate", {}
    )
    for predicate, count in sorted(relationship_stats.items()):
        print(f"  {predicate}: {count}")

    print("\n💡 Next Steps:")
    print("  Run triplet_generator.py to generate structured triplets from this extraction data")


def extract_with_incremental_saving(chunks: List, extractor: EntityExtractor, log_file: str, verbose: bool = True, debug_n_chunks: Optional[int] = None) -> ExtractionResult:
    """Extract entities and relationships with incremental saving and comprehensive logging after each chunk."""
    all_entities = []
    all_relationships = []
    
    # Initialize log file (clear any existing content)
    with open(log_file, "w", encoding="utf-8"):
        pass  # Create empty file
    
    # Limit chunks for debug mode if specified
    if debug_n_chunks is not None:
        chunks = chunks[:debug_n_chunks]
        if verbose:
            print(f"Debug mode: Processing only first {len(chunks)} chunks")
    
    for i, chunk in enumerate(chunks):
        if verbose:
            print(f"Processing chunk {i+1}/{len(chunks)}: {chunk.id}")
        
        entities, relationships = extractor.extract_from_chunk(chunk)
        all_entities.extend(entities)
        all_relationships.extend(relationships)
        
        # Save to comprehensive log file
        save_extraction_log_entry(chunk, entities, relationships, log_file)
        
        if verbose:
            print(f"✓ Chunk {i+1} logged: {len(entities)} entities, {len(relationships)} relationships")
    
    # Create final extraction result
    extraction_result = ExtractionResult(
        entities=all_entities,
        relationships=all_relationships,
        triplets=[],  # Triplets will be generated by separate script
        total_chunks_processed=len(chunks),
        extraction_stats={
            "total_entities": len(all_entities),
            "total_relationships": len(all_relationships),
            "entities_by_type": _count_entities_by_type(all_entities),
            "relationships_by_predicate": _count_relationships_by_predicate(all_relationships)
        }
    )
    
    return extraction_result


def _count_entities_by_type(entities: List) -> Dict[str, int]:
    """Count entities by type."""
    counts = {}
    for entity in entities:
        entity_type = entity.type.value
        counts[entity_type] = counts.get(entity_type, 0) + 1
    return counts


def _count_relationships_by_predicate(relationships: List) -> Dict[str, int]:
    """Count relationships by predicate."""
    counts = {}
    for rel in relationships:
        predicate = rel.predicate.value
        counts[predicate] = counts.get(predicate, 0) + 1
    return counts


def main():
    """Main execution function."""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Extract entities from text chunks with incremental saving")
    parser.add_argument("--debug-chunks", "-n", type=int, 
                       help="Debug mode: process only N chunks")
    args = parser.parse_args()
    
    print("Entity Extraction Pipeline")
    print("=" * 50)

    # Load configuration
    config = load_config()
    verbose = config["verbose"]

    if verbose:
        print(f"📁 Sources directory: {config['sources_dir']}")
        print(f"🤖 Model: {config['model']}")
        print(f"📏 Min confidence: {config['min_confidence']}")
        print(f"📄 Extraction log file: {config['extraction_log_file']}")

    # Check for OpenAI API key
    if not config["openai_api_key"]:
        print("❌ Error: OPENAI_API_KEY environment variable is required")
        print("   Please set your OpenAI API key:")
        print("   export OPENAI_API_KEY='your-api-key-here'")
        sys.exit(1)

    try:
        # Step 1: Generate chunks using existing chunker
        if verbose:
            print(f"\n🔪 Step 1: Chunking text from {config['sources_dir']}")

        chunker = Chunker(sources_dir=config["sources_dir"])
        chunks = chunker.generate_chunks()

        if not chunks:
            print(f"❌ No chunks found in {config['sources_dir']} directory")
            print("   Make sure text files (.txt, .md) exist in the sources directory")
            sys.exit(1)

        if verbose:
            print(f"✓ Generated {len(chunks)} chunks from source documents")

        # Step 2: Extract entities and relationships with comprehensive logging
        if verbose:
            print("\n🔍 Step 2: Extracting entities and relationships (saving after each chunk)")

        extractor = EntityExtractor(
            openai_api_key=config["openai_api_key"], model=config["model"]
        )

        extraction_result = extract_with_incremental_saving(
            chunks, extractor, config["extraction_log_file"], verbose, args.debug_chunks
        )

        if verbose:
            print(
                f"✓ Extracted {len(extraction_result.entities)} entities and {len(extraction_result.relationships)} relationships"
            )

        # Step 3: Save extraction results
        save_extraction_results(extraction_result, config["output_file"], verbose)
        print_extraction_summary(extraction_result, verbose)

        print("\n🎉 Entity extraction completed successfully!")
        if verbose:
            print(f"📄 Extraction results saved to: {config['output_file']}")
            print(f"📄 Comprehensive log saved to: {config['extraction_log_file']}")
            print("\n▶️ Next: Run 'uv run entity_extraction/triplet_generator.py' to generate triplets")

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
