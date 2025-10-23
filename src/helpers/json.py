import json
from pathlib import Path
from typing import List
import yaml
from src.helpers.logger import get_logger
log = get_logger(__name__)

class IgnoreUnknownTagsLoader(yaml.SafeLoader):
    """
    Custom loader that ignores unknown YAML tags instead of throwing an error.
    """

def unknown_tag_handler(loader, tag_suffix, node):
    return 'unknownyamltag'

IgnoreUnknownTagsLoader.add_multi_constructor('', unknown_tag_handler)

def is_corrupted(value):
    return "\n" in value or len(value) > 50

def collect_key_values(data, parallel_entities, parent):
    from src.core.entity import Entity, EntitiesContainer  # Import here to avoid circular dependency
    key_items = EntitiesContainer(parent, "json_keys")
    value_items = EntitiesContainer(parent, "json_values")
    if isinstance(data, dict):
        for key, value in data.items():
            if not is_corrupted(key):
                key_items.append(Entity(key))
            if isinstance(value, str):
                if not is_corrupted(value):
                    value_items.append(Entity(value))
            else:
                collect_key_values(value, parallel_entities, parent + "::" + key)
        if key_items.entities:
            parallel_entities.append(key_items)
        if value_items.entities:
            parallel_entities.append(value_items)
    elif isinstance(data, list):
        for value in data:
            if isinstance(value, str):
                if not is_corrupted(value):
                    value_items.append(Entity(value))
            else:
                collect_key_values(value, parallel_entities, parent)
        if value_items.entities:
            parallel_entities.append(value_items)

def collect_json_keys(file: Path, parallel_entities: List):
    ext = file.suffix
    data = None
    if ext in (".yaml", ".yml"):
        try:
            content = file.read_text()
            data = yaml.load(content, Loader=IgnoreUnknownTagsLoader)
        except Exception as e:
            log.error(e)
    elif ext == ".json":
        content = file.read_text()
        try:
            data = json.loads(content)
        except Exception as e:
            log.error(e)
    if data:
        collect_key_values(data, parallel_entities, str(file))
