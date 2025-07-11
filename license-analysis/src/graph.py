import networkx as nx

def build_dependency_graph(project):
    G = nx.DiGraph()
    for comp in project['components']:
        G.add_node(comp['id'], type=comp['type'], license=comp['license'], activity=comp['activity'])
    for comp in project['components']:
        if comp['activity'] in ['fine-tune', 'train']:
            G.add_edge(comp['id'], 'output_model', label=comp['activity'])
    return G
