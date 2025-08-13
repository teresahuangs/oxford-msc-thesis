# In licensync/core/license_utils.py

import re

# This dictionary maps various SPDX string formats to the simple atoms used in rules.pl
SPDX_TO_PROLOG = {
    "mit": "mit",
    "apache-2.0": "apache2",
    "apache2.0": "apache2",
    "bsd-3-clause": "bsd3",
    "bsd-2-clause": "bsd2",
    "mpl-2.0": "mpl2",
    "lgpl-3.0-only": "lgpl3",
    "lgpl-3.0-or-later": "lgpl3",
    "lgpl-2.1-only": "lgpl2",
    "lgpl-2.1-or-later": "lgpl2",
    "gpl-3.0-only": "gpl3",
    "gpl-3.0-or-later": "gpl3",
    "gpl-2.0-only": "gpl2",
    "gpl-2.0-or-later": "gpl2",
    "agpl-3.0-only": "agpl3",
    "agpl-3.0-or-later": "agpl3",
    "epl-2.0": "epl2",
    "cc0-1.0": "cc0",
    "0bsd": "bsd0",
    "sspl-1.0": "sspl",
    "commons-clause": "commons_clause",
    "cc-by-nc-sa-4.0": "cc_by_nc_sa_4",
    "confluent-community-1.0": "confluent_community_1",
    "elastic-license-2.0": "elastic2",
    "unlicense": "unlicense",
    "isc": "isc",
    "unknown": "unknown",
}

def normalize_license(license_str: str) -> str:
    """
    Cleans and normalizes a license string to its corresponding Prolog atom.
    """
    if not license_str:
        return "unknown"
    
    # Convert to lowercase and strip whitespace
    s = str(license_str).strip().lower()
    
    # Remove trailing text in parentheses, e.g., "bsd-3-clause (new or revised)"
    s = re.sub(r'\\s*\\(.*\\)\\s*$', '', s)
    
    # Use the dictionary for direct lookups
    if s in SPDX_TO_PROLOG:
        return SPDX_TO_PROLOG[s]
    
    # Fallback for other minor variations, like replacing spaces/underscores with a dash
    s = re.sub(r'[\\s_]+', '-', s)
    
    # Check the dictionary again after cleanup
    return SPDX_TO_PROLOG.get(s, s)