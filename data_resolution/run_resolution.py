#!/usr/bin/env python3
"""
Main script for running the data resolution pipeline.

This script orchestrates the complete data resolution process:
1. Loads existing entities and relationships from the database
2. Deduplicates entities using fuzzy matching
3. Consolidates duplicate relationships 
4. Discovers new potential connections between entities
5. Saves resolved data back to the database
6. Generates comprehensive resolution reports

Usage:
    uv run data_resolution/run_resolution.py [options]
"""

import sys
import os
import argparse
import time
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

# Add the parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from db import create_database_interface
from entity_extraction.models import Entity, Relationship
from data_resolution import (
    EntityResolver, 
    RelationshipResolver, 
    ConnectionDiscoverer,
    ResolutionResult,
    ResolutionStats
)

load_dotenv()


def load_config() -> Dict[str, Any]:
    """Load configuration from environment variables with defaults."""
    return {
        "database_url": os.getenv("DATABASE_URL", "sqlite:///db/knowledge_graph.db"),
        "enable_database_storage": os.getenv("ENABLE_DATABASE_STORAGE", "true").lower() == "true",
        "verbose": os.getenv("VERBOSE", "true").lower() == "true",
        
        # Resolution parameters
        "entity_similarity_threshold": float(os.getenv("ENTITY_SIMILARITY_THRESHOLD", "80.0")),
        "entity_acronym_threshold": float(os.getenv("ENTITY_ACRONYM_THRESHOLD", "98.0")),
        "connection_similarity_threshold": float(os.getenv("CONNECTION_SIMILARITY_THRESHOLD", "0.6")),
        "confidence_consolidation_method": os.getenv("CONFIDENCE_CONSOLIDATION_METHOD", "max"),
        
        # Feature toggles
        "enable_acronym_matching": os.getenv("ENABLE_ACRONYM_MATCHING", "true").lower() == "true",
        "enable_transitive_discovery": os.getenv("ENABLE_TRANSITIVE_DISCOVERY", "true").lower() == "true",
        "enable_domain_rules": os.getenv("ENABLE_DOMAIN_RULES", "true").lower() == "true",
        
        # Output settings
        "min_discovery_confidence": float(os.getenv("MIN_DISCOVERY_CONFIDENCE", "0.5")),
        "max_discoveries_per_run": int(os.getenv("MAX_DISCOVERIES_PER_RUN", "1000")),
    }


def load_data_from_database(db_interface, extraction_run_ids: Optional[list] = None, verbose: bool = True):
    """Load entities and relationships from the database."""
    if verbose:
        print("📖 Loading data from database...")
    
    # Load all entities and relationships if no specific extraction runs provided
    entities = []
    relationships = []
    
    try:
        # Get all extraction runs if none specified
        if not extraction_run_ids:
            runs = db_interface.list_extraction_runs()
            if not runs:
                if verbose:
                    print("❌ No extraction runs found in database")
                return [], [], []
            
            extraction_run_ids = [run["id"] for run in runs]
            if verbose:
                print(f"✓ Found {len(extraction_run_ids)} extraction runs")
        
        # Load data from each extraction run
        for run_id in extraction_run_ids:
            try:
                extraction_result = db_interface.get_extraction_result(run_id)
                if extraction_result:
                    entities.extend(extraction_result.entities)
                    relationships.extend(extraction_result.relationships)
                    if verbose:
                        print(f"  ✓ Loaded run {run_id}: {len(extraction_result.entities)} entities, {len(extraction_result.relationships)} relationships")
            except Exception as e:
                if verbose:
                    print(f"  ⚠️ Failed to load run {run_id}: {e}")
        
        if verbose:
            print(f"✓ Total loaded: {len(entities)} entities, {len(relationships)} relationships")
        
        return entities, relationships, extraction_run_ids
        
    except Exception as e:
        print(f"❌ Failed to load data from database: {e}")
        return [], [], []


