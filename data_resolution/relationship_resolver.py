"""Relationship resolution for deduplicating and consolidating relationships."""

import uuid
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

from entity_extraction.models import Relationship
from .models import RelationshipResolutionDecision, ResolutionActionType


class RelationshipResolver:
    """
    Relationship resolver for deduplicating and consolidating relationships.
    
    Handles:
    1. Exact duplicate removal
    2. Consolidating relationships between the same entities 
    3. Updating relationships when entities are merged
    4. Confidence score consolidation
    """
    
    def __init__(self, confidence_consolidation_method: str = "max"):
        """
        Initialize the relationship resolver.
        
        Args:
            confidence_consolidation_method: How to consolidate confidence scores
                - "max": Take the maximum confidence
                - "average": Average all confidence scores  
                - "weighted": Weighted average based on context length
        """
        self.confidence_consolidation_method = confidence_consolidation_method
        self.resolution_decisions: List[RelationshipResolutionDecision] = []
    
    def resolve_relationships(
        self, 
        relationships: List[Relationship],
        entity_id_mapping: Optional[Dict[str, str]] = None
    ) -> Tuple[List[Relationship], List[RelationshipResolutionDecision]]:
        """
        Resolve relationships by removing duplicates and consolidating.
        
        Args:
            relationships: List of relationships to resolve
            entity_id_mapping: Optional mapping from old entity IDs to canonical entity IDs
            
        Returns:
            Tuple of (resolved_relationships, resolution_decisions)
        """
        self.resolution_decisions = []
        
        # Step 1: Update relationship entity IDs if mapping provided
        updated_relationships = relationships
        if entity_id_mapping:
            updated_relationships = self._update_relationship_entity_ids(relationships, entity_id_mapping)
        
        # Step 2: Remove exact duplicates
        deduplicated_relationships = self._remove_exact_duplicates(updated_relationships)
        
        # Step 3: Consolidate relationships between same entity pairs
        consolidated_relationships = self._consolidate_similar_relationships(deduplicated_relationships)
        
        return consolidated_relationships, self.resolution_decisions
    
    def _update_relationship_entity_ids(
        self, 
        relationships: List[Relationship], 
        entity_id_mapping: Dict[str, str]
    ) -> List[Relationship]:
        """Update relationship entity IDs based on entity resolution mapping."""
        updated_relationships = []
        
        for relationship in relationships:
            # Update subject and object IDs if they were merged
            new_subject_id = entity_id_mapping.get(relationship.subject_id, relationship.subject_id)
            new_object_id = entity_id_mapping.get(relationship.object_id, relationship.object_id)
            
            # Create updated relationship if IDs changed
            if new_subject_id != relationship.subject_id or new_object_id != relationship.object_id:
                updated_relationship = Relationship(
                    id=relationship.id,
                    subject_id=new_subject_id,
                    predicate=relationship.predicate,
                    object_id=new_object_id,
                    confidence=relationship.confidence,
                    context=relationship.context,
                    source_chunk_id=relationship.source_chunk_id
                )
                updated_relationships.append(updated_relationship)
            else:
                updated_relationships.append(relationship)
        
        return updated_relationships
    
    def _remove_exact_duplicates(self, relationships: List[Relationship]) -> List[Relationship]:
        """Remove exact duplicate relationships."""
        # Group relationships by their canonical form (subject, predicate, object)
        canonical_groups = defaultdict(list)
        
        for relationship in relationships:
            canonical_key = (relationship.subject_id, relationship.predicate, relationship.object_id)
            canonical_groups[canonical_key].append(relationship)
        
        deduplicated = []
        
        for canonical_key, group_relationships in canonical_groups.items():
            if len(group_relationships) == 1:
                # No duplicates
                deduplicated.append(group_relationships[0])
            else:
                # Multiple relationships with same subject-predicate-object
                best_relationship = self._select_best_relationship(group_relationships)
                deduplicated.append(best_relationship)
                
                # Record the resolution decision
                duplicate_ids = [r.id for r in group_relationships if r.id != best_relationship.id]
                if duplicate_ids:
                    decision = RelationshipResolutionDecision(
                        id=str(uuid.uuid4()),
                        action=ResolutionActionType.KEEP_CANONICAL,
                        canonical_relationship_id=best_relationship.id,
                        merged_relationship_ids=duplicate_ids,
                        consolidated_confidence=best_relationship.confidence,
                        consolidation_method="exact_duplicate_removal",
                        metadata={
                            "canonical_form": f"{canonical_key[0]} --[{canonical_key[1]}]--> {canonical_key[2]}",
                            "duplicates_removed": len(duplicate_ids),
                            "consolidation_reason": "exact_subject_predicate_object_match"
                        }
                    )
                    self.resolution_decisions.append(decision)
        
        return deduplicated
    
    def _consolidate_similar_relationships(self, relationships: List[Relationship]) -> List[Relationship]:
        """Consolidate relationships that are semantically similar."""
        # Group relationships by entity pair (ignoring predicate direction and type)
        entity_pair_groups = defaultdict(list)
        
        for relationship in relationships:
            # Create bidirectional key to catch reverse relationships
            pair_key = tuple(sorted([relationship.subject_id, relationship.object_id]))
            entity_pair_groups[pair_key].append(relationship)
        
        consolidated = []
        
        for pair_key, group_relationships in entity_pair_groups.items():
            if len(group_relationships) == 1:
                # No consolidation needed
                consolidated.append(group_relationships[0])
            else:
                # Multiple relationships between same entity pair - analyze for consolidation
                consolidated_group = self._consolidate_relationship_group(group_relationships)
                consolidated.extend(consolidated_group)
        
        return consolidated
    
    def _consolidate_relationship_group(self, relationships: List[Relationship]) -> List[Relationship]:
        """Consolidate a group of relationships between the same entity pair."""
        if len(relationships) <= 1:
            return relationships
        
        # Group by predicate type
        predicate_groups = defaultdict(list)
        for rel in relationships:
            predicate_groups[rel.predicate].append(rel)
        
        consolidated = []
        
        for predicate, predicate_relationships in predicate_groups.items():
            if len(predicate_relationships) == 1:
                consolidated.append(predicate_relationships[0])
            else:
                # Multiple relationships with same predicate - consolidate them
                best_relationship = self._consolidate_predicate_group(predicate_relationships)
                consolidated.append(best_relationship)
        
        return consolidated
    
    def _consolidate_predicate_group(self, relationships: List[Relationship]) -> Relationship:
        """Consolidate relationships with the same subject, object, and predicate."""
        if len(relationships) == 1:
            return relationships[0]
        
        # Select the best base relationship
        base_relationship = self._select_best_relationship(relationships)
        
        # Consolidate confidence scores
        consolidated_confidence = self._consolidate_confidence_scores(relationships)
        
        # Merge contexts
        consolidated_context = self._merge_contexts(relationships)
        
        # Create consolidated relationship
        consolidated_relationship = Relationship(
            id=base_relationship.id,  # Keep the ID of the best relationship
            subject_id=base_relationship.subject_id,
            predicate=base_relationship.predicate,
            object_id=base_relationship.object_id,
            confidence=consolidated_confidence,
            context=consolidated_context,
            source_chunk_id=base_relationship.source_chunk_id
        )
        
        # Record the consolidation decision
        merged_ids = [r.id for r in relationships if r.id != base_relationship.id]
        if merged_ids:
            decision = RelationshipResolutionDecision(
                id=str(uuid.uuid4()),
                action=ResolutionActionType.CONSOLIDATE_RELATIONSHIPS,
                canonical_relationship_id=base_relationship.id,
                merged_relationship_ids=merged_ids,
                consolidated_confidence=consolidated_confidence,
                consolidation_method=f"predicate_group_{self.confidence_consolidation_method}",
                metadata={
                    "relationships_consolidated": len(relationships),
                    "confidence_method": self.confidence_consolidation_method,
                    "original_confidences": [r.confidence for r in relationships],
                    "contexts_merged": len([r for r in relationships if r.context])
                }
            )
            self.resolution_decisions.append(decision)
        
        return consolidated_relationship
    
    def _select_best_relationship(self, relationships: List[Relationship]) -> Relationship:
        """Select the best relationship from a group."""
        if len(relationships) == 1:
            return relationships[0]
        
        # Selection criteria (in order of priority):
        # 1. Highest confidence
        # 2. Most detailed context
        # 3. Most recent (by ID lexicographic order as proxy)
        
        best_relationship = max(relationships, key=lambda r: (
            r.confidence,
            len(r.context or ""),
            r.id
        ))
        
        return best_relationship
    
    def _consolidate_confidence_scores(self, relationships: List[Relationship]) -> float:
        """Consolidate confidence scores from multiple relationships."""
        if len(relationships) == 1:
            return relationships[0].confidence
        
        confidences = [r.confidence for r in relationships]
        
        if self.confidence_consolidation_method == "max":
            return max(confidences)
        elif self.confidence_consolidation_method == "average":
            return sum(confidences) / len(confidences)
        elif self.confidence_consolidation_method == "weighted":
            # Weight by context length
            weights = []
            for r in relationships:
                context_length = len(r.context or "")
                weight = max(1, context_length)  # Minimum weight of 1
                weights.append(weight)
            
            total_weight = sum(weights)
            weighted_sum = sum(conf * weight for conf, weight in zip(confidences, weights))
            return weighted_sum / total_weight if total_weight > 0 else sum(confidences) / len(confidences)
        else:
            # Default to max
            return max(confidences)
    
    def _merge_contexts(self, relationships: List[Relationship]) -> Optional[str]:
        """Merge context strings from multiple relationships."""
        contexts = [r.context for r in relationships if r.context and r.context.strip()]
        
        if not contexts:
            return None
        
        if len(contexts) == 1:
            return contexts[0]
        
        # Remove duplicates while preserving order
        unique_contexts = []
        seen = set()
        
        for context in contexts:
            context_lower = context.lower().strip()
            if context_lower not in seen:
                unique_contexts.append(context.strip())
                seen.add(context_lower)
        
        # Join with separator if multiple unique contexts
        if len(unique_contexts) > 1:
            return " | ".join(unique_contexts)
        else:
            return unique_contexts[0] if unique_contexts else None
    
    def get_consolidation_stats(self) -> Dict[str, int]:
        """Get statistics about the consolidation process."""
        stats = {
            "total_decisions": len(self.resolution_decisions),
            "exact_duplicates_removed": 0,
            "relationships_consolidated": 0,
            "canonical_kept": 0
        }
        
        for decision in self.resolution_decisions:
            if decision.action == ResolutionActionType.KEEP_CANONICAL:
                stats["canonical_kept"] += 1
                if "exact_duplicate_removal" in decision.consolidation_method:
                    stats["exact_duplicates_removed"] += len(decision.merged_relationship_ids)
            elif decision.action == ResolutionActionType.CONSOLIDATE_RELATIONSHIPS:
                stats["relationships_consolidated"] += len(decision.merged_relationship_ids)
        
        return stats