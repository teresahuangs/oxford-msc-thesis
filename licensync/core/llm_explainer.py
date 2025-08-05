"""
LLM-based natural-language rationale generator
==============================================

from licensync.core.llm_explainer import generate_explanation
txt = generate_explanation("mit", "sspl", "eu", "incompatible")
print(txt)
"""

from __future__ import annotations
import os, time, textwrap, openai
from typing import List, Dict, Any

# ──────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────
MODEL        = os.getenv("LICENSYNC_LLM_MODEL",  "gpt-3.5-turbo")
MAX_TOKENS   = int(os.getenv("LICENSYNC_LLM_TOKENS",  "350"))
TEMPERATURE  = float(os.getenv("LICENSYNC_LLM_TEMP",   "0.3"))
DEBUG_MODE   = bool(os.getenv("LICENSYNC_LLM_DEBUG"))
OPENAI_KEY   = os.getenv("OPENAI_API_KEY")                # set in shell

if not OPENAI_KEY:
    raise RuntimeError("OPENAI_API_KEY not set; export it in your shell.")
openai.api_key = OPENAI_KEY

# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────
def _fmt_obl(obls: List[str]) -> str:
    return "\n".join(f"• {o}" for o in obls) or "• (none)"

def _chat(messages: List[Dict[str, Any]],
          model: str = MODEL,
          max_tokens: int = MAX_TOKENS,
          temp: float = TEMPERATURE,
          tries: int = 3) -> str:
    """OpenAI call with exponential back-off."""
    for attempt in range(tries):
        try:
            rsp = openai.ChatCompletion.create(
                model=model,
                temperature=temp,
                max_tokens=max_tokens,
                messages=messages,
            )
            return rsp.choices[0].message.content.strip()
        except openai.error.RateLimitError:
            if attempt == tries - 1:
                raise
            time.sleep(2 ** attempt)      # 1s, 2s, 4s …
        except openai.error.OpenAIError:
            raise                         # network / auth / quota etc.

# ──────────────────────────────────────────────────────────────
# Public entry point
# ──────────────────────────────────────────────────────────────
def generate_explanation(
    lic1: str,
    lic2: str | None,
    jurisdiction: str,
    verdict: str,
    obligations1: List[str] | None = None,
    obligations2: List[str] | None = None,
) -> str:
    """Return a plain-English rationale; never returns ''. """
    obligations1 = obligations1 or []
    obligations2 = obligations2 or []

    if lic2:
        prompt = textwrap.dedent(f"""
        Two software components are licensed under **{lic1.upper()}**
        and **{lic2.upper()}**.  Jurisdiction: **{jurisdiction.upper()}**.

        • Verdict → **{verdict}**

        Obligations for {lic1.upper()}:
        {_fmt_obl(obligations1)}

        Obligations for {lic2.upper()}:
        {_fmt_obl(obligations2)}

        Explain in 3–4 sentences how the obligations lead to this verdict.
        Avoid legal disclaimers; be concise but precise.
        """)
    else:
        prompt = textwrap.dedent(f"""
        Summarise the obligations that apply to licence **{lic1.upper()}**
        in **{jurisdiction.upper()}**:

        {_fmt_obl(obligations1)}

        Provide a short (max 3 sentences) explanation for developers.
        """)

    if DEBUG_MODE:                       # optional debug echo
        print("▼ LLM prompt\n", prompt, "\n▲ end prompt", flush=True)

    try:
        return _chat(
            [
                {"role": "system",
                 "content": ("You are an open-source compliance lawyer who "
                             "writes concise, plain-English rationales.")},
                {"role": "user", "content": prompt},
            ]
        )
    except Exception as exc:
        return f"[LLM explanation unavailable: {exc}]"
