
import networkx as nx, matplotlib.pyplot as plt, os

def build_graph_recursive(root: str, root_license: str, edges: list[dict]) -> nx.DiGraph:
    G = nx.DiGraph()
    G.add_node(root, license=root_license or "unknown")
    
    # Create a set of all nodes that are parents in the edges list
    parents_in_edges = {e.get("parent") for e in edges}

    for e in edges:
        name = e.get("name")
        lic = e.get("license", "unknown")
        parent = e.get("parent", root)
        
        if not G.has_node(name):
            G.add_node(name, license=lic)
        if not G.has_node(parent):
            # If a parent node from the edges is not in the graph, add it
            # and connect it to the root if it's not connected to anything else.
            G.add_node(parent, license="unknown")
            if parent not in parents_in_edges and nx.is_isolate(G, parent):
                 G.add_edge(root, parent)

        G.add_edge(parent, name)

    # Connect any nodes that are not the root and have no incoming connections to the root
    for n in list(G.nodes):
        if n != root and G.in_degree(n) == 0:
            G.add_edge(root, n)
            
    return G

def show_graph(G: nx.DiGraph, title: str, outfile: str | None = None):
    plt.figure(figsize=(9, 7))
    pos = nx.spring_layout(G, seed=42, k=0.9)
    nx.draw_networkx_nodes(G, pos, node_color="#cfe8ff", node_size=2200, linewidths=0.8, edgecolors="#5b83b1")
    nx.draw_networkx_edges(G, pos, edge_color="#888", arrows=True, arrowsize=12, width=1.0)

    # main labels (names)
    name_labels = {n: n for n in G.nodes}
    nx.draw_networkx_labels(G, pos, labels=name_labels, font_size=8, font_weight="bold")

    # license labels slightly below each node
    lic_labels = {n: G.nodes[n].get("license","") for n in G.nodes}
    lic_pos = {n: (xy[0], xy[1]-0.06) for n, xy in pos.items()}
    nx.draw_networkx_labels(G, lic_pos, labels=lic_labels, font_size=7)

    plt.title(title)
    plt.axis("off")
    try:
        plt.tight_layout()
    except Exception:
        pass
    if outfile:
        os.makedirs(os.path.dirname(outfile), exist_ok=True)
        plt.savefig(outfile, dpi=300)
    else:
        plt.show()
