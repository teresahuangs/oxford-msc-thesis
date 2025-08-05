import typer, pathlib, os
from ..core.github_api import fetch_spdx_license
from ..core.dependency_parser import load_dependencies
from ..core.graph_tools import build_graph, show_graph
from ..core.prolog_interface import (
    evaluate_license_pair,
    obligations_for_license      # ← new helper you expose
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
    verdict = evaluate_license_pair(license1.lower(), license2.lower(), jurisdiction.lower())
    typer.echo(f"Compatibility verdict: {verdict}")
    explanation = generate_explanation(license1, license2, jurisdiction, verdict)
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

# ── run Typer CLI ─────────────────────────────────────────────────
if __name__ == "__main__":
    app()
