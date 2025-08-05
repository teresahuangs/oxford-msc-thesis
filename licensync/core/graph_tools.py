import networkx as nx, matplotlib.pyplot as plt

# ──────────────────────────────────────────────────────────────
# 3.  (optional) recursive builder for SBOM JSON
#     deps  ≙  List[Dict{name, spdx, parent?}]
# ──────────────────────────────────────────────────────────────
def build_graph_recursive(root_name: str,
                          root_license: str,
                          deps_json) -> nx.DiGraph:
    """
    Accepts the raw list returned by GitHub SBOM:
        [{'name': 'react', 'spdx': 'mit', 'parent': None},
         {'name': 'object-assign', 'spdx': 'mit',
                                        'parent': 'react'}, ...]
    """
    G = nx.DiGraph()
    G.add_node(root_name, license=root_license, kind="root")

    for row in deps_json:
        pkg  = row["name"]
        spdx = row.get("spdx", "unknown").lower()

        G.add_node(pkg, license=spdx, kind="package")

        parent = row.get("parent") or root_name
        G.add_edge(parent, pkg, scope="runtime")

    return G


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
