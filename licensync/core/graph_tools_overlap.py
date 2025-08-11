from __future__ import annotations
import networkx as nx
from typing import Dict, Iterable, List, Tuple, Callable, Optional

def build_overlap_graph(
    roots: List[Tuple[str, str]],
    edges: Iterable[Dict],
) -> nx.DiGraph:
    """
    Build a single dependency graph that contains *all* nodes from multiple
    repositories. Roots are always present even if they have 0 deps. Nodes that
    appear in multiple repos are de-duplicated.

    Node attrs:
      - license: SPDX id or "unknown"
      - present_in: set of root names that can reach this node (incl. itself for roots)
      - is_root: bool

    Edge attrs:
      - source_roots: set of root names for which this edge lies on a path
    """
    G = nx.DiGraph()

    # Add roots first
    root_names = [r for r, _ in roots]
    for r_name, r_lic in roots:
        G.add_node(r_name, license=r_lic or "unknown", present_in={r_name}, is_root=True)

    # Add edges and child nodes
    for e in edges:
        parent = e.get("parent")
        child = e.get("name")
        lic = e.get("license", "unknown") or "unknown"
        if not parent or not child:
            continue

        if not G.has_node(parent):
            G.add_node(parent, license="unknown", present_in=set(), is_root=False)

        if not G.has_node(child):
            G.add_node(child, license=lic, present_in=set(), is_root=False)
        else:
            if (G.nodes[child].get("license") in (None, "", "unknown")) and lic not in (None, "", "unknown"):
                G.nodes[child]["license"] = lic

        if not G.has_edge(parent, child):
            G.add_edge(parent, child)

    # Reachability from each root → fill present_in + tag edge source_roots
    for r_name, _ in roots:
        if not G.has_node(r_name):
            continue
        for n in (nx.descendants(G, r_name) | {r_name}):
            G.nodes[n].setdefault("present_in", set()).add(r_name)
        for u, v in nx.bfs_edges(G, r_name):
            G.edges[u, v].setdefault("source_roots", set()).add(r_name)

    return G


def draw_overlap_graph(
    G: nx.DiGraph,
    title: str = "Dependency overlap",
    outfile: Optional[str] = None,
) -> None:
    import matplotlib.pyplot as plt
    pos = nx.spring_layout(G, seed=42, k=0.8 / (1 + max(1, G.number_of_nodes())), iterations=300)

    roots = [n for n, d in G.nodes(data=True) if d.get("is_root")]
    all_roots = set(roots)

    node_colors, node_sizes, labels = [], [], {}
    for n, d in G.nodes(data=True):
        lic = d.get("license", "") or ""
        labels[n] = f"{n}\n({lic})" if lic else n
        present_in = set(d.get("present_in", set()))
        if d.get("is_root"):
            node_sizes.append(1200); node_colors.append(0.75)  # gray-ish roots
        else:
            node_sizes.append(500)
            if len(all_roots) <= 2:
                node_colors.append(0.25 if len(present_in) >= 2 else (0.9 if roots and next(iter(present_in), None) == roots[0] else 0.6))
            else:
                node_colors.append(0.6 if len(present_in) == 1 else 0.25)

    import matplotlib.pyplot as plt
    plt.figure(figsize=(12, 8))
    nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color=node_colors)
    nx.draw_networkx_edges(G, pos, arrows=True, width=0.8, alpha=0.6)
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=8)
    plt.title(title); plt.axis("off"); plt.tight_layout()

    if outfile:
        import os
        os.makedirs(os.path.dirname(outfile), exist_ok=True)
        plt.savefig(outfile, dpi=250); plt.close()
    else:
        plt.show()


def mark_incompatibilities(
    G: nx.DiGraph,
    evaluator: Callable[[str, str], bool],
    set_edge_attr: str = "is_compatible",
) -> None:
    """Optional: tag each edge with a boolean compatibility using your evaluator."""
    for u, v in G.edges():
        lic_u = G.nodes[u].get("license", "unknown")
        lic_v = G.nodes[v].get("license", "unknown")
        ok = True
        try:
            ok = bool(evaluator(lic_u, lic_v))
        except Exception:
            ok = True
        G.edges[u, v][set_edge_attr] = ok
