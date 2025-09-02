import os
import pathlib
import typer
from rich.console import Console

# Import all necessary functions from your core modules
from licensync.core.dependency_parser import load_dependencies, flatten_sbom
from licensync.core.github_api import fetch_github_sbom, fetch_repo_license_spdx
from licensync.core.license_utils import normalize_license
from licensync.core.graph_tools import build_graph_recursive, show_graph
from licensync.core.graph_tools_overlap import build_overlap_graph, draw_overlap_graph
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
        console.print("\\nGenerating dependency graphs...", style="blue")
        figdir = pathlib.Path("figs"); figdir.mkdir(exist_ok=True)
        edges1 = [dict(name=n, license=lic, parent=repo1) for (n, lic) in deps1]
        edges2 = [dict(name=n, license=lic, parent=repo2) for (n, lic) in deps2]
        G1 = build_graph_recursive(repo1, root1, edges1)
        G2 = build_graph_recursive(repo2, root2, edges2)
        path1 = str(figdir / f"{repo1.replace('/','_')}_graph.png")
        path2 = str(figdir / f"{repo2.replace('/','_')}_graph.png")
        show_graph(G1, f"{repo1} Dependency Licenses", outfile=path1)
        show_graph(G2, f"{repo2} Dependency Licenses", outfile=path2)
        console.print(f"✅ Graphs saved to '{path1}' and '{path2}'")

# --- Second Command: explain ---
@app.command(name="explain", help="Explain the compatibility between any two licenses.")
def explain_license_pair(
    lic1: str = typer.Argument(..., help="The first license's SPDX identifier (e.g., 'MIT')."),
    lic2: str = typer.Argument(..., help="The second license's SPDX identifier (e.g., 'GPL-3.0-only')."),
    jurisdiction: str = typer.Argument(..., help="The legal jurisdiction (e.g., 'global', 'us', 'eu').")
):
    """Provides a detailed explanation for the compatibility of two licenses."""
    console.print(f"Analyzing: [bold cyan]{lic1}[/] vs. [bold cyan]{lic2}[/] in jurisdiction [bold green]{jurisdiction}[/]", justify="center")
    
    
    verdict, obligs1, obligs2 = verdict_and_obligs(lic1, lic2, jurisdiction)
    
    response = evaluate_license_pair(lic1, lic2, jurisdiction)
    risk = response.get("risk", "undefined")
 

    verdict_style = "bold green" if verdict == "ok" else "bold red"
    console.print(f"\\nVerdict: [{verdict_style}]{verdict.upper()}[/] | Assessed Risk: [yellow]{risk.capitalize()}[/]")

    console.print(f"\\nObligations for [bold cyan]{lic1.upper()}[/]:")
    if obligs1:
        for ob in obligs1: console.print(f"  • {ob.replace('_', ' ').capitalize()}")
    else:
        console.print("  • (none)")

    console.print(f"\\nObligations for [bold cyan]{lic2.upper()}[/]:")
    if obligs2:
        for ob in obligs2: console.print(f"  • {ob.replace('_', ' ').capitalize()}")
    else:
        console.print("  • (none)")

    # Now, pass the correct obligations to the explainer
    console.print("\\n[bold]Expert Explanation:[/bold]")
    explanation = generate_explanation(lic1, lic2, jurisdiction, verdict, obligs1, obligs2)
    console.print(f"[bright_black]{explanation}[/]")


# --- Third Command: overlap ---
@app.command(name="overlap", help="Create a single graph showing the dependency overlap between two repos.")
def overlap_graphs(
    repo1: str = typer.Argument(..., help="First repository (e.g., 'owner/repo')."),
    repo2: str = typer.Argument(..., help="Second repository (e.g., 'owner/repo')."),
    gh_token: str = typer.Option(os.getenv("GITHUB_TOKEN"), "--gh-token", help="GitHub API token."),
):
    console.print(f"Generating overlap graph for [bold cyan]{repo1}[/] and [bold cyan]{repo2}[/]...", style="blue")
    root1_lic = normalize_license(fetch_repo_license_spdx(repo1, gh_token) or "unknown")
    root2_lic = normalize_license(fetch_repo_license_spdx(repo2, gh_token) or "unknown")
    roots = [(repo1, root1_lic), (repo2, root2_lic)]
    deps1 = load_dependencies(pathlib.Path("."), repo1, gh_token)
    deps2 = load_dependencies(pathlib.Path("."), repo2, gh_token)
    
    all_edges = []
    all_edges.extend([{"name": name, "license": license, "parent": repo1} for name, license in deps1])
    all_edges.extend([{"name": name, "license": license, "parent": repo2} for name, license in deps2])
    
    G = build_overlap_graph(roots, all_edges)
    figdir = pathlib.Path("figs"); figdir.mkdir(exist_ok=True)
    out_path = str(figdir / f"overlap_{repo1.replace('/','_')}_vs_{repo2.replace('/','_')}.png")
    draw_overlap_graph(G, title=f"Dependency Overlap: {repo1} vs {repo2}", outfile=out_path)
    console.print(f"✅ Overlap graph saved to '{out_path}'")

# --- Main execution block ---
if __name__ == "__main__":
    app()