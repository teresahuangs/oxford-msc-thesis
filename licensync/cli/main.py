import os
import pathlib
import typer
from rich.console import Console

# Import all necessary functions from your core modules
from licensync.core.dependency_parser import load_dependencies, flatten_sbom
from licensync.core.github_api import fetch_github_sbom, fetch_repo_license_spdx
from licensync.core.license_utils import normalize_license
from licensync.core.graph_tools import build_graph_recursive, show_graph
from licensync.core.graph_tools_overlap import build_overlap_graph, draw_overlap_graph # <-- New import
from licensync.core.prolog_interface import evaluate_license_pair, verdict_and_obligs, obligations_for_license
from licensync.core.llm_explainer import generate_explanation

# --- Create a SINGLE Typer App ---
app = typer.Typer(help="LicenSync CLI: Analyze and explain software license compatibility.")
console = Console()

def _extract_license_set(flat_deps: list[tuple[str,str]]):
    """Helper function to get unique licenses from a dependency list."""
    return sorted({normalize_license(lic) for _, lic in flat_deps})

# --- First Command: compare ---
@app.command(name="compare", help="Compare dependency trees of two GitHub repos and generate graphs.")
def compare_repos(
    repo1: str = typer.Argument(..., help="First repository (e.g., 'owner/repo')."),
    repo2: str = typer.Argument(..., help="Second repository (e.g., 'owner/repo')."),
    jurisdiction: str = typer.Option("global", "--jurisdiction", "-j", help="The legal jurisdiction for evaluation."),
    gh_token: str = typer.Option(os.getenv("GITHUB_TOKEN"), "--gh-token", help="GitHub API token."),
    save_figs: bool = typer.Option(True, help="Save dependency graphs as images."),
):
    """
    Compares the full dependency trees of two repositories and generates graphs.
    """
    # (This is your full compare logic with graph-making)
    console.print(f"Comparing repositories [bold cyan]{repo1}[/] and [bold cyan]{repo2}[/]...", style="blue")
    
    deps1 = load_dependencies(pathlib.Path("."), repo1, gh_token)
    deps2 = load_dependencies(pathlib.Path("."), repo2, gh_token)
    LA = _extract_license_set(deps1)
    LB = _extract_license_set(deps2)
    root1 = normalize_license(fetch_repo_license_spdx(repo1, gh_token) or "unknown")
    root2 = normalize_license(fetch_repo_license_spdx(repo2, gh_token) or "unknown")
    console.print(f"{repo1}: [bold yellow]{root1}[/] – Found {len(LA)} unique dependency licenses.")
    console.print(f"{repo2}: [bold yellow]{root2}[/] – Found {len(LB)} unique dependency licenses.")

    if save_figs:
        # ... (your existing graph generation logic)
        console.print("\\nGenerating dependency graphs...", style="blue")
        # ... etc.

# --- Second Command: explain ---
@app.command(name="explain", help="Explain the compatibility between any two licenses.")
def explain_license_pair(
    lic1: str = typer.Argument(..., help="The first license's SPDX identifier (e.g., 'MIT')."),
    lic2: str = typer.Argument(..., help="The second license's SPDX identifier (e.g., 'GPL-3.0-only')."),
    jurisdiction: str = typer.Argument(..., help="The legal jurisdiction (e.g., 'global', 'us', 'eu').")
):
    """Provides a detailed explanation for the compatibility of two licenses."""
    # (This is your full explain logic)
    response = evaluate_license_pair(lic1, lic2, jurisdiction)
    # ... etc.

# --- Third Command: overlap ---
# In licensync/cli/main.py

# --- (your other imports and commands remain the same) ---

@app.command(name="overlap", help="Create a single graph showing the dependency overlap between two repos.")
def overlap_graphs(
    repo1: str = typer.Argument(..., help="First repository (e.g., 'owner/repo')."),
    repo2: str = typer.Argument(..., help="Second repository (e.g., 'owner/repo')."),
    gh_token: str = typer.Option(os.getenv("GITHUB_TOKEN"), "--gh-token", help="GitHub API token."),
):
    """
    Builds and saves a single graph visualizing shared and unique dependencies.
    """
    console.print(f"Generating overlap graph for [bold cyan]{repo1}[/] and [bold cyan]{repo2}[/]...", style="blue")
    
    # 1. Get root licenses
    root1_lic = normalize_license(fetch_repo_license_spdx(repo1, gh_token) or "unknown")
    root2_lic = normalize_license(fetch_repo_license_spdx(repo2, gh_token) or "unknown")
    roots = [(repo1, root1_lic), (repo2, root2_lic)]

    # 2. Get dependency lists using the resilient load_dependencies function
    deps1 = load_dependencies(pathlib.Path("."), repo1, gh_token)
    deps2 = load_dependencies(pathlib.Path("."), repo2, gh_token)

    if not deps1 and not deps2:
        console.print("Error: Could not retrieve dependency data for either repository.", style="bold red")
        raise typer.Exit()
        
    # 3. Convert the dependency lists into the "edge" format needed for the graph
    all_edges = []
    for name, license in deps1:
        all_edges.append({"name": name, "license": license, "parent": repo1})
    for name, license in deps2:
        all_edges.append({"name": name, "license": license, "parent": repo2})

    # 4. Build and draw the graph
    G = build_overlap_graph(roots, all_edges)
    figdir = pathlib.Path("figs"); figdir.mkdir(exist_ok=True)
    out_path = str(figdir / f"overlap_{repo1.replace('/','_')}_vs_{repo2.replace('/','_')}.png")
    
    draw_overlap_graph(G, title=f"Dependency Overlap: {repo1} vs {repo2}", outfile=out_path)
    console.print(f"✅ Overlap graph saved to '{out_path}'")

# --- Main execution block ---
if __name__ == "__main__":
    app()