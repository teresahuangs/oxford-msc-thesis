
def process_license_info(graph, model_id, license_info):
    if not license_info:
        return
    license_id = license_info.get("license", "unknown")
    name = license_info.get("license_name", license_id)
    link = license_info.get("license_link", "")
    obligations = license_info.get("obligations", [])
    permissions = license_info.get("permissions", [])
    graph.create_license_node(license_id, name, "auto", obligations, permissions)
    graph.link_model_to_license(model_id, license_id)
