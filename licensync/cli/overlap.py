import pathlib, typer
from typing import Optional, List, Tuple, Dict

from licensync.core.dependency_parser import load_dependencies, flatten_sbom
from licensync.core.github_api import fetch_github_sbom, fetch_repo_license_spdx
from licensync.core.license_utils import normalize_license
from licensync.core.graph_tools_overlap import build_overlap_graph, draw_overlap_graph

app = typer.Typer(help="Draw a single, merged dependency graph for two repos.")

@app.command()
def main(
    repo1: str,
    repo2: str,
    j: str = typer.Option("global", "--jurisdiction", "-j"),
    gh_token: Optional[str] = typer.Option(None, "--gh-token"),
    out: Optional[pathlib.Path] = typer.Option(None, "--out"),
):
    """
    Build one combined dependency graph that includes *all* nodes from both repos,
    even if a repo has zero dependencies.
    """
    figdir = (out.parent if out else pathlib.Path("figs"))
    figdir.mkdir(parents=True, exist_ok=True)

    def _edges_for(repo: str) -> Tuple[str, List[Dict]]:
        edges: List[Dict] = []
        lic = "unknown"
        # Try SBOM first
        try:
            sbom = fetch_github_sbom(repo, gh_token)
            edges = flatten_sbom(repo, sbom)
        except Exception:
            pass
        # Fallback to requirement/pyproject parsing
        if not edges:

            deps = load_dependencies(pathlib.Path("."), gh_repo=repo, gh_token=gh_token)
            edges = [dict(parent=repo, name=n, license=normalize_license(lic)) for (n, lic) in deps]
        # Repo license for root node
        try:
            lic = normalize_license(fetch_repo_license_spdx(repo, gh_token))
        except Exception:
            lic = "unknown"
        return lic, edges

    root1_lic, edges1 = _edges_for(repo1)
    root2_lic, edges2 = _edges_for(repo2)

    roots = [(repo1, root1_lic), (repo2, root2_lic)]
    G = build_overlap_graph(roots, [*edges1, *edges2])

    title = f"{repo1} ∪ {repo2} dependencies"
    outfile = str(out or (figdir / f"{repo1.replace('/','_')}__{repo2.replace('/','_')}_overlap.png"))
    draw_overlap_graph(G, title=title, outfile=outfile)

if __name__ == "__main__":
    app()
