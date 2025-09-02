#!/usr/bin/env python3
"""
Simple script to show the effects of the last resolution run.

Shows what was added to the database, with which thresholds, and key statistics.
"""

import sys
import os
from pathlib import Path

# Add the parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from db import create_database_interface


def main():
    """Show effects of the last resolution run."""
    print("Last Data Resolution Run Effects")
    print("=" * 50)
    
    try:
        # Connect to database
        db = create_database_interface()
        
        # Get all resolution runs, sorted by timestamp (newest first)
        runs = db.list_resolution_runs()
        
        if not runs:
            print("❌ No resolution runs found in database")
            print("   Run the resolution pipeline first:")
            print("   uv run data_resolution/run_resolution.py")
            return
        
        # Get the latest run
        latest_run = runs[0]
        run_id = latest_run['id']
        
        print(f"🔍 Latest Resolution Run: {run_id}")
        print(f"📅 Timestamp: {latest_run['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️  Duration: {latest_run['resolution_duration_seconds']:.2f} seconds")
        print()
        
        # Show configuration used
        resolution_data = db.get_resolution_result(run_id)
        if resolution_data and 'config_used' in resolution_data:
            config = resolution_data['config_used']
            print("⚙️  Configuration Used:")
            print(f"   Entity similarity threshold: {config.get('entity_similarity_threshold', 'N/A')}")
            print(f"   Connection similarity threshold: {config.get('connection_similarity_threshold', 'N/A')}")
            print(f"   Acronym matching: {'✓' if config.get('enable_acronym_matching') else '✗'}")
            print(f"   Transitive discovery: {'✓' if config.get('enable_transitive_discovery') else '✗'}")
            print(f"   Domain rules: {'✓' if config.get('enable_domain_rules') else '✗'}")
            print()
        
        # Show statistics
        stats = latest_run['stats']
        print("📊 Resolution Statistics:")
        print(f"   Entities processed: {stats.get('entities_processed', 0)}")
        print(f"   Entities merged: {stats.get('entities_merged', 0)}")
        print(f"   Duplicate entities removed: {stats.get('duplicate_entities_removed', 0)}")
        print(f"   Entity merge rate: {(stats.get('entities_merged', 0) / max(1, stats.get('entities_processed', 1)) * 100):.1f}%")
        print()
        print(f"   Relationships processed: {stats.get('relationships_processed', 0)}")
        print(f"   Relationships consolidated: {stats.get('relationships_consolidated', 0)}")
        print(f"   Relationship consolidation rate: {(stats.get('relationships_consolidated', 0) / max(1, stats.get('relationships_processed', 1)) * 100):.1f}%")
        print()
        print(f"   New connections discovered: {stats.get('new_connections_discovered', 0)}")
        print()
        
        # Show what was added to database
        print("💾 Database Additions:")
        print(f"   Entity resolution decisions: {latest_run['entity_decisions_count']}")
        print(f"   Relationship resolution decisions: {latest_run['relationship_decisions_count']}")  
        print(f"   Discovered connections: {latest_run['discovered_connections_count']}")
        print()
        
        # Show top entity resolution decisions
        if latest_run['entity_decisions_count'] > 0:
            print("🔗 Top Entity Merges:")
            with db.get_session() as session:
                from db.schema import EntityResolutionDecisionDB
                decisions = session.query(EntityResolutionDecisionDB).filter(
                    EntityResolutionDecisionDB.resolution_run_id == run_id
                ).order_by(EntityResolutionDecisionDB.similarity_score.desc()).limit(3).all()
                
                for i, decision in enumerate(decisions, 1):
                    duplicates_count = len(decision.duplicate_entity_ids)
                    print(f"   {i}. Canonical: {decision.canonical_entity_id}")
                    print(f"      Merged {duplicates_count} duplicate(s): {decision.duplicate_entity_ids}")
                    print(f"      Method: {decision.resolution_method}, Similarity: {decision.similarity_score:.3f}")
            print()
        
        # Show top discovered connections
        if latest_run['discovered_connections_count'] > 0:
            print("🎯 Top Discovered Connections:")
            discoveries = db.search_discoveries(
                resolution_run_id=run_id,
                limit=5
            )
            
            for i, discovery in enumerate(discoveries, 1):
                print(f"   {i}. {discovery['subject_entity_id']} --[{discovery['suggested_predicate']}]--> {discovery['object_entity_id']}")
                print(f"      Confidence: {discovery['confidence']:.3f}, Method: {discovery['discovery_method']}")
                if discovery['supporting_evidence']:
                    print(f"      Evidence: {discovery['supporting_evidence'][0]}")
            print()
        
        # Show discovery methods breakdown
        if latest_run['discovered_connections_count'] > 0:
            print("🔍 Discovery Methods Used:")
            with db.get_session() as session:
                from db.schema import ConnectionDiscoveryDB
                from sqlalchemy import func
                
                methods = session.query(
                    ConnectionDiscoveryDB.discovery_method,
                    func.count(ConnectionDiscoveryDB.id).label('count'),
                    func.avg(ConnectionDiscoveryDB.confidence).label('avg_confidence')
                ).filter(
                    ConnectionDiscoveryDB.resolution_run_id == run_id
                ).group_by(ConnectionDiscoveryDB.discovery_method).all()
                
                for method, count, avg_conf in methods:
                    print(f"   {method}: {count} discoveries (avg confidence: {avg_conf:.3f})")
            print()
        
        # Show comparison with previous run if available
        if len(runs) > 1:
            prev_run = runs[1]
            print("📈 Comparison with Previous Run:")
            print(f"   Entity decisions: {latest_run['entity_decisions_count']} vs {prev_run['entity_decisions_count']} ({latest_run['entity_decisions_count'] - prev_run['entity_decisions_count']:+d})")
            print(f"   Relationship decisions: {latest_run['relationship_decisions_count']} vs {prev_run['relationship_decisions_count']} ({latest_run['relationship_decisions_count'] - prev_run['relationship_decisions_count']:+d})")
            print(f"   Discoveries: {latest_run['discovered_connections_count']} vs {prev_run['discovered_connections_count']} ({latest_run['discovered_connections_count'] - prev_run['discovered_connections_count']:+d})")
            print()
        
        print("✅ Resolution run analysis complete!")
        
    except Exception as e:
        print(f"❌ Error analyzing resolution run: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()