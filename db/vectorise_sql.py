import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import create_database_interface
from sqlalchemy import inspect, text

import pandas as pd
import chromadb

db = create_database_interface()

time1 = time.time()
client = chromadb.PersistentClient(path="chroma")
time2 = time.time()
print(f"ChromaDB client initialized in {time2 - time1:.2f} seconds")

time3 = time.time()
collection = client.get_or_create_collection(name="my_documents")
time4 = time.time()
print(f"ChromaDB collection accessed in {time4 - time3:.2f}")
# Found 9 tables: chunks, connection_discoveries, entities, entity_resolution_decisions, extraction_runs, relationship_resolution_decisions, relationships, resolution_runs, triplets

with db.get_session() as session:
    # Get table info using SQLAlchemy inspector
    inspector = inspect(db.engine)
    table_names = inspector.get_table_names()
    # print(f"Found {len(table_names)} tables: {', '.join(table_names)}")
    df = pd.read_sql(
        text("SELECT * FROM entities where description like '%conversion%'"),
        db.engine,
    )
    print(df)
    # for c in df.columns:
    #    print(f"Column: {c}")
    #    print(df[c])
    # print("------")
    # print(df["description"])
    # documents = df["description"].tolist()
    # ids = df["id"].tolist()
    # print(ids)
    # collection.add(documents=documents, ids=ids)

"""
time5 = time.time()
results = collection.query(query_texts=["conversion rate"], n_results=2)
time6 = time.time()
print(f"ChromaDB query executed in {time6 - time5:.2f} seconds")
print(results)
"""