def run_entity_resolution(entities, config, verbose: bool = True):
    """Run entity resolution to deduplicate entities."""
    if verbose:
        print(f"\n🔍 Step 1: Entity Resolution ({len(entities)} entities)")
    
    resolver = EntityResolver(
        similarity_threshold=config["entity_similarity_threshold"],
        acronym_threshold=config["entity_acronym_threshold"],
        enable_acronym_matching=config["enable_acronym_matching"]
    )
    
    start_time = time.time()
    canonical_entities, entity_decisions = resolver.resolve_entities(entities)
    resolution_time = time.time() - start_time
    
    if verbose:
        duplicates_removed = sum(len(decision.duplicate_entity_ids) for decision in entity_decisions)
        print(f"✓ Entity resolution completed in {resolution_time:.2f}s")
        print(f"  Original entities: {len(entities)}")
        print(f"  Canonical entities: {len(canonical_entities)}")
        print(f"  Duplicates removed: {duplicates_removed}")
        print(f"  Resolution decisions: {len(entity_decisions)}")
    
    return canonical_entities, entity_decisions, resolution_time


def run_relationship_resolution(relationships, entity_decisions, config, verbose: bool = True):
    """Run relationship resolution to consolidate relationships."""
    if verbose:
        print(f"\n🔗 Step 2: Relationship Resolution ({len(relationships)} relationships)")
    
    # Build entity ID mapping from resolution decisions
    entity_id_mapping = {}
    for decision in entity_decisions:
        for duplicate_id in decision.duplicate_entity_ids:
            entity_id_mapping[duplicate_id] = decision.canonical_entity_id
    
    resolver = RelationshipResolver(
        confidence_consolidation_method=config["confidence_consolidation_method"]
    )
    
    start_time = time.time()
    consolidated_relationships, relationship_decisions = resolver.resolve_relationships(
        relationships, entity_id_mapping
    )
    resolution_time = time.time() - start_time
    
    if verbose:
        stats = resolver.get_consolidation_stats()
        print(f"✓ Relationship resolution completed in {resolution_time:.2f}s")
        print(f"  Original relationships: {len(relationships)}")
        print(f"  Consolidated relationships: {len(consolidated_relationships)}")
        print(f"  Resolution decisions: {stats['total_decisions']}")
        print(f"  Exact duplicates removed: {stats['exact_duplicates_removed']}")
        print(f"  Relationships consolidated: {stats['relationships_consolidated']}")
    
    return consolidated_relationships, relationship_decisions, resolution_time


def run_connection_discovery(entities, relationships, config, verbose: bool = True):
    """Run connection discovery to find new potential relationships."""
    if verbose:
        print(f"\n🔍 Step 3: Connection Discovery")
    
    discoverer = ConnectionDiscoverer(
        similarity_threshold=config["connection_similarity_threshold"],
        enable_transitive_discovery=config["enable_transitive_discovery"],
        enable_domain_rules=config["enable_domain_rules"]
    )
    
    start_time = time.time()
    discovered_connections = discoverer.discover_connections(entities, relationships)
    discovery_time = time.time() - start_time
    
    # Filter by minimum confidence and limit results
    high_confidence_discoveries = [
        d for d in discovered_connections 
        if d.confidence >= config["min_discovery_confidence"]
    ]
    
    # Limit results if specified
    max_discoveries = config["max_discoveries_per_run"]
    if len(high_confidence_discoveries) > max_discoveries:
        high_confidence_discoveries = high_confidence_discoveries[:max_discoveries]
        if verbose:
            print(f"  ⚠️ Limited to top {max_discoveries} discoveries")
    
    if verbose:
        print(f"✓ Connection discovery completed in {discovery_time:.2f}s")
        print(f"  Total discoveries: {len(discovered_connections)}")
        print(f"  High-confidence discoveries: {len(high_confidence_discoveries)}")
        
        # Show discovery methods breakdown
        method_counts = {}
        for d in high_confidence_discoveries:
            method_counts[d.discovery_method] = method_counts.get(d.discovery_method, 0) + 1
        
        print("  Discovery methods:")
        for method, count in sorted(method_counts.items()):
            print(f"    {method}: {count}")
    
    return high_confidence_discoveries, discovery_time


