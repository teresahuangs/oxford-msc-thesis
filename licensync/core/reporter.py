
from typing import List, Dict, Any

def generate_report(results: List[Dict[str, Any]]):
    for item in results:
        la = item.get("la"); lb = item.get("lb")
        res = item.get("result")
        expl = item.get("explanation","")
        print(f"{la} × {lb} → {res}")
        if expl:
            print("  ", expl)
