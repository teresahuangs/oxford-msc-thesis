import typer
from core.prolog_interface import evaluate_license_pair

app = typer.Typer()

@app.command()
def check(l1: str, l2: str, jurisdiction: str):
    result = evaluate_license_pair(l1.lower(), l2.lower(), jurisdiction.lower())
    print(f"Evaluation: {result}")

if __name__ == "__main__":
    app()
