"""Connection discovery for finding new potential relationships between entities."""

import uuid
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict, Counter
import math

from rapidfuzz import fuzz
from entity_extraction.models import Entity, Relationship, EntityType, PredicateType
from .models import ConnectionDiscovery


class ConnectionDiscoverer:
    """
    Discovers new potential connections between entities based on:
    1. Semantic similarity of names and descriptions
    2. Common attributes and properties
    3. Existing relationship patterns (transitive relationships)
    4. Domain-specific rules for KPIs, metrics, and data sources
    """
    
    def __init__(
        self,
        similarity_threshold: float = 0.6,
        description_weight: float = 0.4,
        name_weight: float = 0.6,
        enable_transitive_discovery: bool = True,
        enable_domain_rules: bool = True
    ):
        """
        Initialize the connection discoverer.
        
        Args:
            similarity_threshold: Minimum similarity for suggesting connections
            description_weight: Weight for description similarity
            name_weight: Weight for name similarity  
            enable_transitive_discovery: Whether to discover transitive relationships
            enable_domain_rules: Whether to apply domain-specific connection rules
        """
        self.similarity_threshold = similarity_threshold
        self.description_weight = description_weight
        self.name_weight = name_weight
        self.enable_transitive_discovery = enable_transitive_discovery
        self.enable_domain_rules = enable_domain_rules
        
        # Cache for relationship patterns
        self._relationship_patterns: Dict[Tuple[EntityType, EntityType], List[PredicateType]] = {}
        self._entity_connectivity: Dict[str, Set[str]] = defaultdict(set)
    
    def discover_connections(
        self, 
        entities: List[Entity], 
        existing_relationships: List[Relationship]
    ) -> List[ConnectionDiscovery]:
        """
        Discover new potential connections between entities.
        
        Args:
            entities: List of entities to analyze
            existing_relationships: Existing relationships to consider
            
        Returns:
            List of discovered potential connections
        """
        discoveries = []
        
        # Build connectivity maps from existing relationships
        self._build_connectivity_maps(entities, existing_relationships)
        
        # Extract relationship patterns
        self._extract_relationship_patterns(existing_relationships, entities)
        
        # Method 1: Similarity-based discovery
        similarity_discoveries = self._discover_by_similarity(entities, existing_relationships)
        discoveries.extend(similarity_discoveries)
        
        # Method 2: Transitive relationship discovery
        if self.enable_transitive_discovery:
            transitive_discoveries = self._discover_transitive_relationships(entities, existing_relationships)
            discoveries.extend(transitive_discoveries)
        
        # Method 3: Domain-specific rules
        if self.enable_domain_rules:
            domain_discoveries = self._discover_by_domain_rules(entities, existing_relationships)
            discoveries.extend(domain_discoveries)
        
        # Method 4: Pattern-based discovery
        pattern_discoveries = self._discover_by_patterns(entities, existing_relationships)
        discoveries.extend(pattern_discoveries)
        
        # Remove duplicates and sort by confidence
        unique_discoveries = self._deduplicate_discoveries(discoveries)
        unique_discoveries.sort(key=lambda d: d.confidence, reverse=True)
        
        return unique_discoveries
    
    def _build_connectivity_maps(self, entities: List[Entity], relationships: List[Relationship]) -> None:
        """Build maps of entity connectivity."""
        self._entity_connectivity.clear()
        
        # Build entity ID to entity mapping
        entity_map = {e.id: e for e in entities}
        
        # Build connectivity graph
        for rel in relationships:
            if rel.subject_id in entity_map and rel.object_id in entity_map:
                self._entity_connectivity[rel.subject_id].add(rel.object_id)
                self._entity_connectivity[rel.object_id].add(rel.subject_id)  # Bidirectional
    
    def _extract_relationship_patterns(self, relationships: List[Relationship], entities: List[Entity]) -> None:
        """Extract common relationship patterns between entity types."""
        self._relationship_patterns.clear()
        
        entity_map = {e.id: e for e in entities}
        pattern_counter = defaultdict(list)
        
        for rel in relationships:
            subject_entity = entity_map.get(rel.subject_id)
            object_entity = entity_map.get(rel.object_id)
            
            if subject_entity and object_entity:
                type_pair = (subject_entity.type, object_entity.type)
                pattern_counter[type_pair].append(rel.predicate)
        
        # Store most common predicates for each entity type pair
        for type_pair, predicates in pattern_counter.items():
            predicate_counts = Counter(predicates)
            common_predicates = [pred for pred, count in predicate_counts.most_common(3)]
            self._relationship_patterns[type_pair] = common_predicates
    
    def _discover_by_similarity(
        self, 
        entities: List[Entity], 
        existing_relationships: List[Relationship]
    ) -> List[ConnectionDiscovery]:
        """Discover connections based on entity similarity."""
        discoveries = []
        existing_pairs = self._get_existing_entity_pairs(existing_relationships)
        
        for i, entity1 in enumerate(entities):
            for entity2 in entities[i + 1:]:
                # Skip if relationship already exists
                if self._entities_connected(entity1.id, entity2.id, existing_pairs):
                    continue
                
                # Calculate similarity
                similarity_score, similarity_features = self._calculate_entity_similarity(entity1, entity2)
                
                if similarity_score >= self.similarity_threshold:
                    # Suggest predicate based on entity types and similarity
                    suggested_predicate = self._suggest_predicate_from_similarity(
                        entity1, entity2, similarity_features
                    )
                    
                    if suggested_predicate:
                        discovery = ConnectionDiscovery(
                            id=str(uuid.uuid4()),
                            subject_entity_id=entity1.id,
                            object_entity_id=entity2.id,
                            suggested_predicate=suggested_predicate,
                            confidence=similarity_score,
                            discovery_method="similarity_analysis",
                            supporting_evidence=[
                                f"Name similarity: {similarity_features.get('name_similarity', 0):.2f}",
                                f"Description similarity: {similarity_features.get('description_similarity', 0):.2f}",
                                f"Attribute overlap: {similarity_features.get('attribute_overlap', 0):.2f}"
                            ],
                            similarity_features=similarity_features,
                            metadata={
                                "entity1_name": entity1.name,
                                "entity2_name": entity2.name,
                                "entity1_type": entity1.type.value,
                                "entity2_type": entity2.type.value
                            }
                        )
                        discoveries.append(discovery)
        
        return discoveries
    
    def _discover_transitive_relationships(
        self, 
        entities: List[Entity], 
        existing_relationships: List[Relationship]
    ) -> List[ConnectionDiscovery]:
        """Discover transitive relationships (A->B, B->C implies A->C)."""
        discoveries = []
        entity_map = {e.id: e for e in entities}
        existing_pairs = self._get_existing_entity_pairs(existing_relationships)
        
        # Build relationship graph
        outgoing_relations = defaultdict(list)
        for rel in existing_relationships:
            outgoing_relations[rel.subject_id].append((rel.object_id, rel.predicate))
        
        for entity1 in entities:
            # Find entities connected to entity1
            for intermediate_id, pred1 in outgoing_relations[entity1.id]:
                # Find entities connected to the intermediate entity
                for target_id, pred2 in outgoing_relations[intermediate_id]:
                    # Skip if target is the original entity (avoid cycles)
                    if target_id == entity1.id:
                        continue
                    
                    # Skip if direct relationship already exists
                    if self._entities_connected(entity1.id, target_id, existing_pairs):
                        continue
                    
                    target_entity = entity_map.get(target_id)
                    intermediate_entity = entity_map.get(intermediate_id)
                    
                    if target_entity and intermediate_entity:
                        # Determine if this transitive relationship makes sense
                        transitive_predicate = self._infer_transitive_predicate(pred1, pred2)
                        
                        if transitive_predicate:
                            # Calculate confidence based on the strength of intermediate relationships
                            confidence = self._calculate_transitive_confidence(
                                entity1, intermediate_entity, target_entity, existing_relationships
                            )
                            
                            discovery = ConnectionDiscovery(
                                id=str(uuid.uuid4()),
                                subject_entity_id=entity1.id,
                                object_entity_id=target_id,
                                suggested_predicate=transitive_predicate,
                                confidence=confidence,
                                discovery_method="transitive_inference",
                                supporting_evidence=[
                                    f"{entity1.name} --[{pred1.value}]--> {intermediate_entity.name}",
                                    f"{intermediate_entity.name} --[{pred2.value}]--> {target_entity.name}",
                                    f"Inferred: {entity1.name} --[{transitive_predicate.value}]--> {target_entity.name}"
                                ],
                                similarity_features={
                                    "transitive_strength": confidence
                                },
                                metadata={
                                    "intermediate_entity_id": intermediate_id,
                                    "intermediate_entity_name": intermediate_entity.name,
                                    "path_predicates": [pred1.value, pred2.value]
                                }
                            )
                            discoveries.append(discovery)
        
        return discoveries
    
    def _discover_by_domain_rules(
        self, 
        entities: List[Entity], 
        existing_relationships: List[Relationship]
    ) -> List[ConnectionDiscovery]:
        """Discover connections using domain-specific rules."""
        discoveries = []
        existing_pairs = self._get_existing_entity_pairs(existing_relationships)
        
        # Group entities by type
        entities_by_type = defaultdict(list)
        for entity in entities:
            entities_by_type[entity.type].append(entity)
        
        # Rule 1: KPIs should be connected to Metrics
        if EntityType.KPI in entities_by_type and EntityType.METRIC in entities_by_type:
            discoveries.extend(self._apply_kpi_metric_rules(
                entities_by_type[EntityType.KPI],
                entities_by_type[EntityType.METRIC],
                existing_pairs
            ))
        
        # Rule 2: Metrics should be connected to Tables/Columns
        if EntityType.METRIC in entities_by_type:
            table_entities = entities_by_type.get(EntityType.TABLE, [])
            column_entities = entities_by_type.get(EntityType.COLUMN, [])
            
            if table_entities:
                discoveries.extend(self._apply_metric_table_rules(
                    entities_by_type[EntityType.METRIC],
                    table_entities,
                    existing_pairs
                ))
            
            if column_entities:
                discoveries.extend(self._apply_metric_column_rules(
                    entities_by_type[EntityType.METRIC],
                    column_entities,
                    existing_pairs
                ))
        
        # Rule 3: Formulas should be connected to Metrics/KPIs
        if EntityType.FORMULA in entities_by_type:
            formula_entities = entities_by_type[EntityType.FORMULA]
            
            for target_type in [EntityType.KPI, EntityType.METRIC]:
                if target_type in entities_by_type:
                    discoveries.extend(self._apply_formula_rules(
                        formula_entities,
                        entities_by_type[target_type],
                        existing_pairs
                    ))
        
        return discoveries
    
    def _discover_by_patterns(
        self, 
        entities: List[Entity], 
        existing_relationships: List[Relationship]
    ) -> List[ConnectionDiscovery]:
        """Discover connections based on learned relationship patterns."""
        discoveries = []
        existing_pairs = self._get_existing_entity_pairs(existing_relationships)
        
        for entity1 in entities:
            for entity2 in entities:
                if entity1.id == entity2.id:
                    continue
                
                if self._entities_connected(entity1.id, entity2.id, existing_pairs):
                    continue
                
                # Check if we have patterns for this entity type combination
                type_pair = (entity1.type, entity2.type)
                common_predicates = self._relationship_patterns.get(type_pair, [])
                
                if common_predicates:
                    # Use the most common predicate for this type pair
                    suggested_predicate = common_predicates[0]
                    
                    # Calculate confidence based on pattern frequency and entity similarity
                    pattern_confidence = self._calculate_pattern_confidence(
                        entity1, entity2, type_pair, common_predicates
                    )
                    
                    if pattern_confidence >= self.similarity_threshold:
                        discovery = ConnectionDiscovery(
                            id=str(uuid.uuid4()),
                            subject_entity_id=entity1.id,
                            object_entity_id=entity2.id,
                            suggested_predicate=suggested_predicate,
                            confidence=pattern_confidence,
                            discovery_method="pattern_matching",
                            supporting_evidence=[
                                f"Common pattern: {entity1.type.value} --[{suggested_predicate.value}]--> {entity2.type.value}",
                                f"Pattern frequency: {len(self._relationship_patterns.get(type_pair, []))}"
                            ],
                            similarity_features={
                                "pattern_strength": pattern_confidence,
                                "pattern_frequency": len(common_predicates)
                            },
                            metadata={
                                "entity_type_pair": [entity1.type.value, entity2.type.value],
                                "available_patterns": [p.value for p in common_predicates]
                            }
                        )
                        discoveries.append(discovery)
        
        return discoveries
    
    def _calculate_entity_similarity(self, entity1: Entity, entity2: Entity) -> Tuple[float, Dict[str, float]]:
        """Calculate similarity between two entities."""
        features = {}
        
        # Name similarity
        name_sim = fuzz.partial_ratio(entity1.name.lower(), entity2.name.lower()) / 100.0
        features["name_similarity"] = name_sim
        
        # Description similarity
        desc_sim = 0.0
        if entity1.description and entity2.description:
            desc_sim = fuzz.partial_ratio(entity1.description.lower(), entity2.description.lower()) / 100.0
        features["description_similarity"] = desc_sim
        
        # Attribute overlap
        attr_sim = self._calculate_attribute_similarity(entity1.attributes, entity2.attributes)
        features["attribute_overlap"] = attr_sim
        
        # Type compatibility boost
        type_boost = 1.0 if entity1.type == entity2.type else 0.8
        features["type_compatibility"] = type_boost
        
        # Overall similarity
        overall_similarity = (
            name_sim * self.name_weight +
            desc_sim * self.description_weight +
            attr_sim * 0.2
        ) * type_boost
        
        return overall_similarity, features
    
    def _calculate_attribute_similarity(self, attrs1: Dict, attrs2: Dict) -> float:
        """Calculate similarity between attribute dictionaries."""
        if not attrs1 or not attrs2:
            return 0.0
        
        common_keys = set(attrs1.keys()) & set(attrs2.keys())
        if not common_keys:
            return 0.0
        
        total_similarity = 0.0
        for key in common_keys:
            val1, val2 = str(attrs1[key]).lower(), str(attrs2[key]).lower()
            if val1 == val2:
                total_similarity += 1.0
            else:
                total_similarity += fuzz.ratio(val1, val2) / 100.0
        
        return total_similarity / len(common_keys)
    
    def _get_existing_entity_pairs(self, relationships: List[Relationship]) -> Set[Tuple[str, str]]:
        """Get set of existing entity pairs (bidirectional)."""
        pairs = set()
        for rel in relationships:
            pairs.add((rel.subject_id, rel.object_id))
            pairs.add((rel.object_id, rel.subject_id))  # Bidirectional
        return pairs
    
    def _entities_connected(self, entity1_id: str, entity2_id: str, existing_pairs: Set[Tuple[str, str]]) -> bool:
        """Check if two entities are already connected."""
        return (entity1_id, entity2_id) in existing_pairs
    
    def _suggest_predicate_from_similarity(
        self, 
        entity1: Entity, 
        entity2: Entity, 
        similarity_features: Dict[str, float]
    ) -> Optional[PredicateType]:
        """Suggest a predicate based on entity similarity analysis."""
        # Domain-specific predicate suggestions based on entity types
        type_pair = (entity1.type, entity2.type)
        
        # Use learned patterns if available
        if type_pair in self._relationship_patterns:
            return self._relationship_patterns[type_pair][0]
        
        # Default suggestions based on types
        default_suggestions = {
            (EntityType.KPI, EntityType.METRIC): PredicateType.DEPENDS_ON,
            (EntityType.METRIC, EntityType.FORMULA): PredicateType.CALCULATED_BY,
            (EntityType.METRIC, EntityType.TABLE): PredicateType.DERIVED_FROM,
            (EntityType.COLUMN, EntityType.TABLE): PredicateType.BELONGS_TO,
            (EntityType.DEFINITION, EntityType.KPI): PredicateType.HAS_DEFINITION,
        }
        
        return default_suggestions.get(type_pair, PredicateType.DEPENDS_ON)
    
    def _infer_transitive_predicate(self, pred1: PredicateType, pred2: PredicateType) -> Optional[PredicateType]:
        """Infer a transitive predicate from two consecutive predicates."""
        transitive_rules = {
            (PredicateType.BELONGS_TO, PredicateType.BELONGS_TO): PredicateType.BELONGS_TO,
            (PredicateType.DEPENDS_ON, PredicateType.DEPENDS_ON): PredicateType.DEPENDS_ON,
            (PredicateType.DERIVED_FROM, PredicateType.DERIVED_FROM): PredicateType.DERIVED_FROM,
            (PredicateType.CONTAINS, PredicateType.BELONGS_TO): PredicateType.CONTAINS,
            (PredicateType.HAS_DEFINITION, PredicateType.DEPENDS_ON): PredicateType.HAS_DEFINITION,
        }
        
        return transitive_rules.get((pred1, pred2))
    
    def _calculate_transitive_confidence(
        self, 
        entity1: Entity, 
        intermediate: Entity, 
        entity2: Entity,
        relationships: List[Relationship]
    ) -> float:
        """Calculate confidence for a transitive relationship."""
        # Find the constituent relationships
        rel1_confidence = 0.0
        rel2_confidence = 0.0
        
        for rel in relationships:
            if rel.subject_id == entity1.id and rel.object_id == intermediate.id:
                rel1_confidence = max(rel1_confidence, rel.confidence)
            elif rel.subject_id == intermediate.id and rel.object_id == entity2.id:
                rel2_confidence = max(rel2_confidence, rel.confidence)
        
        # Transitive confidence is generally lower than constituent relationships
        base_confidence = math.sqrt(rel1_confidence * rel2_confidence) * 0.8
        
        # Boost confidence if entity types are compatible
        if self._types_compatible_for_transitivity(entity1.type, entity2.type):
            base_confidence *= 1.1
        
        return min(1.0, base_confidence)
    
    def _types_compatible_for_transitivity(self, type1: EntityType, type2: EntityType) -> bool:
        """Check if entity types are compatible for transitive relationships."""
        compatible_pairs = {
            (EntityType.KPI, EntityType.METRIC),
            (EntityType.METRIC, EntityType.TABLE),
            (EntityType.COLUMN, EntityType.TABLE),
            (EntityType.FORMULA, EntityType.KPI),
        }
        
        return (type1, type2) in compatible_pairs or (type2, type1) in compatible_pairs
    
    def _apply_kpi_metric_rules(
        self, 
        kpi_entities: List[Entity], 
        metric_entities: List[Entity],
        existing_pairs: Set[Tuple[str, str]]
    ) -> List[ConnectionDiscovery]:
        """Apply domain rules for KPI-Metric connections."""
        discoveries = []
        
        for kpi in kpi_entities:
            for metric in metric_entities:
                if self._entities_connected(kpi.id, metric.id, existing_pairs):
                    continue
                
                # Check for name/description similarity
                similarity, features = self._calculate_entity_similarity(kpi, metric)
                
                if similarity >= self.similarity_threshold * 0.7:  # Lower threshold for domain rules
                    discovery = ConnectionDiscovery(
                        id=str(uuid.uuid4()),
                        subject_entity_id=kpi.id,
                        object_entity_id=metric.id,
                        suggested_predicate=PredicateType.DEPENDS_ON,
                        confidence=min(0.9, similarity * 1.1),
                        discovery_method="domain_rule_kpi_metric",
                        supporting_evidence=[
                            "Domain rule: KPIs typically depend on metrics",
                            f"Similarity score: {similarity:.2f}"
                        ],
                        similarity_features=features,
                        metadata={
                            "rule_type": "kpi_depends_on_metric",
                            "kpi_name": kpi.name,
                            "metric_name": metric.name
                        }
                    )
                    discoveries.append(discovery)
        
        return discoveries
    
    def _apply_metric_table_rules(
        self, 
        metric_entities: List[Entity], 
        table_entities: List[Entity],
        existing_pairs: Set[Tuple[str, str]]
    ) -> List[ConnectionDiscovery]:
        """Apply domain rules for Metric-Table connections."""
        discoveries = []
        
        for metric in metric_entities:
            for table in table_entities:
                if self._entities_connected(metric.id, table.id, existing_pairs):
                    continue
                
                similarity, features = self._calculate_entity_similarity(metric, table)
                
                if similarity >= self.similarity_threshold * 0.6:
                    discovery = ConnectionDiscovery(
                        id=str(uuid.uuid4()),
                        subject_entity_id=metric.id,
                        object_entity_id=table.id,
                        suggested_predicate=PredicateType.DERIVED_FROM,
                        confidence=min(0.85, similarity * 1.0),
                        discovery_method="domain_rule_metric_table",
                        supporting_evidence=[
                            "Domain rule: Metrics are typically derived from tables",
                            f"Similarity score: {similarity:.2f}"
                        ],
                        similarity_features=features,
                        metadata={
                            "rule_type": "metric_derived_from_table",
                            "metric_name": metric.name,
                            "table_name": table.name
                        }
                    )
                    discoveries.append(discovery)
        
        return discoveries
    
    def _apply_metric_column_rules(
        self, 
        metric_entities: List[Entity], 
        column_entities: List[Entity],
        existing_pairs: Set[Tuple[str, str]]
    ) -> List[ConnectionDiscovery]:
        """Apply domain rules for Metric-Column connections."""
        discoveries = []
        
        for metric in metric_entities:
            for column in column_entities:
                if self._entities_connected(metric.id, column.id, existing_pairs):
                    continue
                
                similarity, features = self._calculate_entity_similarity(metric, column)
                
                if similarity >= self.similarity_threshold * 0.7:
                    discovery = ConnectionDiscovery(
                        id=str(uuid.uuid4()),
                        subject_entity_id=metric.id,
                        object_entity_id=column.id,
                        suggested_predicate=PredicateType.MEASURES,
                        confidence=min(0.8, similarity * 1.0),
                        discovery_method="domain_rule_metric_column",
                        supporting_evidence=[
                            "Domain rule: Metrics typically measure specific columns",
                            f"Similarity score: {similarity:.2f}"
                        ],
                        similarity_features=features,
                        metadata={
                            "rule_type": "metric_measures_column",
                            "metric_name": metric.name,
                            "column_name": column.name
                        }
                    )
                    discoveries.append(discovery)
        
        return discoveries
    
    def _apply_formula_rules(
        self, 
        formula_entities: List[Entity], 
        target_entities: List[Entity],
        existing_pairs: Set[Tuple[str, str]]
    ) -> List[ConnectionDiscovery]:
        """Apply domain rules for Formula connections."""
        discoveries = []
        
        for formula in formula_entities:
            for target in target_entities:
                if self._entities_connected(formula.id, target.id, existing_pairs):
                    continue
                
                similarity, features = self._calculate_entity_similarity(formula, target)
                
                if similarity >= self.similarity_threshold * 0.6:
                    discovery = ConnectionDiscovery(
                        id=str(uuid.uuid4()),
                        subject_entity_id=target.id,  # Target is calculated by formula
                        object_entity_id=formula.id,
                        suggested_predicate=PredicateType.CALCULATED_BY,
                        confidence=min(0.8, similarity * 1.0),
                        discovery_method="domain_rule_formula",
                        supporting_evidence=[
                            f"Domain rule: {target.type.value}s can be calculated by formulas",
                            f"Similarity score: {similarity:.2f}"
                        ],
                        similarity_features=features,
                        metadata={
                            "rule_type": f"{target.type.value.lower()}_calculated_by_formula",
                            "formula_name": formula.name,
                            "target_name": target.name
                        }
                    )
                    discoveries.append(discovery)
        
        return discoveries
    
    def _calculate_pattern_confidence(
        self, 
        entity1: Entity, 
        entity2: Entity, 
        type_pair: Tuple[EntityType, EntityType],
        common_predicates: List[PredicateType]
    ) -> float:
        """Calculate confidence for pattern-based discovery."""
        # Base confidence from pattern frequency
        pattern_strength = min(1.0, len(common_predicates) / 10.0)  # Normalize to 0-1
        
        # Entity similarity boost
        similarity, _ = self._calculate_entity_similarity(entity1, entity2)
        
        # Combine pattern strength with entity similarity
        confidence = (pattern_strength * 0.6 + similarity * 0.4)
        
        return confidence
    
    def _deduplicate_discoveries(self, discoveries: List[ConnectionDiscovery]) -> List[ConnectionDiscovery]:
        """Remove duplicate discoveries, keeping the highest confidence one."""
        # Group by entity pair and predicate
        discovery_groups = defaultdict(list)
        
        for discovery in discoveries:
            key = (discovery.subject_entity_id, discovery.object_entity_id, discovery.suggested_predicate)
            discovery_groups[key].append(discovery)
        
        # Keep only the highest confidence discovery from each group
        unique_discoveries = []
        for group in discovery_groups.values():
            if len(group) == 1:
                unique_discoveries.append(group[0])
            else:
                # Keep the one with highest confidence
                best_discovery = max(group, key=lambda d: d.confidence)
                
                # Merge evidence from all discoveries in the group
                all_evidence = []
                all_methods = []
                
                for d in group:
                    all_evidence.extend(d.supporting_evidence)
                    all_methods.append(d.discovery_method)
                
                best_discovery.supporting_evidence = list(set(all_evidence))
                best_discovery.metadata["discovery_methods"] = list(set(all_methods))
                
                unique_discoveries.append(best_discovery)
        
        return unique_discoveries