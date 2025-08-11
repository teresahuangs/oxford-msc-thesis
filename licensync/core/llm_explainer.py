
import os, time, textwrap
from typing import List, Dict, Any

MODEL        = os.getenv("LICENSYNC_LLM_MODEL",  "gpt-3.5-turbo")
MAX_TOKENS   = int(os.getenv("LICENSYNC_LLM_TOKENS",  "350"))
TEMPERATURE  = float(os.getenv("LICENSYNC_LLM_TEMP",   "0.3"))
OPENAI_KEY   = os.getenv("OPENAI_API_KEY")

def _fmt_obl(obls: List[str]) -> str:
    return "\n".join(f"• {o}" for o in obls) or "• (none)"

def _chat(messages: List[Dict[str, Any]]) -> str:
    if not OPENAI_KEY:
        return "[LLM explanation unavailable: OPENAI_API_KEY not set]"
    import openai
    openai.api_key = OPENAI_KEY
    for attempt in range(3):
        try:
            rsp = openai.ChatCompletion.create(
                model=MODEL,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
                messages=messages,
            )
            return rsp.choices[0].message.content.strip()
        except Exception as e:
            if attempt == 2: return f"[LLM explanation unavailable: {e}]"
            time.sleep(2 ** attempt)

def generate_explanation(lic1: str,
                         lic2: str | None,
                         jurisdiction: str,
                         verdict: str,
                         obligations1: List[str] | None = None,
                         obligations2: List[str] | None = None) -> str:
    obligations1 = obligations1 or []
    obligations2 = obligations2 or []
    prompt = textwrap.dedent(f"""
    Two software components are licensed under **{lic1.upper()}** and **{lic2.upper()}**.
    Jurisdiction: **{jurisdiction.upper()}**. Verdict: **{verdict}**.

    Obligations for {lic1.upper()}:
    {_fmt_obl(obligations1)}

    Obligations for {lic2.upper()}:
    {_fmt_obl(obligations2)}

    Explain in 3–4 sentences how the obligations lead to this verdict.
    """)
    return _chat([
        {"role": "system", "content": "You are an open-source compliance lawyer who writes concise, precise rationales."},
        {"role": "user", "content": prompt},
    ])
