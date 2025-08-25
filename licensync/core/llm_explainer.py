# In licensync/core/llm_explainer.py

import os
import time
import textwrap
from typing import List, Dict, Any

# --- Configuration (remains the same) ---
MODEL        = os.getenv("LICENSYNC_LLM_MODEL",  "gpt-4o") # Using a more advanced model is recommended for reasoning
MAX_TOKENS   = int(os.getenv("LICENSYNC_LLM_TOKENS",  "200"))
TEMPERATURE  = float(os.getenv("LICENSYNC_LLM_TEMP",   "0.2"))
OPENAI_KEY   = "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"

# --- Helper function to format the list of obligations ---
def _fmt_obligations(obligations: List[str]) -> str:
    """Formats a list of obligations into a clean, bulleted string."""
    if not obligations:
        return "  • No specific obligations found."
    return "\\n".join(f"  • {o.capitalize().replace('_', ' ')}" for o in obligations)

# --- Chat function (remains the same) ---
def _chat(messages: List[Dict[str, Any]]) -> str:
    # ... (Your existing _chat function)
    if not OPENAI_KEY:
        return "[LLM explanation unavailable: OPENAI_API_KEY not set]"
    from openai import OpenAI
    
    client = OpenAI(api_key=OPENAI_KEY)
    for attempt in range(3):
        try:
            # Note: Ensure you are using a compatible OpenAI library version
            # For v1.0 and later:
            # client = openai.OpenAI()
            # response = client.chat.completions.create(...)
            # return response.choices[0].message.content.strip()

            # For older versions (e.g., v0.28):
            rsp = client.chat.completions.create(model=MODEL,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            messages=messages)
            return rsp.choices[0].message.content.strip()
        except Exception as e:
            if attempt == 2: return f"[LLM explanation unavailable: {e}]"
            time.sleep(2 ** attempt)

# --- NEW, IMPROVED Prompt Generation ---
def generate_explanation(lic1: str,
                         lic2: str,
                         jurisdiction: str,
                         verdict: str,
                         obligations1: List[str],
                         obligations2: List[str]) -> str:
    """Generates a detailed, legally-grounded explanation for a license compatibility verdict."""

    # This is the new, more sophisticated prompt template.
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

    # The system message primes the LLM with its role and desired tone.
    system_message = "You are a precise and knowledgeable open-source compliance lawyer. Your task is to provide clear, evidence-based rationales for license compatibility verdicts."

    return _chat([
        {"role": "system", "content": system_message},
        {"role": "user", "content": prompt},
    ])