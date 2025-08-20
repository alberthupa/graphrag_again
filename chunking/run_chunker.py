#!/usr/bin/env python3
"""
Standalone script to run the text chunker.

This script demonstrates how to use the Chunker class to process text files
from the sources directory and generate paragraph-based chunks.
"""

import sys
from pathlib import Path

# Add the parent directory to Python path so we can import from chunking
sys.path.insert(0, str(Path(__file__).parent.parent))

from chunking import Chunker


def main():
    """Run the chunker and display results."""
    print("Text Chunker - Processing files from sources directory")
    print("=" * 60)

    # Create chunker instance (sources directory is relative to project root)
    chunker = Chunker(sources_dir="sources")
    chunks = chunker.generate_chunks()

    if chunks is not None:
        print(f"\n✓ Generated {len(chunks)} chunks total from all documents")
        print("\nSample chunks (21-22):")
        print("-" * 40)

        # for i, chunk in enumerate(chunks[21:23]):
        for i, chunk in enumerate(chunks):
            if chunk.metadata["document_name"] == "table_schema":
                print(f"Chunk {i+21}:")
                print(f"  ID: {chunk.id}")
                print(f"  Document: {chunk.metadata['document_name']}")
                print(f"  Source: {Path(chunk.metadata['source_file']).name}")
                print(f"  Length: {chunk.metadata['chunk_length']} chars")
                print(
                    f"  Text: {repr(chunk.text[:150])}{'...' if len(chunk.text) > 150 else ''}"
                )
                print()

        # Display document summary
        print("Document Summary:")
        print("-" * 40)
        docs = {}
        for chunk in chunks:
            doc_name = chunk.metadata["document_name"]
            if doc_name not in docs:
                docs[doc_name] = 0
            docs[doc_name] += 1

        for doc_name, count in sorted(docs.items()):
            print(f"  {doc_name}: {count} chunks")

    else:
        print("❌ No chunks found. Check that text files exist in sources directory.")


if __name__ == "__main__":
    main()
