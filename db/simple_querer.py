import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import create_database_interface
from sqlalchemy import inspect, text

import pandas as pd


db = create_database_interface()

# Found 9 tables: chunks, connection_discoveries, entities, entity_resolution_decisions, extraction_runs, relationship_resolution_decisions, relationships, resolution_runs, triplets

with db.get_session() as session:
    # Get table info using SQLAlchemy inspector
    inspector = inspect(db.engine)
    table_names = inspector.get_table_names()
    # print(f"Found {len(table_names)} tables: {', '.join(table_names)}")
    df = pd.read_sql(text("SELECT * FROM entities"), db.engine)
    print(df)
    for c in df.columns:
        print(f"Column: {c}")
        print(df[c])
    print("------")
    # df = pd.read_sql(text("SELECT * FROM relationships LIMIT 3"), db.engine)
    # print(df)
    # for c in df.columns:
    #    print(f"Column: {c}")
    #    print(df[c])
