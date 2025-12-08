
import os
import yaml
import jsonschema
from dataclasses import dataclass, field
from typing import List, Optional

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "config", "ducku_schema.yaml")


class BaseOptions:
    """Base options for use cases."""
    def __init__(self):
        self.enabled = True


@dataclass
class PatternSearchOptions(BaseOptions):
    disabled_patterns: Optional[List[str]] = field(default_factory=list)


@dataclass
class UseCasesOptions:
    pattern_search: PatternSearchOptions = field(default_factory=PatternSearchOptions)
    unused_modules: BaseOptions = field(default_factory=BaseOptions)
    spellcheck: BaseOptions = field(default_factory=BaseOptions)
    partial_lists: BaseOptions = field(default_factory=BaseOptions)


@dataclass
class Configuration:
    documentation_paths: Optional[List[str]] = field(default_factory=list)
    disabled_use_cases: Optional[List[str]] = field(default_factory=list)
    code_paths_to_ignore: Optional[List[str]] = field(default_factory=list)
    documentation_paths_to_ignore: Optional[List[str]] = field(default_factory=list)
    use_case_options: UseCasesOptions = field(default_factory=UseCasesOptions)
    fail_on_issues: bool = False

def load_schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def parse_ducku_yaml(project_root):
    config_path = os.path.join(project_root, ".ducku.yaml")
    if not os.path.exists(config_path):
        return Configuration()
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print("\n❌ Error: .ducku.yaml is either empty or YAML syntax is not correct")
        print(f"Problem: {str(e)}\n")
        raise SystemExit(1) from e
    except Exception as e:
        print("\n❌ Error: Failed to read .ducku.yaml due to OS error")
        print(f"Problem: {str(e)}\n")
        raise SystemExit(1) from e
    
    if config is None:
        return Configuration()
    
    schema = load_schema()
    try:
        jsonschema.validate(instance=config, schema=schema)
    except jsonschema.ValidationError as e:
        print("\n❌ Error: .ducku.yaml validation failed")
        print(f"Problem: {e.message}\n")
        raise SystemExit(1) from e
    except Exception as e:
        print("\n❌ Error: Invalid .ducku.yaml")
        print(f"Problem: {str(e)}\n")
        raise SystemExit(1) from e
    
    return Configuration(**config)
