#!/usr/bin/env python3
"""Simple graph visualization script for knowledge graph triplets."""

import os
import sys
import networkx as nx
import matplotlib.pyplot as plt
from typing import List, Dict, Any
import logging

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.interface import create_database_interface

# Configure logging
logging.basicConfig(level=logging.WARNING)

def load_triplets_from_db() -> List[Dict[str, Any]]:
    """Load all triplets from the database."""
    try:
        # Create database interface
        db = create_database_interface()
        
        # Get all triplets
        triplets = db.search_triplets(limit=1000)  # Increase limit if needed
        
        print(f"Loaded {len(triplets)} triplets from database")
        return triplets
        
    except Exception as e:
        print(f"Error loading triplets: {e}")
        return []

def create_graph(triplets: List[Dict[str, Any]]) -> nx.DiGraph:
    """Create a NetworkX directed graph from triplets."""
    G = nx.DiGraph()
    
    for triplet in triplets:
        subject = triplet['subject_name']
        predicate = triplet['predicate']
        obj = triplet['object_name']
        confidence = triplet['confidence']
        
        # Add nodes
        G.add_node(subject)
        G.add_node(obj)
        
        # Add edge with predicate and confidence as attributes
        G.add_edge(subject, obj, predicate=predicate, confidence=confidence)
    
    print(f"Created graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
    return G

def visualize_graph(G: nx.DiGraph, save_path: str = None):
    """Visualize the graph using matplotlib."""
    if G.number_of_nodes() == 0:
        print("No nodes to visualize!")
        return
    
    # Set up the plot
    plt.figure(figsize=(12, 8))
    
    # Use spring layout for node positioning
    pos = nx.spring_layout(G, k=1, iterations=50)
    
    # Draw nodes
    nx.draw_networkx_nodes(G, pos, node_color='lightblue', 
                          node_size=500, alpha=0.8)
    
    # Draw edges
    nx.draw_networkx_edges(G, pos, edge_color='gray', 
                          arrows=True, arrowsize=20, alpha=0.6)
    
    # Draw labels
    nx.draw_networkx_labels(G, pos, font_size=8, font_weight='bold')
    
    # Draw edge labels (predicates)
    edge_labels = nx.get_edge_attributes(G, 'predicate')
    nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=6)
    
    plt.title("Knowledge Graph Visualization", fontsize=16, fontweight='bold')
    plt.axis('off')
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Graph saved to: {save_path}")
    else:
        plt.show()

def main():
    """Main visualization function."""
    print("Loading triplets from database...")
    triplets = load_triplets_from_db()
    
    if not triplets:
        print("No triplets found in database!")
        return
    
    print("Creating graph...")
    G = create_graph(triplets)
    
    print("Visualizing graph...")
    # Save to file in the db directory
    output_path = "db/knowledge_graph_visualization.png"
    visualize_graph(G, save_path=output_path)

if __name__ == "__main__":
    main()