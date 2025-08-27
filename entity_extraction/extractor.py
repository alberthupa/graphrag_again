"""Entity extraction functionality using OpenAI API."""

import argparse
import json
import uuid
from typing import List, Dict, Any, Optional
from openai import OpenAI
from pydantic import ValidationError

try:
    from .models import Entity, Relationship, EntityType, PredicateType, ExtractionResult
    from .entity_types import get_extraction_prompt_context, ENTITY_TYPE_CONFIGS
except ImportError:
    from models import Entity, Relationship, EntityType, PredicateType, ExtractionResult
    from entity_types import get_extraction_prompt_context, ENTITY_TYPE_CONFIGS


class EntityExtractor:
    """Extracts entities and relationships from text chunks using OpenAI API."""
    
    def __init__(self, openai_api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """Initialize the entity extractor.
        
        Args:
            openai_api_key: OpenAI API key. If None, will use environment variable.
            model: OpenAI model to use for extraction.
        """
        self.client = OpenAI(api_key=openai_api_key)
        self.model = model
        
    def _create_extraction_prompt(self, text: str) -> str:
        """Create a structured prompt for entity and relationship extraction."""
        entity_context = get_extraction_prompt_context()
        
        return f"""You are an expert data analyst specializing in extracting structured information from business and data engineering texts.

Your task is to extract entities and relationships from the provided text. Focus on identifying key business concepts, data structures, metrics, and their relationships.

## Entity Types to Extract:
{entity_context}

## Relationship Types:
- hasDefinition: Entity has a definition or explanation
- calculatedBy: Entity is calculated using a formula/method
- belongsTo: Entity belongs to a domain or category
- contains: Entity contains other entities (e.g., table contains columns)
- hasType: Entity has a specific data type
- dependsOn: Entity depends on other entities
- derivedFrom: Entity is derived from other entities
- measures: Entity measures or quantifies something
- locatedIn: Entity is located in a system or location

## Instructions:
1. Read the text carefully and identify all relevant entities
2. For each entity, determine its type, name, and key attributes
3. Identify relationships between entities
4. Assign confidence scores (0.0-1.0) based on how certain you are about each extraction
5. Return the results in the exact JSON format specified below

## Text to analyze:
{text}

## Required JSON Response Format:
{{
    "entities": [
        {{
            "id": "unique_id",
            "type": "EntityType",
            "name": "Entity Name",
            "description": "Brief description",
            "confidence": 0.95,
            "attributes": {{
                "key": "value"
            }}
        }}
    ],
    "relationships": [
        {{
            "id": "unique_relationship_id",
            "subject_id": "subject_entity_id",
            "predicate": "PredicateType", 
            "object_id": "object_entity_id",
            "confidence": 0.90,
            "context": "Context where relationship was found"
        }}
    ]
}}

Respond only with valid JSON. Do not include any explanatory text before or after the JSON."""

    def _parse_extraction_response(self, response_content: str, chunk_id: str) -> tuple[List[Entity], List[Relationship]]:
        """Parse the OpenAI response and convert to Entity and Relationship objects."""
        try:
            data = json.loads(response_content.strip())
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            return [], []
        
        entities = []
        relationships = []
        
        # Parse entities
        for entity_data in data.get("entities", []):
            try:
                # Ensure entity has required fields
                if not all(key in entity_data for key in ["id", "type", "name", "confidence"]):
                    continue
                    
                # Validate entity type
                try:
                    entity_type = EntityType(entity_data["type"])
                except ValueError:
                    print(f"Unknown entity type: {entity_data['type']}")
                    continue
                
                entity = Entity(
                    id=entity_data["id"],
                    type=entity_type,
                    name=entity_data["name"],
                    description=entity_data.get("description"),
                    confidence=entity_data["confidence"],
                    attributes=entity_data.get("attributes", {}),
                    source_chunk_id=chunk_id
                )
                entities.append(entity)
            except (ValidationError, KeyError, TypeError) as e:
                print(f"Error parsing entity: {e}")
                continue
        
        # Parse relationships
        for rel_data in data.get("relationships", []):
            try:
                # Ensure relationship has required fields
                required_fields = ["id", "subject_id", "predicate", "object_id", "confidence"]
                if not all(key in rel_data for key in required_fields):
                    continue
                
                # Validate predicate type
                try:
                    predicate = PredicateType(rel_data["predicate"])
                except ValueError:
                    print(f"Unknown predicate type: {rel_data['predicate']}")
                    continue
                
                relationship = Relationship(
                    id=rel_data["id"],
                    subject_id=rel_data["subject_id"],
                    predicate=predicate,
                    object_id=rel_data["object_id"],
                    confidence=rel_data["confidence"],
                    context=rel_data.get("context"),
                    source_chunk_id=chunk_id
                )
                relationships.append(relationship)
            except (ValidationError, KeyError, TypeError) as e:
                print(f"Error parsing relationship: {e}")
                continue
        
        return entities, relationships
    
    def extract_from_chunk(self, chunk) -> tuple[List[Entity], List[Relationship]]:
        """Extract entities and relationships from a single chunk.
        
        Args:
            chunk: Chunk object from the chunking module
            
        Returns:
            Tuple of (entities, relationships) lists
        """
        if not chunk.text.strip():
            return [], []
        
        try:
            prompt = self._create_extraction_prompt(chunk.text)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a precise data extraction assistant. Always respond with valid JSON."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            response_content = response.choices[0].message.content
            return self._parse_extraction_response(response_content, chunk.id)
            
        except Exception as e:
            print(f"Error extracting from chunk {chunk.id}: {e}")
            return [], []
    
    def extract_from_chunks(self, chunks: List, debug_n_chunks: Optional[int] = None) -> ExtractionResult:
        """Extract entities and relationships from multiple chunks.
        
        Args:
            chunks: List of Chunk objects
            debug_n_chunks: Optional limit on number of chunks to process for debugging
            
        Returns:
            ExtractionResult containing all extracted entities, relationships, and metadata
        """
        all_entities = []
        all_relationships = []
        
        # Limit chunks for debug mode if specified
        if debug_n_chunks is not None:
            chunks = chunks[:debug_n_chunks]
            print(f"Debug mode: Processing only first {len(chunks)} chunks")
        
        for i, chunk in enumerate(chunks):
            print(f"Processing chunk {i+1}/{len(chunks)}: {chunk.id}")
            
            entities, relationships = self.extract_from_chunk(chunk)
            all_entities.extend(entities)
            all_relationships.extend(relationships)
        
        # Create extraction result
        extraction_result = ExtractionResult(
            entities=all_entities,
            relationships=all_relationships,
            triplets=[],  # Will be populated by TripletGenerator
            total_chunks_processed=len(chunks),
            extraction_stats={
                "total_entities": len(all_entities),
                "total_relationships": len(all_relationships),
                "entities_by_type": self._count_entities_by_type(all_entities),
                "relationships_by_predicate": self._count_relationships_by_predicate(all_relationships)
            }
        )
        
        return extraction_result
    
    def _count_entities_by_type(self, entities: List[Entity]) -> Dict[str, int]:
        """Count entities by type."""
        counts = {}
        for entity in entities:
            entity_type = entity.type.value
            counts[entity_type] = counts.get(entity_type, 0) + 1
        return counts
    
    def _count_relationships_by_predicate(self, relationships: List[Relationship]) -> Dict[str, int]:
        """Count relationships by predicate."""
        counts = {}
        for rel in relationships:
            predicate = rel.predicate.value
            counts[predicate] = counts.get(predicate, 0) + 1
        return counts


def main():
    """Command line interface for running entity extraction."""
    parser = argparse.ArgumentParser(description="Extract entities from text chunks")
    parser.add_argument("--debug-chunks", "-n", type=int, 
                       help="Debug mode: process only N chunks")
    
    args = parser.parse_args()
    
    # Your existing extraction logic would go here
    # This is just a placeholder for the CLI interface
    if args.debug_chunks:
        print(f"Debug mode enabled: will process only {args.debug_chunks} chunks")
    

if __name__ == "__main__":
    main()