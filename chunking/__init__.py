"""
Text chunking module for graphrag-again project.

This module provides functionality for chunking text files into paragraphs
for use in graph-based retrieval-augmented generation (GraphRAG) systems.
"""

from .chunker import Chunk, Chunker

__all__ = ['Chunk', 'Chunker']