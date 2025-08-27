"""TripletGenerator class for converting entities and relationships into knowledge graph triplets."""

from typing import List, Dict, Any, Optional
from .models import Entity, Relationship, Triplet, ExtractionResult, EntityType, PredicateType


class TripletGenerator:
    """Generates knowledge graph triplets from entities and relationships."""
    
    def __init__(self, min_confidence: float = 0.3):
        """Initialize TripletGenerator with minimum confidence threshold."""
        self.min_confidence = min_confidence
    
    def generate_triplets(
        self, 
        extraction_result: ExtractionResult, 
        source_text_map: Optional[Dict[str, str]] = None
    ) -> List[Triplet]:
        """Generate triplets from entities and relationships."""
        triplets = []
        
        # Create entity lookup
        entity_lookup = {entity.id: entity for entity in extraction_result.entities}
        
        for relationship in extraction_result.relationships:
            if relationship.confidence < self.min_confidence:
                continue
                
            subject = entity_lookup.get(relationship.subject_id)
            obj = entity_lookup.get(relationship.object_id)
            
            if subject and obj:
                triplet = Triplet(
                    id=f"triplet_{len(triplets)}",
                    subject=subject,
                    predicate=relationship.predicate,
                    object=obj,
                    confidence=relationship.confidence,
                    context=relationship.context,
                    source_chunk_id=relationship.source_chunk_id
                )
                triplets.append(triplet)
        
        # Update extraction result
        extraction_result.triplets = triplets
        return triplets
    
    def generate_kpi_focused_triplets(
        self, 
        extraction_result: ExtractionResult, 
        source_text_map: Optional[Dict[str, str]] = None
    ) -> List[Triplet]:
        """Generate KPI-focused specialized triplets."""
        kpi_triplets = []
        
        # Create entity lookup
        entity_lookup = {entity.id: entity for entity in extraction_result.entities}
        
        # Find KPI entities
        kpi_entities = [e for e in extraction_result.entities if e.type == EntityType.KPI]
        
        for kpi_entity in kpi_entities:
            # Find relationships involving this KPI
            kpi_relationships = [
                r for r in extraction_result.relationships 
                if (r.subject_id == kpi_entity.id or r.object_id == kpi_entity.id)
                and r.confidence >= self.min_confidence
            ]
            
            for relationship in kpi_relationships:
                subject = entity_lookup.get(relationship.subject_id)
                obj = entity_lookup.get(relationship.object_id)
                
                if subject and obj:
                    triplet = Triplet(
                        id=f"kpi_triplet_{len(kpi_triplets)}",
                        subject=subject,
                        predicate=relationship.predicate,
                        object=obj,
                        confidence=relationship.confidence,
                        context=f"KPI-focused: {relationship.context}",
                        source_chunk_id=relationship.source_chunk_id
                    )
                    kpi_triplets.append(triplet)
        
        return kpi_triplets
    
    def export_triplets_summary(self, triplets: List[Triplet]) -> Dict[str, Any]:
        """Export summary statistics for generated triplets."""
        if not triplets:
            return {
                "total_triplets": 0,
                "average_confidence": 0.0,
                "unique_subjects": 0,
                "unique_objects": 0,
                "triplets_by_predicate": {}
            }
        
        # Calculate statistics
        total_confidence = sum(t.confidence for t in triplets)
        average_confidence = total_confidence / len(triplets)
        
        unique_subjects = len(set(t.subject.id for t in triplets))
        unique_objects = len(set(t.object.id for t in triplets))
        
        # Count triplets by predicate
        predicate_counts = {}
        for triplet in triplets:
            predicate = triplet.predicate.value
            predicate_counts[predicate] = predicate_counts.get(predicate, 0) + 1
        
        return {
            "total_triplets": len(triplets),
            "average_confidence": average_confidence,
            "unique_subjects": unique_subjects,
            "unique_objects": unique_objects,
            "triplets_by_predicate": predicate_counts
        }