"""Entity resolution using fuzzy matching for deduplication."""

import string
import uuid
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict

from rapidfuzz import fuzz

from entity_extraction.models import Entity, EntityType
from .models import EntityResolutionDecision, ResolutionActionType


class EntityResolver:
    """
    Entity resolver for deduplicating entities using fuzzy matching.
    
    Based on the EntityResolution class from the temporal agents notebook,
    adapted for the current project's data structures.
    """
    
    def __init__(
        self,
        similarity_threshold: float = 80.0,
        acronym_threshold: float = 98.0,
        enable_acronym_matching: bool = True
    ):
        """
        Initialize the entity resolver.
        
        Args:
            similarity_threshold: Minimum similarity score for considering entities as duplicates
            acronym_threshold: Higher threshold for acronym matching
            enable_acronym_matching: Whether to enable acronym-based matching
        """
        self.similarity_threshold = similarity_threshold
        self.acronym_threshold = acronym_threshold
        self.enable_acronym_matching = enable_acronym_matching
        self.canonical_entities: Dict[str, Entity] = {}  # entity_id -> canonical entity
        self.resolution_decisions: List[EntityResolutionDecision] = []
    
    def clean_entity_name(self, name: str) -> str:
        """Clean entity name for comparison."""
        return name.lower().strip().translate(str.maketrans("", "", string.punctuation))
    
    def resolve_entities(self, entities: List[Entity]) -> Tuple[List[Entity], List[EntityResolutionDecision]]:
        """
        Resolve entities by finding and merging duplicates.
        
        Args:
            entities: List of entities to resolve
            
        Returns:
            Tuple of (canonical_entities, resolution_decisions)
        """
        self.canonical_entities = {}
        self.resolution_decisions = []
        
        # Group entities by type for more accurate matching
        type_groups = self._group_entities_by_type(entities)
        
        for entity_type, type_entities in type_groups.items():
            self._resolve_entities_by_type(type_entities)
        
        # Handle acronym matching across all canonical entities
        if self.enable_acronym_matching:
            self._merge_acronym_entities()
        
        # Return the final canonical entities
        canonical_entities = list(self.canonical_entities.values())
        
        return canonical_entities, self.resolution_decisions
    
    def _group_entities_by_type(self, entities: List[Entity]) -> Dict[EntityType, List[Entity]]:
        """Group entities by their type."""
        type_groups = defaultdict(list)
        for entity in entities:
            type_groups[entity.type].append(entity)
        return dict(type_groups)
    
    def _resolve_entities_by_type(self, entities: List[Entity]) -> None:
        """Resolve entities within a single type group."""
        if not entities:
            return
        
        # Group entities by fuzzy name similarity
        similarity_clusters = self._group_entities_by_fuzzy_match(entities)
        
        for cluster_name, cluster_entities in similarity_clusters.items():
            if not cluster_entities:
                continue
                
            if len(cluster_entities) == 1:
                # Single entity - add directly as canonical
                entity = cluster_entities[0]
                self.canonical_entities[entity.id] = entity
            else:
                # Multiple entities - need to select canonical and merge
                self._resolve_entity_cluster(cluster_entities)
    
    def _group_entities_by_fuzzy_match(self, entities: List[Entity]) -> Dict[str, List[Entity]]:
        """
        Group entities by fuzzy name similarity using rapidfuzz.
        
        Returns a mapping from cluster representative name to list of grouped entities.
        """
        # Create name-to-entities mapping
        name_to_entities = defaultdict(list)
        cleaned_name_map = {}
        
        for entity in entities:
            name_to_entities[entity.name].append(entity)
            cleaned_name_map[entity.name] = self.clean_entity_name(entity.name)
        
        unique_names = list(name_to_entities.keys())
        clustered = {}
        used_names = set()
        
        for name in unique_names:
            if name in used_names:
                continue
                
            # Start a new cluster with this name
            cluster_entities = []
            cluster_used_names = set()
            
            for other_name in unique_names:
                if other_name in used_names:
                    continue
                    
                # Calculate similarity between cleaned names
                score = fuzz.partial_ratio(
                    cleaned_name_map[name], 
                    cleaned_name_map[other_name]
                )
                
                if score >= self.similarity_threshold:
                    cluster_entities.extend(name_to_entities[other_name])
                    cluster_used_names.add(other_name)
            
            if cluster_entities:
                clustered[name] = cluster_entities
                used_names.update(cluster_used_names)
        
        return clustered
    
    def _resolve_entity_cluster(self, cluster_entities: List[Entity]) -> None:
        """Resolve a cluster of similar entities by selecting a canonical one."""
        if not cluster_entities:
            return
        
        # Select the medoid (most representative) entity as canonical
        canonical_entity = self._select_medoid_entity(cluster_entities)
        
        if canonical_entity is None:
            return
        
        # Check if this canonical entity is similar to any existing canonical entity
        existing_match = self._find_matching_canonical_entity(canonical_entity)
        
        if existing_match:
            # Merge with existing canonical entity
            final_canonical_id = existing_match.id
            duplicate_ids = [e.id for e in cluster_entities]
        else:
            # This becomes a new canonical entity
            final_canonical_id = canonical_entity.id
            self.canonical_entities[canonical_entity.id] = canonical_entity
            duplicate_ids = [e.id for e in cluster_entities if e.id != canonical_entity.id]
        
        # Record the resolution decision if we have duplicates
        if duplicate_ids:
            decision = EntityResolutionDecision(
                id=str(uuid.uuid4()),
                canonical_entity_id=final_canonical_id,
                duplicate_entity_ids=duplicate_ids,
                similarity_score=self._calculate_cluster_similarity(cluster_entities),
                resolution_method="fuzzy_match_medoid",
                confidence=self._calculate_resolution_confidence(cluster_entities),
                metadata={
                    "cluster_size": len(cluster_entities),
                    "canonical_name": canonical_entity.name,
                    "duplicate_names": [e.name for e in cluster_entities if e.id != canonical_entity.id]
                }
            )
            self.resolution_decisions.append(decision)
    
    def _select_medoid_entity(self, entities: List[Entity]) -> Optional[Entity]:
        """
        Select the medoid entity - the one with highest total similarity to all others.
        
        Args:
            entities: List of entities in the cluster
            
        Returns:
            The medoid entity or None if empty list
        """
        if not entities:
            return None
        
        if len(entities) == 1:
            return entities[0]
        
        n = len(entities)
        similarity_scores = [0.0] * n
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    cleaned_i = self.clean_entity_name(entities[i].name)
                    cleaned_j = self.clean_entity_name(entities[j].name)
                    similarity_scores[i] += fuzz.partial_ratio(cleaned_i, cleaned_j)
        
        # Select entity with highest total similarity score
        max_idx = max(range(n), key=lambda idx: similarity_scores[idx])
        
        # Also consider confidence score as a tiebreaker
        medoid = entities[max_idx]
        
        # If there are entities with similar similarity scores, prefer higher confidence
        max_score = similarity_scores[max_idx]
        candidates = [
            entities[i] for i in range(n) 
            if abs(similarity_scores[i] - max_score) < 10.0  # Within 10 points
        ]
        
        if len(candidates) > 1:
            # Choose the one with highest confidence
            medoid = max(candidates, key=lambda e: e.confidence)
        
        return medoid
    
    def _find_matching_canonical_entity(self, entity: Entity) -> Optional[Entity]:
        """Find if this entity matches any existing canonical entity."""
        cleaned_name = self.clean_entity_name(entity.name)
        
        best_score = 0.0
        best_canonical = None
        
        for canonical in self.canonical_entities.values():
            if canonical.type != entity.type:
                continue
                
            canonical_cleaned = self.clean_entity_name(canonical.name)
            score = fuzz.partial_ratio(cleaned_name, canonical_cleaned)
            
            if score > best_score and score >= self.similarity_threshold:
                best_score = score
                best_canonical = canonical
        
        return best_canonical
    
    def _merge_acronym_entities(self) -> None:
        """Merge canonical entities where one is an acronym of another."""
        if not self.enable_acronym_matching:
            return
        
        canonical_list = list(self.canonical_entities.values())
        multi_word_entities = [e for e in canonical_list if " " in e.name]
        single_word_entities = [e for e in canonical_list if " " not in e.name]
        
        entities_to_remove = []
        
        for multi_word_entity in multi_word_entities:
            # Generate acronym from multi-word entity
            acronym = "".join(word[0].upper() for word in multi_word_entity.name.split())
            
            # Look for matching single-word entities
            for single_word_entity in single_word_entities:
                if single_word_entity.type != multi_word_entity.type:
                    continue
                    
                score = fuzz.ratio(acronym, single_word_entity.name.upper())
                
                if score >= self.acronym_threshold:
                    # Merge single-word entity into multi-word entity
                    decision = EntityResolutionDecision(
                        id=str(uuid.uuid4()),
                        canonical_entity_id=multi_word_entity.id,
                        duplicate_entity_ids=[single_word_entity.id],
                        similarity_score=score / 100.0,
                        resolution_method="acronym_match",
                        confidence=0.9,  # High confidence for acronym matches
                        metadata={
                            "acronym": acronym,
                            "full_form": multi_word_entity.name,
                            "acronym_form": single_word_entity.name
                        }
                    )
                    self.resolution_decisions.append(decision)
                    entities_to_remove.append(single_word_entity.id)
                    break
        
        # Remove merged entities from canonical entities
        for entity_id in entities_to_remove:
            if entity_id in self.canonical_entities:
                del self.canonical_entities[entity_id]
    
    def _calculate_cluster_similarity(self, entities: List[Entity]) -> float:
        """Calculate average similarity within a cluster."""
        if len(entities) < 2:
            return 1.0
        
        total_similarity = 0.0
        comparisons = 0
        
        for i in range(len(entities)):
            for j in range(i + 1, len(entities)):
                cleaned_i = self.clean_entity_name(entities[i].name)
                cleaned_j = self.clean_entity_name(entities[j].name)
                similarity = fuzz.partial_ratio(cleaned_i, cleaned_j)
                total_similarity += similarity
                comparisons += 1
        
        return (total_similarity / comparisons) / 100.0 if comparisons > 0 else 1.0
    
    def _calculate_resolution_confidence(self, entities: List[Entity]) -> float:
        """Calculate confidence in the resolution decision."""
        if len(entities) < 2:
            return 1.0
        
        # Base confidence on average entity confidence and similarity
        avg_entity_confidence = sum(e.confidence for e in entities) / len(entities)
        cluster_similarity = self._calculate_cluster_similarity(entities)
        
        # Weight both factors
        confidence = (avg_entity_confidence + cluster_similarity) / 2.0
        
        # Boost confidence for higher similarity
        if cluster_similarity > 0.9:
            confidence = min(1.0, confidence + 0.1)
        
        return confidence