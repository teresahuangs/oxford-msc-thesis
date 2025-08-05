import typer, pathlib, json, os
from licensync.core.dependency_parser import load_dependencies
from licensync.core.prolog_interface import obligations_for_license
from licensync.core.llm_explainer import generate_explanation

app = typer.Typer()

@app.command()
def repo(repo: str, jurisdiction: str = "global",
         local: pathlib.Path = typer.Option(None),
         gh_token: str = typer.Option(os.getenv("GITHUB_TOKEN"))):
    """End-to-end smoke test on one repo."""
    deps = load_dependencies(local or pathlib.Path("."), repo, gh_token)
    unique = {lic for _, lic in deps}
    report = {}
    for lic in unique:
        obligations = obligations_for_license(lic, jurisdiction)
        explanation = generate_explanation(lic, jurisdiction, obligations)
        report[lic] = dict(obligations=obligations, explanation=explanation)

    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    app()
