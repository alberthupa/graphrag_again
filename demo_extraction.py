#!/usr/bin/env python3
"""
Demo script showing entity extraction pipeline usage.

This demonstrates how to use the pipeline on a limited set of chunks.
Set OPENAI_API_KEY environment variable to run actual extraction.
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from chunking import Chunker
from entity_extraction import EntityExtractor, TripletGenerator
from dotenv import load_dotenv

load_dotenv()


def demo_with_limited_chunks(max_chunks: int = 3):
    """Run demo with limited number of chunks to reduce API costs."""
    print("Entity Extraction Pipeline - Demo")
    print("=" * 50)

    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY not set - showing structure only")
        print("   Set the API key to run actual extraction:")
        print("   export OPENAI_API_KEY='your-key-here'")
        return

    print(f"🔍 Running demo with first {max_chunks} chunks")

    try:
        # Get chunks
        chunker = Chunker(sources_dir="sources")
        all_chunks = chunker.generate_chunks()

        if not all_chunks:
            print("❌ No source chunks found")
            return

        # Limit chunks for demo
        chunks = all_chunks[:max_chunks]
        print(f"✓ Processing {len(chunks)} chunks (of {len(all_chunks)} available)")

        # Extract entities
        extractor = EntityExtractor(openai_api_key=api_key, model="gpt-4o-mini")
        extraction_result = extractor.extract_from_chunks(chunks)

        print(f"✓ Extracted {len(extraction_result.entities)} entities")
        print(f"✓ Found {len(extraction_result.relationships)} relationships")

        # Generate triplets
        triplet_generator = TripletGenerator(min_confidence=0.3)
        source_text_map = {chunk.id: chunk.text for chunk in chunks}

        triplets = triplet_generator.generate_triplets(
            extraction_result, source_text_map
        )
        kpi_triplets = triplet_generator.generate_kpi_focused_triplets(
            extraction_result
        )

        print(f"✓ Generated {len(triplets)} triplets")
        print(f"✓ Generated {len(kpi_triplets)} KPI-focused triplets")

        # Show sample results
        if extraction_result.entities:
            print(f"\n🏷️ Sample Entities:")
            for entity in extraction_result.entities[:3]:
                print(
                    f"  - {entity.name} ({entity.type.value}) - confidence: {entity.confidence:.2f}"
                )

        if triplets:
            print(f"\n🔗 Sample Triplets:")
            for triplet in triplets[:3]:
                print(
                    f"  - {triplet.subject.name} --[{triplet.predicate.value}]--> {triplet.object.name}"
                )

        print(f"\n📊 Statistics:")
        stats = extraction_result.extraction_stats
        print(f"  Entity types: {stats.get('entities_by_type', {})}")
        print(f"  Relationship types: {stats.get('relationships_by_predicate', {})}")

    except Exception as e:
        print(f"❌ Demo failed: {e}")


if __name__ == "__main__":
    demo_with_limited_chunks(max_chunks=3)
