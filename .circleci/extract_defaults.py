import re
import sys
import json
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import FoldedScalarString

def extract_variable_defaults(configmap_file):
    yaml = YAML()
    yaml.preserve_quotes = True

    with open(configmap_file, 'r') as f:
        config = yaml.load(f)

    values_yaml = config['data']['values.yaml']
    pattern = re.compile(r'\$\{(\w+):=((?:[^{}]|{[^{}]*})*)}')

    extracted = {}

    for line in values_yaml.splitlines():
        match = pattern.search(line)
        if match:
            var_name = match.group(1)
            default_val = match.group(2).strip()

            # Try parsing as JSON
            try:
                parsed_json = json.loads(default_val)

                if isinstance(parsed_json, (dict, list)):
                    # Pretty-print only if it's an object or array
                    pretty_json = json.dumps(parsed_json, indent=2)
                    extracted[var_name] = FoldedScalarString(pretty_json)
                else:
                    # Primitive types: use as-is (e.g., 0, true, "text")
                    extracted[var_name] = str(parsed_json)
                continue
            except json.JSONDecodeError:
                # Fallback to string
                extracted[var_name] = default_val

    # Replace the "values" suffix with "config" in the name of the sample CM
    if 'metadata' in config and 'name' in config['metadata']:
        original_name = config['metadata']['name']
        if original_name.endswith('values'):
            config['metadata']['name'] = original_name.replace('values', 'config')

    output = {
        'apiVersion': config['apiVersion'],
        'kind': config['kind'],
        'metadata': config['metadata'],
        'data': extracted
    }

    yaml.dump(output, sys.stdout)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python extract_defaults.py <input_file.yaml>")
        sys.exit(1)

    extract_variable_defaults(sys.argv[1])