def save_resolution_results(resolution_result, db_interface, config, verbose: bool = True):
    """Save resolution results to the database."""
    if not config["enable_database_storage"]:
        if verbose:
            print("⚠️ Database storage disabled - results not saved")
        return None
    
    if verbose:
        print("\n💾 Step 4: Saving resolution results to database")
    
    try:
        resolution_run_id = db_interface.save_resolution_result(resolution_result)
        
        if verbose:
            print(f"✓ Resolution results saved to database")
            print(f"  Resolution run ID: {resolution_run_id}")
            print(f"  Entity decisions: {len(resolution_result.entity_decisions)}")
            print(f"  Relationship decisions: {len(resolution_result.relationship_decisions)}")
            print(f"  Discovered connections: {len(resolution_result.discovered_connections)}")
        
        return resolution_run_id
        
    except Exception as e:
        print(f"❌ Failed to save resolution results: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return None


def print_resolution_summary(resolution_result: ResolutionResult, verbose: bool = True):
    """Print a comprehensive summary of the resolution results."""
    if not verbose:
        return
    
    print("\n" + "=" * 80)
    print("DATA RESOLUTION PIPELINE RESULTS")
    print("=" * 80)
    
    stats = resolution_result.stats
    
    print(f"\n📊 Overall Statistics:")
    print(f"  Run ID: {resolution_result.run_id}")
    print(f"  Timestamp: {resolution_result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Total processing time: {stats.resolution_duration_seconds:.2f} seconds")
    
    print(f"\n🏷️ Entity Resolution:")
    print(f"  Entities processed: {stats.entities_processed}")
    print(f"  Entities merged: {stats.entities_merged}")
    print(f"  Duplicate entities removed: {stats.duplicate_entities_removed}")
    print(f"  Entity merge rate: {stats.entity_merge_rate:.1%}")
    print(f"  Final canonical entities: {len(resolution_result.canonical_entities)}")
    
    print(f"\n🔗 Relationship Resolution:")
    print(f"  Relationships processed: {stats.relationships_processed}")
    print(f"  Relationships consolidated: {stats.relationships_consolidated}")
    print(f"  Relationship consolidation rate: {stats.relationship_consolidation_rate:.1%}")
    print(f"  Final consolidated relationships: {len(resolution_result.consolidated_relationships)}")
    
    print(f"\n🎯 Connection Discovery:")
    print(f"  New connections discovered: {stats.new_connections_discovered}")
    
    if resolution_result.discovered_connections:
        print(f"\n📋 Top Discoveries (by confidence):")
        for i, discovery in enumerate(resolution_result.discovered_connections[:5]):
            print(f"  {i+1}. Confidence: {discovery.confidence:.3f}")
            print(f"     Method: {discovery.discovery_method}")
            print(f"     Connection: {discovery.subject_entity_id} --[{discovery.suggested_predicate.value}]--> {discovery.object_entity_id}")
            if discovery.supporting_evidence:
                print(f"     Evidence: {discovery.supporting_evidence[0]}")
    
    # Show entity resolution decisions
    if resolution_result.entity_decisions:
        print(f"\n🔍 Entity Resolution Examples:")
        for i, decision in enumerate(resolution_result.entity_decisions[:3]):
            print(f"  {i+1}. Method: {decision.resolution_method}")
            print(f"     Canonical: {decision.canonical_entity_id}")
            print(f"     Merged: {len(decision.duplicate_entity_ids)} duplicates")
            print(f"     Similarity: {decision.similarity_score:.3f}")
    
    print(f"\n💡 Next Steps:")
    print(f"  • Review high-confidence discoveries for manual validation")
    print(f"  • Consider adjusting similarity thresholds based on results")
    print(f"  • Use resolved canonical entities for downstream processing")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Run data resolution pipeline")
    parser.add_argument("--extraction-runs", nargs="+", 
                       help="Specific extraction run IDs to process (default: all)")
    parser.add_argument("--dry-run", action="store_true",
                       help="Run resolution without saving results")
    parser.add_argument("--entity-threshold", type=float,
                       help="Override entity similarity threshold")
    parser.add_argument("--connection-threshold", type=float, 
                       help="Override connection discovery threshold")
    parser.add_argument("--max-discoveries", type=int,
                       help="Maximum number of discoveries to return")
    
    args = parser.parse_args()
    
    print("Data Resolution Pipeline")
    print("=" * 50)
    
    # Load configuration
    config = load_config()
    verbose = config["verbose"]
    
    # Apply command line overrides
    if args.entity_threshold:
        config["entity_similarity_threshold"] = args.entity_threshold
    if args.connection_threshold:
        config["connection_similarity_threshold"] = args.connection_threshold
    if args.max_discoveries:
        config["max_discoveries_per_run"] = args.max_discoveries
    if args.dry_run:
        config["enable_database_storage"] = False
    
    if verbose:
        print(f"🗃️ Database: {config['database_url']}")
        print(f"🎯 Entity similarity threshold: {config['entity_similarity_threshold']}")
        print(f"🎯 Connection similarity threshold: {config['connection_similarity_threshold']}")
        print(f"💾 Database storage: {'enabled' if config['enable_database_storage'] else 'disabled'}")
    
    try:
        # Initialize database interface
        if verbose:
            print(f"\n🗃️ Connecting to database...")
        
        db_interface = create_database_interface(
            database_url=config["database_url"],
            echo=False
        )
        
        # Load data from database
        entities, relationships, extraction_run_ids = load_data_from_database(
            db_interface, args.extraction_runs, verbose
        )
        
        if not entities:
            print("❌ No entities found to process")
            sys.exit(1)
        
        # Start the resolution pipeline
        start_total_time = time.time()
        
        # Step 1: Entity Resolution
        canonical_entities, entity_decisions, entity_time = run_entity_resolution(
            entities, config, verbose
        )
        
        # Step 2: Relationship Resolution  
        consolidated_relationships, relationship_decisions, relationship_time = run_relationship_resolution(
            relationships, entity_decisions, config, verbose
        )
        
        # Step 3: Connection Discovery
        discovered_connections, discovery_time = run_connection_discovery(
            canonical_entities, consolidated_relationships, config, verbose
        )
        
        total_time = time.time() - start_total_time
        
        # Create resolution result
        resolution_result = ResolutionResult(
            run_id=f"resolution_{int(time.time())}",
            timestamp=datetime.now(),
            entity_decisions=entity_decisions,
            relationship_decisions=relationship_decisions,
            discovered_connections=discovered_connections,
            canonical_entities=canonical_entities,
            consolidated_relationships=consolidated_relationships,
            stats=ResolutionStats(
                entities_processed=len(entities),
                entities_merged=sum(len(d.duplicate_entity_ids) for d in entity_decisions),
                relationships_processed=len(relationships),
                relationships_consolidated=len(relationship_decisions),
                new_connections_discovered=len(discovered_connections),
                resolution_duration_seconds=total_time,
                duplicate_entities_removed=sum(len(d.duplicate_entity_ids) for d in entity_decisions)
            ),
            config_used=config,
            source_extraction_run_ids=extraction_run_ids
        )
        
        # Step 4: Save results
        resolution_run_id = save_resolution_results(resolution_result, db_interface, config, verbose)
        
        # Print comprehensive summary
        print_resolution_summary(resolution_result, verbose)
        
        print(f"\n🎉 Data resolution completed successfully!")
        if verbose:
            print(f"⏱️ Total time: {total_time:.2f} seconds")
            if resolution_run_id:
                print(f"💾 Results saved with ID: {resolution_run_id}")
        
    except KeyboardInterrupt:
        print("\n⚠️ Resolution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Resolution failed with error: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()