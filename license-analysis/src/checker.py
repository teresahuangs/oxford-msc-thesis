def check_pairwise_compatibility(license1, license2):
    l1, l2 = license1['license_id'], license2['license_id']
    if l2 in license1.get('incompatible_with', []) or l1 in license2.get('incompatible_with', []):
        return False, f"Incompatible: {l1} vs {l2}"
    if l2 in license1.get('compatible_with', []) or l1 in license2.get('compatible_with', []):
        return True, f"Explicitly compatible: {l1} vs {l2}"
    return None, f"Unknown compatibility: {l1} vs {l2}"

def check_project(project, licenses):
    violations = []
    components = project['components']
    for i, comp1 in enumerate(components):
        for j, comp2 in enumerate(components):
            if i < j:
                l1 = licenses.get(comp1['license'])
                l2 = licenses.get(comp2['license'])
                if l1 and l2:
                    ok, msg = check_pairwise_compatibility(l1, l2)
                    if ok is False:
                        violations.append(msg)
    return violations
