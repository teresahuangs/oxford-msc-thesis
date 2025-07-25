import typer, pathlib, os
from ..core.github_api import fetch_spdx_license
from ..core.dependency_parser import load_dependencies
from ..core.graph_tools import build_graph, show_graph
from ..core.prolog_interface import evaluate_license_pair

app = typer.Typer()

@app.command("compare-repos")
def compare_repos(repo1: str, repo2: str,
                  jurisdiction: str,
                  local_path1: pathlib.Path = typer.Option(
                      None, help="Optional local checkout of repo1"),
                  local_path2: pathlib.Path = typer.Option(
                      None, help="Optional local checkout of repo2"),
                  gh_token: str = typer.Option(
                      os.getenv("GITHUB_TOKEN"), help="GitHub PAT")):
    """
    Pull SPDX licences & dependencies for two repos, build graphs, compare root licences.
    """
    lic1 = fetch_spdx_license(repo1) or "unknown"
    lic2 = fetch_spdx_license(repo2) or "unknown"

    deps1 = load_dependencies(local_path1 or pathlib.Path("."), repo1, gh_token)
    deps2 = load_dependencies(local_path2 or pathlib.Path("."), repo2, gh_token)

    G1 = build_graph(repo1, lic1, deps1)
    G2 = build_graph(repo2, lic2, deps2)

    typer.echo(f"{repo1}: {lic1}  – deps: {len(deps1)}")
    typer.echo(f"{repo2}: {lic2}  – deps: {len(deps2)}")
    typer.echo(f"Jurisdiction: {jurisdiction}")

    root_result = evaluate_license_pair(lic1.lower(), lic2.lower(),
                                        jurisdiction.lower())
    typer.echo(f"→ Root‑license verdict: {root_result}")

    # Visualise graphs
    show_graph(G1, f"{repo1} dependency licences")
    show_graph(G2, f"{repo2} dependency licences")


