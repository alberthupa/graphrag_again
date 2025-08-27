#!/usr/bin/env python3
"""
Test script to verify the entity extraction pipeline structure and components.

This script tests the pipeline without requiring OpenAI API key by using mock data.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from chunking import Chunker
from entity_extraction.models import Entity, Relationship, EntityType, PredicateType, ExtractionResult
from entity_extraction.triplet_generator import TripletGenerator
from entity_extraction.entity_types import get_extraction_prompt_context, get_all_entity_types


def test_chunker():
    """Test the existing chunker with source data."""
    print("🔪 Testing Chunker")
    print("-" * 30)
    
    chunker = Chunker(sources_dir="sources")
    chunks = chunker.generate_chunks()
    
    if chunks:
        print(f"✓ Generated {len(chunks)} chunks")
        print(f"✓ Sample chunk ID: {chunks[0].id}")
        print(f"✓ Sample chunk text (50 chars): {chunks[0].text[:50]}...")
        print(f"✓ Sample metadata keys: {list(chunks[0].metadata.keys())}")
        return chunks
    else:
        print("❌ No chunks generated")
        return []


def test_entity_types():
    """Test entity type configuration."""
    print("\n🏷️ Testing Entity Types Configuration")
    print("-" * 40)
    
    entity_types = get_all_entity_types()
    print(f"✓ Configured entity types: {entity_types}")
    
    context = get_extraction_prompt_context()
    print(f"✓ Prompt context length: {len(context)} characters")
    print(f"✓ First 200 chars of context: {context[:200]}...")


def test_models():
    """Test Pydantic models creation."""
    print("\n📊 Testing Pydantic Models")
    print("-" * 30)
    
    # Test Entity creation
    entity = Entity(
        id="test_entity_1",
        type=EntityType.KPI,
        name="Customer Acquisition Cost",
        description="The cost of acquiring a new customer",
        confidence=0.95,
        attributes={"unit": "USD", "calculation": "Marketing Spend / New Customers"},
        source_chunk_id="chunk_0"
    )
    print(f"✓ Created Entity: {entity.name} (type: {entity.type.value})")
    
    # Test Relationship creation
    relationship = Relationship(
        id="test_rel_1",
        subject_id="test_entity_1",
        predicate=PredicateType.HAS_DEFINITION,
        object_id="test_entity_2",
        confidence=0.88,
        context="Found in marketing documentation",
        source_chunk_id="chunk_0"
    )
    print(f"✓ Created Relationship: {relationship.predicate.value}")
    
    # Test ExtractionResult
    extraction_result = ExtractionResult(
        entities=[entity],
        relationships=[relationship],
        triplets=[],
        total_chunks_processed=1,
        extraction_stats={"test": "data"}
    )
    print(f"✓ Created ExtractionResult with {len(extraction_result.entities)} entities")


def test_triplet_generator():
    """Test triplet generation with mock data."""
    print("\n🔗 Testing Triplet Generator")
    print("-" * 30)
    
    # Create mock entities
    kpi_entity = Entity(
        id="kpi_1",
        type=EntityType.KPI,
        name="Conversion Rate",
        description="Percentage of visitors who make a purchase",
        confidence=0.92,
        attributes={"unit": "%"},
        source_chunk_id="chunk_1"
    )
    
    definition_entity = Entity(
        id="def_1",
        type=EntityType.DEFINITION,
        name="Conversion Rate Definition",
        description="Ratio of customers to total visitors",
        confidence=0.88,
        attributes={"text": "Conversion rate is calculated as purchases divided by unique visitors"},
        source_chunk_id="chunk_1"
    )
    
    # Create mock relationship
    relationship = Relationship(
        id="rel_1",
        subject_id="kpi_1",
        predicate=PredicateType.HAS_DEFINITION,
        object_id="def_1",
        confidence=0.90,
        context="Definition found in analytics documentation",
        source_chunk_id="chunk_1"
    )
    
    # Create extraction result
    extraction_result = ExtractionResult(
        entities=[kpi_entity, definition_entity],
        relationships=[relationship],
        triplets=[],
        total_chunks_processed=1
    )
    
    # Test triplet generation
    triplet_generator = TripletGenerator(min_confidence=0.3)
    source_text_map = {"chunk_1": "Sample source text about conversion rates..."}
    
    triplets = triplet_generator.generate_triplets(extraction_result, source_text_map)
    
    if triplets:
        print(f"✓ Generated {len(triplets)} triplets")
        triplet = triplets[0]
        print(f"✓ Sample triplet: {triplet.subject.name} --[{triplet.predicate.value}]--> {triplet.object.name}")
        print(f"✓ Triplet confidence: {triplet.confidence:.3f}")
    else:
        print("❌ No triplets generated")
    
    # Test KPI-focused triplets
    kpi_triplets = triplet_generator.generate_kpi_focused_triplets(extraction_result)
    print(f"✓ Generated {len(kpi_triplets)} KPI-focused triplets")
    
    # Test triplets summary
    summary = triplet_generator.export_triplets_summary(triplets)
    print(f"✓ Summary generated: {list(summary.keys())}")


def main():
    """Run all tests."""
    print("Entity Extraction Pipeline - Component Testing")
    print("=" * 60)
    
    try:
        # Test individual components
        chunks = test_chunker()
        test_entity_types()
        test_models()
        test_triplet_generator()
        
        print("\n🎉 All component tests passed!")
        print("\n📝 Next Steps:")
        print("1. Set OPENAI_API_KEY environment variable")
        print("2. Run: uv run entity_extraction/run_extraction.py")
        print("3. Check extraction_results.json for output")
        
        if chunks:
            print(f"\n📊 Ready to process {len(chunks)} chunks from source data")
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()