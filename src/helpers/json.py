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
    # Convert to string if not already a string
    if not isinstance(value, str):
        value = str(value)
    return "\n" in value or len(value) > 50

def to_filter_key(key):
    filter_keys = ["if", "when", "id", "uuid", "name", "type", "version", "lang", "language", "title", "description", "date", "created_at", "updated_at"]
    if not isinstance(key, str):
        key = str(key)
    return key.lower() in filter_keys or len(key) > 30

def collect_key_values(data, parallel_entities, parent):
    from src.core.entity import Entity, EntitiesContainer  # Import here to avoid circular dependency
    key_items = EntitiesContainer(parent, "json_keys")
    value_items = EntitiesContainer(parent, "json_values")
    if isinstance(data, dict):
        for key, value in data.items():
            if not is_corrupted(key) and not to_filter_key(key):
                key_items.append(Entity(str(key)))
            if isinstance(value, (str, int, float, bool)):
                if not is_corrupted(value):
                    value_items.append(Entity(str(value)))
            else:
                collect_key_values(value, parallel_entities, parent + "::" + str(key))
        if key_items.entities:
            parallel_entities.append(key_items)
        if value_items.entities:
            parallel_entities.append(value_items)
    elif isinstance(data, list):
        for value in data:
            if isinstance(value, (str, int, float, bool)):
                if not is_corrupted(value):
                    value_items.append(Entity(str(value)))
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
