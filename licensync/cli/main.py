import typer, pathlib, os
from ..core.github_api import fetch_spdx_license
from ..core.dependency_parser import load_dependencies
from ..core.graph_tools import build_graph, show_graph
from ..core.prolog_interface import (
    evaluate_license_pair,
    obligations_for_license,
    verdict_and_obligs      # ← new helper you expose
)
from ..core.llm_explainer import generate_explanation

app = typer.Typer()

# ── 1. repo-to-repo comparison ─────────────────────────────────────
@app.command("compare-repos")
def compare_repos(
    repo1: str,
    repo2: str,
    jurisdiction: str,
    local_path1: pathlib.Path = typer.Option(None, help="Local checkout of repo1"),
    local_path2: pathlib.Path = typer.Option(None, help="Local checkout of repo2"),
    gh_token: str = typer.Option(os.getenv("GITHUB_TOKEN"), help="GitHub PAT")
):
    lic1 = fetch_spdx_license(repo1, gh_token) or "unknown"
    lic2 = fetch_spdx_license(repo2, gh_token) or "unknown"
    deps1 = load_dependencies(local_path1 or pathlib.Path("."), repo1, gh_token)
    deps2 = load_dependencies(local_path2 or pathlib.Path("."), repo2, gh_token)

    verdict = evaluate_license_pair(lic1.lower(), lic2.lower(), jurisdiction.lower())
    typer.echo(f"{repo1}: {lic1}  – deps: {len(deps1)}")
    typer.echo(f"{repo2}: {lic2}  – deps: {len(deps2)}")
    typer.echo(f"Jurisdiction: {jurisdiction}")
    typer.echo(f"→ Root-licence verdict: {verdict}")

    show_graph(build_graph(repo1, lic1, deps1), f"{repo1} dependency licences")
    show_graph(build_graph(repo2, lic2, deps2), f"{repo2} dependency licences")

# ── 2. simple pair check (kept) ────────────────────────────────────
@app.command("check")
def check(l1: str, l2: str, jurisdiction: str):
    result = evaluate_license_pair(l1.lower(), l2.lower(), jurisdiction.lower())
    typer.echo(f"Evaluation: {result}")

# ── 3. explanation with LLM (kept) ─────────────────────────────────
@app.command("explain")
def explain(license1: str, license2: str, jurisdiction: str):
    # ▲  get verdict + obligations from Prolog
    verdict, obls1, obls2 = verdict_and_obligs(
        license1.lower(), license2.lower(), jurisdiction.lower()
    )

    typer.echo(f"Compatibility verdict: {verdict}")

    # ▼  ALWAYS print the obligations so the user sees something
    typer.echo("\nObligations:")
    typer.echo(f"  {license1.upper()}: {', '.join(obls1) or '(none)'}")
    typer.echo(f"  {license2.upper()}: {', '.join(obls2) or '(none)'}")

    # ▼  call the LLM explainer (returns placeholder if quota exhausted)
    explanation = generate_explanation(
        license1, license2, jurisdiction, verdict, obls1, obls2
    )

    typer.echo("\nExplanation:")
    typer.echo(explanation)


# ── 4. NEW: obligations for a single licence in a jurisdiction ────
@app.command("license-info")
def license_info(
    license_id: str,
    jurisdiction: str = typer.Option("global", help="global | us | eu | …")
):
    """
    Show the obligations that apply to one SPDX licence under a given jurisdiction.
    """
    obls = obligations_for_license(license_id.lower(), jurisdiction.lower())
    typer.echo(f"Obligations for {license_id} under {jurisdiction}:")
    for o in obls:
        typer.echo(f"  • {o}")

@app.command("show-graph")
def show_graph_cmd(repo: str,
                   jurisdiction: str = typer.Option("global",
                                help="ignored – kept for symmetry"),
                   gh_token: str = typer.Option(
                       os.getenv("GITHUB_TOKEN"),
                       help="GitHub personal-access token")):
    """
    Pull SBOM from GitHub and draw dependency-licence graph.
    """
    from ..core.dependency_parser import dependency_graph_api
    from ..core.graph_tools        import build_graph_recursive, show_graph

    sbom = dependency_graph_api(repo, gh_token)
    root_lic = fetch_spdx_license(repo, gh_token) or "unknown"

    G = build_graph_recursive(repo, root_lic, [
            {"name": p, "spdx": l, "parent": root} for root, (p, l) in
            [(repo, pair) for pair in sbom]    # flatten
        ])

    show_graph(G, f"{repo} dependency licences")

@app.command("show-graph")
def show_graph_cmd(
    repo: str,
    local_path1: pathlib.Path = typer.Option(None, help="optional local checkout"),
    gh_token: str = typer.Option(os.getenv("GITHUB_TOKEN")),
):
    """
    Build dependency graph for REPO and save figure into ./figs/.
    """
    from ..core.github_api       import fetch_spdx_license
    from ..core.dependency_parser import load_dependencies
    from ..core.graph_tools       import build_graph, show_graph

    root_lic = fetch_spdx_license(repo, gh_token) or "unknown"
    deps     = load_dependencies(local_path1 or pathlib.Path("."), repo, gh_token)

    G = build_graph(repo, root_lic, deps)
    outfile = pathlib.Path("figs") / f"{repo.replace('/', '_')}_deps.png"
    show_graph(G, repo, outfile=str(outfile))
    typer.echo(f"Graph written to {outfile}")



# ── run Typer CLI ─────────────────────────────────────────────────
if __name__ == "__main__":
    app()
