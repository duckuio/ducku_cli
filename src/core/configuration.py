
import os
import yaml
import jsonschema

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "config", "documentory_schema.yaml")

def load_schema():
	with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
		return yaml.safe_load(f)

def parse_documentory_yaml(project_root):
	config_path = os.path.join(project_root, ".documentory.yaml")
	if not os.path.exists(config_path):
		return None
	with open(config_path, "r", encoding="utf-8") as f:
		config = yaml.safe_load(f)
	schema = load_schema()
	try:
		jsonschema.validate(instance=config, schema=schema)
	except jsonschema.ValidationError as e:
		raise ValueError(f"Invalid .documentory.yaml: {e.message}") from e
	return config
