# licensync/core/llm_explainer.py
import openai
import os

openai.api_key = "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"

def generate_explanation(license1, license2, jurisdiction, verdict):
    prompt = f"""
Two software components are licensed under '{license1}' and '{license2}'.
The jurisdiction is '{jurisdiction}'.
The automated system evaluated the pair and concluded: '{verdict}'.

Can you explain in simple terms why this compatibility result holds,
based on the general characteristics of these licenses and jurisdictional influences?
Keep it concise but informative.
"""

    response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",  # instead of "gpt-4"
    messages=[
        {"role": "system", "content": "You are an expert in open-source licensing and legal compliance."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.3,
    max_tokens=300
)


    return response["choices"][0]["message"]["content"].strip()
