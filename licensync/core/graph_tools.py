# In licensync/core/graph_tools.py

import matplotlib
matplotlib.use('Agg') # Set the backend BEFORE importing pyplot
import matplotlib.pyplot as plt
import networkx as nx
import os

def build_graph_recursive(root: str, root_license: str, edges: list[dict]) -> nx.DiGraph:
    # (This function remains the same)
    G = nx.DiGraph()
    G.add_node(root, license=root_license or "unknown")
    for e in edges:
        name = e.get("name")
        lic = e.get("license", "unknown")
        parent = e.get("parent", root)
        if not G.has_node(name):
            G.add_node(name, license=lic)
        if not G.has_node(parent):
            G.add_node(parent, license="unknown")
        G.add_edge(parent, name)
    for n in list(G.nodes):
        if n != root and G.in_degree(n) == 0:
            G.add_edge(root, n)
    return G

def show_graph(G: nx.DiGraph, title: str, outfile: str | None = None):
    """
    Builds and saves a dependency graph, now optimized for large graphs.
    """
    try:
        print(f"  -> Attempting to generate graph for '{title}' with {G.number_of_nodes()} nodes...")
        plt.figure(figsize=(16, 16)) # Use a larger figure for larger graphs
        
        # --- OPTIMIZATION ---
        # Reduce layout iterations for large graphs to save memory and time.
        iterations = 50
        if G.number_of_nodes() > 100:
            print("     -> Large graph detected, using fewer layout iterations.")
            iterations = 25
            
        print("     -> Calculating graph layout (this can be slow for large graphs)...")
        pos = nx.spring_layout(G, seed=42, iterations=iterations)
        print("     -> Layout calculation complete.")
        
        # Adjust node and font size for readability on large graphs
        node_size = 1200 if G.number_of_nodes() < 100 else 800
        font_size = 8 if G.number_of_nodes() < 100 else 6

        print("     -> Drawing nodes, edges, and labels...")
        nx.draw_networkx_nodes(G, pos, node_color="#cfe8ff", node_size=node_size)
        nx.draw_networkx_edges(G, pos, edge_color="#999", alpha=0.6)
        nx.draw_networkx_labels(G, pos, font_size=font_size)

        plt.title(title, fontsize=20)
        plt.axis("off")
        plt.tight_layout()

        if outfile:
            print(f"     -> Saving image to {outfile}...")
            os.makedirs(os.path.dirname(outfile), exist_ok=True)
            plt.savefig(outfile, dpi=300, bbox_inches="tight")
            print(f"  -> ✅ Graph successfully saved.")
        else:
            plt.show()
        
        plt.close()

    except Exception as e:
        print(f"\\n❌ ERROR: Failed to generate or save the graph.")
        print(f"   Error details: {e}")