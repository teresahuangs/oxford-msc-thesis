
import re

SPDX_TO_PROLOG = {
    "mit": "mit",
    "apache-2.0": "apache2",
    "apache2.0": "apache2",
    "bsd-3-clause": "bsd3",
    "bsd-2-clause": "bsd2",
    "mpl-2.0": "mpl2",
    "lgpl-3.0": "lgpl3",
    "gpl-3.0": "gpl3",
    "gpl-3.0-only": "gpl3",
    "gpl-3.0-or-later": "gpl3",
    "agpl-3.0": "agpl3",
    "agpl-3.0-only": "agpl3",
    "agpl-3.0-or-later": "agpl3",
    "sspl-1.0": "sspl",
    "llama-2": "llama_nc",
    "llama-2-community": "llama_nc",
    "openrail": "openrail",
    "unknown": "unknown",
}

def normalize_license(license_str: str) -> str:
    if not license_str:
        return "unknown"
    s = license_str.strip().lower()
    s = re.sub(r'\s*\(.*?\)\s*$', '', s)      # strip trailing parentheses
    s = re.sub(r'[\s_]+', '-', s)                # collapse whitespace/underscores
    return SPDX_TO_PROLOG.get(s, s.replace('-', ''))
