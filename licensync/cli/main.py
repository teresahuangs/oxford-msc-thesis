
import os, pathlib, typer
from licensync.core.dependency_parser import load_dependencies, flatten_sbom
from licensync.core.github_api import fetch_github_sbom, fetch_repo_license_spdx
from licensync.core.license_utils import normalize_license
from licensync.core.graph_tools import build_graph_recursive, show_graph
from licensync.core.prolog_interface import evaluate_license_pair, obligations_for_license
from licensync.core.llm_explainer import generate_explanation

app = typer.Typer(help="LicenSync CLI")

def _extract_license_set(flat_deps: list[tuple[str,str]]):
    return sorted({normalize_license(lic) for _, lic in flat_deps})

@app.command()
def main(
    repo1: str,
    repo2: str,
    jurisdiction: str = typer.Option("global", "--jurisdiction", "-j"),
    gh_token: str = typer.Option(os.getenv("GITHUB_TOKEN"), "--gh-token"),
    save_figs: bool = typer.Option(True, help="Save dependency graphs")
):
    deps1 = load_dependencies(pathlib.Path("."), repo1, gh_token)
    deps2 = load_dependencies(pathlib.Path("."), repo2, gh_token)

    LA = _extract_license_set(deps1)
    LB = _extract_license_set(deps2)

    root1 = normalize_license(fetch_repo_license_spdx(repo1, gh_token) or "unknown")
    root2 = normalize_license(fetch_repo_license_spdx(repo2, gh_token) or "unknown")
    typer.echo(f"{repo1}: {root1}  – deps: {len(LA)}")
    typer.echo(f"{repo2}: {root2}  – deps: {len(LB)}")
    typer.echo(f"Jurisdiction: {jurisdiction}")

    incompatible = []
    for la in LA:
        for lb in LB:
            res = evaluate_license_pair(la, lb, jurisdiction)
            if res != "ok":
                ob1 = obligations_for_license(la, jurisdiction)
                ob2 = obligations_for_license(lb, jurisdiction)
                expl = generate_explanation(la, lb, jurisdiction, res, ob1, ob2)
                incompatible.append({"la": la, "lb": lb, "result": res, "explanation": expl})

    overall = "ok" if not incompatible else "incompatible"
    typer.echo(f"→ Overall verdict: {overall}")
    for item in incompatible[:5]:
        typer.echo(f"- {item['la']} × {item['lb']} → {item['result']}\n  {item['explanation']}")

    if save_figs:
        figdir = pathlib.Path("figs"); figdir.mkdir(exist_ok=True)
        edges1, edges2 = [], []
        try:
            sbom1 = fetch_github_sbom(repo1, gh_token); edges1 = flatten_sbom(repo1, sbom1)
        except Exception:
            pass
        try:
            sbom2 = fetch_github_sbom(repo2, gh_token); edges2 = flatten_sbom(repo2, sbom2)
        except Exception:
            pass
        if not edges1:
            edges1 = [dict(name=n, license=lic, parent=repo1) for (n, lic) in deps1]
        if not edges2:
            edges2 = [dict(name=n, license=lic, parent=repo2) for (n, lic) in deps2]
        G1 = build_graph_recursive(repo1, root1, edges1)
        G2 = build_graph_recursive(repo2, root2, edges2)
        show_graph(G1, f"{repo1} dependency licences", outfile=str(figdir / f"{repo1.replace('/','_')}_graph.png"))
        show_graph(G2, f"{repo2} dependency licences", outfile=str(figdir / f"{repo2.replace('/','_')}_graph.png"))

if __name__ == "__main__":
    app()
