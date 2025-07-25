import networkx as nx, matplotlib.pyplot as plt

def build_graph(root_name: str, root_license: str,
                deps: list[tuple[str,str]]) -> nx.DiGraph:
    g = nx.DiGraph()
    g.add_node(root_name, license=root_license)
    for dep, lic in deps:
        g.add_node(dep, license=lic)
        g.add_edge(root_name, dep)
    return g

def show_graph(G: nx.DiGraph, title: str):
    pos = nx.spring_layout(G, seed=42)
    labels = {n: f"{n}\n{G.nodes[n]['license']}" for n in G.nodes}
    nx.draw(G, pos, node_size=2500, node_color="#cce5ff",
            edge_color="#888", with_labels=True, labels=labels,
            font_size=8, font_family="monospace")
    plt.title(title)
    plt.tight_layout(); plt.show()
