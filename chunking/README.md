# Text Chunking Module

This module provides text chunking functionality for the graphrag-again project, designed to process text files and break them into paragraph-based chunks suitable for GraphRAG (Graph Retrieval-Augmented Generation) systems.

## Overview

The chunker processes text files from the `sources/` directory and creates structured chunks with metadata. It's designed to handle various document formats and extract meaningful paragraphs for downstream processing.

## Files

- `chunker.py` - Core chunking implementation
- `__init__.py` - Module initialization and exports
- `run_chunker.py` - Standalone script to test and run the chunker
- `README.md` - This documentation file

## Core Components

### `Chunk` Class
A dataclass representing a text chunk with the following attributes:
- `id`: Unique identifier for the chunk
- `text`: The actual text content
- `metadata`: Dictionary containing chunk metadata

### `Chunker` Class
Main chunking class with the following key features:
- Document discovery from `sources/` directory
- Paragraph-based text splitting
- Metadata generation
- Support for `.txt` and `.md` files

## Document Structure

The chunker handles two types of document structures:

1. **Single Files**: Document name = filename (without extension)
   ```
   sources/
   ├── document1.txt
   └── document2.md
   ```

2. **Nested Directories**: Document name = deepest subdirectory name
   ```
   sources/
   └── extracted_texts/
       ├── company_a_texts/
       │   ├── page_1.txt
       │   └── page_2.txt
       └── company_b_texts/
           └── content.txt
   ```

## Paragraph Detection

The chunker uses a multi-criteria approach for paragraph identification:

1. **Primary Split**: Uses double line breaks (`\n\n`) to identify paragraph boundaries
2. **Text Cleaning**: Normalizes whitespace and removes empty lines
3. **Size Filtering**: Filters out very short text fragments (< 10 characters)
4. **Smart Merging**: Combines short fragments (< 50 characters) with adjacent content
5. **Content Validation**: Only processes files with actual content

## Metadata

Each chunk includes comprehensive metadata:
- `document_name`: Name derived from file/directory structure
- `source_file`: Full path to the source file
- `chunk_index`: Sequential number within the document
- `file_size`: Size of the original file in bytes
- `chunk_length`: Character count of the chunk text

## Usage

### As a Module

```python
from chunking import Chunker

# Create chunker instance
chunker = Chunker()

# Generate chunks from all sources
chunks = chunker.generate_chunks()

if chunks:
    for chunk in chunks:
        print(f"ID: {chunk.id}")
        print(f"Text: {chunk.text[:100]}...")
        print(f"Metadata: {chunk.metadata}")
```

### Custom Sources Directory

```python
chunker = Chunker(sources_dir="custom/path/to/sources")
chunks = chunker.generate_chunks()
```

### Standalone Script

Run the chunker directly from the chunking directory:

```bash
cd chunking
uv run python run_chunker.py
```

Or from the project root:

```bash
uv run python chunking/run_chunker.py
```

## Example Output

```
Text Chunker - Processing files from sources directory
============================================================

✓ Generated 155 chunks total from all documents

Sample chunks (21-22):
----------------------------------------
Chunk 21:
  ID: chunk_21
  Document: engagebay_texts
  Source: engagebay_page_23.txt
  Length: 738 chars
  Text: 'Source: Marketing Charts When customers respond to your survey...'

Document Summary:
----------------------------------------
  agencyanalytics_texts: 42 chunks
  databox_texts: 31 chunks
  engagebay_texts: 35 chunks
  ...
```

## Future Enhancements

- **Metadata Extraction**: Enhanced metadata extraction from filenames and content
- **Custom Chunking Strategies**: Support for different chunking algorithms
- **Format Support**: Additional file format support beyond `.txt` and `.md`
- **Chunk Size Control**: Configurable minimum/maximum chunk sizes
- **Language Detection**: Language-aware paragraph detection

## Dependencies

The module uses only Python standard library components:
- `pathlib` - File system operations
- `dataclasses` - Chunk data structure
- `re` - Regular expressions for text processing
- `os` - Operating system interface
- `typing` - Type hints

No external dependencies required.