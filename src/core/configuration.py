
import os
import yaml
import jsonschema
from pydantic import BaseModel, Field
from dataclasses import dataclass, field, fields
from typing import List, Optional

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "config", "ducku_schema.yaml")


class BaseOptions(BaseModel):
    enabled: bool = True

class PatternSearchOptions(BaseOptions):
    disabled_patterns: Optional[List[str]] = Field(default_factory=list)

class UseCasesOptions(BaseModel):
    pattern_search: PatternSearchOptions = Field(default_factory=PatternSearchOptions)
    unused_modules: BaseOptions = Field(default_factory=BaseOptions)
    spellcheck: BaseOptions = Field(default_factory=BaseOptions)
    partial_lists: BaseOptions = Field(default_factory=BaseOptions)

class Configuration(BaseModel):
    documentation_paths: Optional[List[str]] = Field(default_factory=list)
    code_paths_to_ignore: Optional[List[str]] = Field(default_factory=list)
    documentation_paths_to_ignore: Optional[List[str]] = Field(default_factory=list)
    use_case_options: UseCasesOptions = Field(default_factory=UseCasesOptions)
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
    
    return Configuration(**config)
