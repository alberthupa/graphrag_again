#!/usr/bin/env python3
"""
Simple script to peek into the SQLite database tables and show their contents.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import create_database_interface
from sqlalchemy import inspect, text
import json

def peek_database():
    """Peek into database tables and show sample data."""
    
    print("🗃️ Database Peek - Knowledge Graph Contents")
    print("=" * 60)
    
    try:
        # Create database interface
        db = create_database_interface()
        
        # Get database statistics first
        print("\n📊 Database Overview:")
        stats = db.get_database_stats()
        for key, value in stats.items():
            if isinstance(value, dict) and len(value) > 0:
                print(f"  {key}: {len(value)} types")
            else:
                print(f"  {key}: {value}")
        
        with db.get_session() as session:
            # Get table info using SQLAlchemy inspector
            inspector = inspect(db.engine)
            table_names = inspector.get_table_names()
            
            print(f"\n📋 Found {len(table_names)} tables: {', '.join(table_names)}")
            
            for table_name in table_names:
                print(f"\n🔍 Table: {table_name.upper()}")
                print("-" * 40)
                
                # Get column info
                columns = inspector.get_columns(table_name)
                print(f"Columns ({len(columns)}): {', '.join([col['name'] for col in columns])}")
                
                # Get sample data
                result = session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                count = result.scalar()
                print(f"Row count: {count}")
                
                if count > 0:
                    # Show first few rows
                    result = session.execute(text(f"SELECT * FROM {table_name} LIMIT 3"))
                    rows = result.fetchall()
                    
                    print(f"Sample data (first {len(rows)} rows):")
                    for i, row in enumerate(rows, 1):
                        print(f"  Row {i}:")
                        for col, value in zip([col['name'] for col in columns], row):
                            if isinstance(value, str) and len(value) > 100:
                                value = value[:100] + "..."
                            elif col in ['attributes', 'extraction_stats', 'config_used', 'triplet_metadata'] and value:
                                try:
                                    # Pretty print JSON fields
                                    if isinstance(value, str):
                                        value = json.loads(value)
                                    value = json.dumps(value, indent=2)[:200] + "..." if len(str(value)) > 200 else json.dumps(value, indent=2)
                                except:
                                    pass
                            print(f"    {col}: {value}")
                        print()
                else:
                    print("  (No data)")
        
        # Show some interesting queries
        print("\n🔍 Sample Queries:")
        print("-" * 40)
        
        # Top entities by confidence
        entities = db.search_entities(limit=5)
        print(f"Top 5 entities by confidence:")
        for entity in entities:
            print(f"  {entity['name']} ({entity['type']}) - confidence: {entity['confidence']:.2f}")
        
        # Sample triplets
        print(f"\nSample triplets:")
        triplets = db.search_triplets(limit=3)
        for triplet in triplets:
            print(f"  {triplet['subject_name']} --[{triplet['predicate']}]--> {triplet['object_name']} (confidence: {triplet['confidence']:.2f})")
        
    except Exception as e:
        print(f"❌ Error peeking into database: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    peek_database()