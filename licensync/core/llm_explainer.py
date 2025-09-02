# In licensync/core/llm_explainer.py

import os
import time
import textwrap
from typing import List, Dict, Any

# --- Configuration (remains the same) ---
MODEL        = os.getenv("LICENSYN_LLM_MODEL",  "gpt-4o") # Using a more advanced model is recommended
MAX_TOKENS   = int(os.getenv("LICENSYNC_LLM_TOKENS",  "200"))
TEMPERATURE  = float(os.getenv("LICENSYNC_LLM_TEMP",   "0.2"))
OPENAI_KEY   = os.getenv("OPENAI_API_KEY")

# --- Helper function (remains the same) ---
def _fmt_obligations(obligations: List[str]) -> str:
    if not obligations:
        return "  • No specific obligations found."
    return "\\n".join(f"  • {o.capitalize().replace('_', ' ')}" for o in obligations)

def _chat(messages: List[Dict[str, Any]]) -> str:
    """
    Connects to the OpenAI API using the modern (v1.0.0+) library syntax.
    """
    if not OPENAI_KEY:
        return "[LLM explanation unavailable: OPENAI_API_KEY not set]"
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_KEY)
    except ImportError:
        return "[LLM explanation unavailable: The 'openai' library is not installed or is too old.]"

    for attempt in range(3):
        try:
            # This is the new, correct way to make the API call
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            if attempt == 2:
                return f"[LLM explanation unavailable after 3 attempts. Error: {e}]"
            time.sleep(2 ** attempt)
    return "[LLM explanation failed after multiple retries.]"


# --- Prompt Generation function (remains the same) ---
def generate_explanation(lic1: str,
                         lic2: str,
                         jurisdiction: str,
                         verdict: str,
                         obligations1: List[str],
                         obligations2: List[str]) -> str:
    # This function is correct and does not need changes
    prompt = textwrap.dedent(f"""
    **Case Details:**
    - **License A:** {lic1.upper()}
    - **License B:** {lic2.upper()}
    - **Jurisdiction:** {jurisdiction.upper()}
    - **Final Verdict:** {verdict.upper()}

    **Evidence: Known Obligations**
    - **Obligations for {lic1.upper()}:**
    {_fmt_obligations(obligations1)}
    - **Obligations for {lic2.upper()}:**
    {_fmt_obligations(obligations2)}

    **Task:**
    As an expert in open-source software compliance, write a concise, 2-4 sentence explanation for the verdict.
    You MUST base your reasoning *directly* on the provided obligations. Do not introduce outside information.
    Explain how the specific obligations of the two licenses conflict or align to produce the given verdict.
    """)
    system_message = "You are a precise and knowledgeable open-source compliance lawyer. Your task is to provide clear, evidence-based rationales for license compatibility verdicts."
    return _chat([
        {"role": "system", "content": system_message},
        {"role": "user", "content": prompt},
    ])