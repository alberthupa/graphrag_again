from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any
import os
import re


@dataclass
class Chunk:
    """Represents a text chunk with metadata."""
    id: str
    text: str
    metadata: Dict[str, Any]


class Chunker:
    """Text chunker that processes files from sources directory."""
    
    def __init__(self, sources_dir: str = "sources"):
        self.sources_dir = Path(sources_dir)
        self.chunk_counter = 0
    
    def _discover_documents(self) -> Dict[str, List[Path]]:
        """Discover text files and organize them by document name."""
        documents = {}
        
        if not self.sources_dir.exists():
            return documents
        
        for file_path in self.sources_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in ['.txt', '.md']:
                if self._has_content(file_path):
                    doc_name = self._get_document_name(file_path)
                    if doc_name not in documents:
                        documents[doc_name] = []
                    documents[doc_name].append(file_path)
        
        return documents
    
    def _has_content(self, file_path: Path) -> bool:
        """Check if file has non-empty content."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().strip()
                return len(content) > 0
        except Exception:
            return False
    
    def _get_document_name(self, file_path: Path) -> str:
        """Extract document name based on file structure."""
        relative_path = file_path.relative_to(self.sources_dir)
        
        if len(relative_path.parts) == 1:
            return relative_path.stem
        else:
            return relative_path.parent.name
    
    def _extract_paragraphs(self, text: str) -> List[str]:
        """Extract paragraphs from text using multi-criteria approach."""
        text = text.strip()
        if not text:
            return []
        
        paragraphs = re.split(r'\n\s*\n', text)
        
        cleaned_paragraphs = []
        for para in paragraphs:
            para = re.sub(r'\s+', ' ', para.strip())
            if para and len(para) > 10:
                cleaned_paragraphs.append(para)
        
        merged_paragraphs = []
        for para in cleaned_paragraphs:
            if len(para) < 50 and merged_paragraphs:
                merged_paragraphs[-1] += " " + para
            else:
                merged_paragraphs.append(para)
        
        return merged_paragraphs
    
    def _create_chunk_metadata(self, doc_name: str, file_path: Path, 
                              chunk_index: int, chunk_text: str) -> Dict[str, Any]:
        """Create metadata for a chunk."""
        return {
            "document_name": doc_name,
            "source_file": str(file_path),
            "chunk_index": chunk_index,
            "file_size": file_path.stat().st_size,
            "chunk_length": len(chunk_text)
        }
    
    def generate_chunks(self) -> Optional[List[Chunk]]:
        """Generate chunks from all documents in sources directory."""
        documents = self._discover_documents()
        
        if not documents:
            return None
        
        all_chunks = []
        
        for doc_name, file_paths in documents.items():
            doc_chunks = []
            
            for file_path in file_paths:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    paragraphs = self._extract_paragraphs(content)
                    
                    for chunk_index, paragraph in enumerate(paragraphs):
                        chunk_id = f"chunk_{self.chunk_counter}"
                        self.chunk_counter += 1
                        
                        metadata = self._create_chunk_metadata(
                            doc_name, file_path, chunk_index, paragraph
                        )
                        
                        chunk = Chunk(
                            id=chunk_id,
                            text=paragraph,
                            metadata=metadata
                        )
                        
                        doc_chunks.append(chunk)
                
                except Exception as e:
                    continue
            
            all_chunks.extend(doc_chunks)
        
        return all_chunks if all_chunks else None