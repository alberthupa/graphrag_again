#!/usr/bin/env python3
"""Interactive graph visualization script for knowledge graph triplets with customizable layouts."""

import os
import sys
import networkx as nx
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from typing import List, Dict, Any, Optional
import logging

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.interface import create_database_interface

# Configure logging
logging.basicConfig(level=logging.WARNING)


class InteractiveGraphVisualizer:
    """Interactive graph visualizer with customizable layouts and styling."""

    def __init__(self):
        self.layout_options = {
            "spring": "Spring Layout (force-directed)",
            "circular": "Circular Layout",
            "random": "Random Layout",
            "kamada_kawai": "Kamada-Kawai Layout",
            "shell": "Shell Layout",
            "spectral": "Spectral Layout",
        }

    def load_triplets_from_db(self) -> List[Dict[str, Any]]:
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

    def create_graph(self, triplets: List[Dict[str, Any]]) -> nx.DiGraph:
        """Create a NetworkX directed graph from triplets."""
        G = nx.DiGraph()

        for triplet in triplets:
            subject = triplet["subject_name"]
            predicate = triplet["predicate"]
            obj = triplet["object_name"]
            confidence = triplet["confidence"]

            # Add nodes
            G.add_node(subject)
            G.add_node(obj)

            # Add edge with predicate and confidence as attributes
            G.add_edge(subject, obj, predicate=predicate, confidence=confidence)

        print(
            f"Created graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges"
        )
        return G

    def get_layout_positions(self, G: nx.DiGraph, layout_type: str = "spring") -> Dict:
        """Get node positions based on selected layout algorithm."""
        if layout_type == "spring":
            return nx.spring_layout(G, k=1, iterations=50, seed=42)
        elif layout_type == "circular":
            return nx.circular_layout(G)
        elif layout_type == "random":
            return nx.random_layout(G, seed=42)
        elif layout_type == "kamada_kawai":
            return nx.kamada_kawai_layout(G)
        elif layout_type == "shell":
            return nx.shell_layout(G)
        elif layout_type == "spectral":
            return nx.spectral_layout(G)
        else:
            print(f"Unknown layout type: {layout_type}, using spring layout")
            return nx.spring_layout(G, k=1, iterations=50, seed=42)

    def create_interactive_plot(
        self,
        G: nx.DiGraph,
        layout_type: str = "spring",
        node_size: int = 20,
        edge_width: float = 1.0,
        show_edge_labels: bool = True,
    ) -> go.Figure:
        """Create an interactive plotly figure for the graph."""

        if G.number_of_nodes() == 0:
            print("No nodes to visualize!")
            return None

        # Get positions
        pos = self.get_layout_positions(G, layout_type)

        # Create edge traces
        edge_x = []
        edge_y = []
        edge_text = []

        for edge in G.edges(data=True):
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

            if show_edge_labels:
                edge_text.append(
                    f"{edge[2]['predicate']} (conf: {edge[2]['confidence']:.2f})"
                )
            else:
                edge_text.append("")

        edge_trace = go.Scatter(
            x=edge_x,
            y=edge_y,
            line=dict(width=edge_width, color="#888"),
            hoverinfo="text",
            text=edge_text,
            mode="lines",
            name="edges",
        )

        # Create node traces
        node_x = []
        node_y = []
        node_text = []
        node_color = []
        node_size_list = []

        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)

            # Calculate node properties based on degree
            degree = G.degree(node)
            node_size_list.append(node_size + degree * 2)
            node_color.append(degree)

            # Node info
            node_text.append(f"Node: {node}<br>Degree: {degree}")

        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            hoverinfo="text",
            text=[node for node in G.nodes()],
            textposition="top center",
            hovertext=node_text,
            marker=dict(
                showscale=True,
                colorscale="YlGnBu",
                size=node_size_list,
                color=node_color,
                colorbar=dict(thickness=15, title="Node Degree", xanchor="left"),
                line_width=2,
            ),
            name="nodes",
        )

        # Create figure
        fig = go.Figure(data=[edge_trace, node_trace])

        # Update layout
        fig.update_layout(
            title=dict(
                text=f"Interactive Knowledge Graph - {self.layout_options.get(layout_type, layout_type)} Layout",
                font=dict(size=16),
            ),
            showlegend=False,
            hovermode="closest",
            margin=dict(b=20, l=5, r=5, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor="white",
        )

        return fig

    def save_plot_config(self, config: Dict, filename: str = "plot_config.json"):
        """Save plot configuration to JSON file."""
        with open(filename, "w") as f:
            json.dump(config, f, indent=2)
        print(f"Configuration saved to {filename}")

    def load_plot_config(self, filename: str = "plot_config.json") -> Dict:
        """Load plot configuration from JSON file."""
        try:
            with open(filename, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return self.get_default_config()

    def get_default_config(self) -> Dict:
        """Get default configuration for the plot."""
        return {
            "layout_type": "spring",
            "node_size": 20,
            "edge_width": 1.0,
            "show_edge_labels": True,
            "output_filename": "interactive_knowledge_graph.html",
        }

    def visualize_interactive(self, config: Optional[Dict] = None):
        """Main interactive visualization function."""
        if config is None:
            config = self.get_default_config()

        print("Loading triplets from database...")
        triplets = self.load_triplets_from_db()

        if not triplets:
            print("No triplets found in database!")
            return

        print("Creating graph...")
        G = self.create_graph(triplets)

        print(f"Creating interactive plot with {config['layout_type']} layout...")
        fig = self.create_interactive_plot(
            G,
            layout_type=config["layout_type"],
            node_size=config["node_size"],
            edge_width=config["edge_width"],
            show_edge_labels=config["show_edge_labels"],
        )

        if fig is None:
            return

        # Save as HTML file
        output_file = config["output_filename"]
        fig.write_html(output_file)
        print(f"Interactive graph saved to: {output_file}")
        print("Open this file in your web browser to interact with the graph!")

        # Also show available layout options
        print("\nAvailable layout options:")
        for key, desc in self.layout_options.items():
            print(f"  {key}: {desc}")

        return fig


def main():
    """Main function with configuration options."""
    visualizer = InteractiveGraphVisualizer()

    # Try to load existing config, otherwise use defaults
    config = visualizer.load_plot_config("db/plot_config.json")

    # You can modify these values to customize the plot
    # config['layout_type'] = 'circular'  # Try: 'spring', 'circular', 'random', 'kamada_kawai', 'shell', 'spectral'
    # config['node_size'] = 25
    # config['edge_width'] = 1.5
    # config['show_edge_labels'] = False
    # config['output_filename'] = 'my_custom_graph.html'

    visualizer.visualize_interactive(config)

    # Save the config for future use
    visualizer.save_plot_config(config, "db/plot_config.json")


if __name__ == "__main__":
    main()
