
import os
import yaml
import jsonschema
from dataclasses import dataclass, field
from typing import List, Optional
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "config", "ducku_schema.yaml")

@dataclass
class Configuration:
    documentation_paths: Optional[List[str]] = field(default_factory=list)
    disabled_use_cases: Optional[List[str]] = field(default_factory=list)
    disabled_pattern_search_patterns: Optional[List[str]] = field(default_factory=list)

def load_schema():
	with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
		return yaml.safe_load(f)

def parse_ducku_yaml(project_root):
	config_path = os.path.join(project_root, ".ducku.yaml")
	if not os.path.exists(config_path):
		return Configuration()
	with open(config_path, "r", encoding="utf-8") as f:
		config = yaml.safe_load(f)
	schema = load_schema()
	try:
		jsonschema.validate(instance=config, schema=schema)
	except jsonschema.ValidationError as e:
		raise ValueError(f"Invalid .ducku.yaml: {e.message}") from e
	return Configuration(**config)
