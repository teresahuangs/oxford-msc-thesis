
def create_license_node(self, license_id, name, type, obligations, permissions):
    query = """
    MERGE (l:License {id: $license_id})
    SET l.name = $name, l.type = $type,
        l.obligations = $obligations,
        l.permissions = $permissions
    RETURN l
    """
    return self.execute_write(query, {
        "license_id": license_id,
        "name": name,
        "type": type,
        "obligations": obligations,
        "permissions": permissions
    })

def link_model_to_license(self, model_id, license_id):
    query = """
    MATCH (m:Model {id: $model_id}), (l:License {id: $license_id})
    MERGE (m)-[:USES_LICENSE]->(l)
    """
    self.execute_write(query, {"model_id": model_id, "license_id": license_id})
