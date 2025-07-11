import os
import yaml

def load_yaml_dir(directory):
    data = {}
    for filename in os.listdir(directory):
        if filename.endswith('.yaml'):
            with open(os.path.join(directory, filename)) as f:
                obj = yaml.safe_load(f)
                data[obj['license_id'] if 'license_id' in obj else obj['project_id']] = obj
    return data

