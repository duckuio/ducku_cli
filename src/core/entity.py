import os
from pathlib import Path
from typing import List, Optional
from src.core.documentation import Documentation
from src.helpers.json import collect_json_keys

class Entity:
    def __init__(self, name: str, entity_object=None):
        self.name = name
        self.object = entity_object

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

class EntitiesContainer:
    def __init__(self, parent: str, type: str):
        self.entities = []
        self.parent = parent
        self.type = type

    def append(self, entity: Entity):
        self.entities.append(entity)


def recursive_collect_doc_entities(children, parallel_entities: List[EntitiesContainer], parent_type):
    if children:
        ls = EntitiesContainer(parent_type, "documentation")
        for n in children:
            if n.kind == "__bullet_list":
                recursive_collect_doc_entities(n.children, parallel_entities, parent_type + "::bullet_list")
                continue # __bullet_list is just container
            if n.children:
                recursive_collect_doc_entities(n.children, parallel_entities, parent_type + "::" + n.kind)
            ls.append(Entity(n.name, parent_type))
        if ls.entities:
            parallel_entities.append(ls)

def collect_docs_entities(documentation: Documentation) -> List[EntitiesContainer]:
    parallel_entities = []
    for part in documentation.doc_parts:
        if part.headers and part.headers.children:
            recursive_collect_doc_entities(part.headers.children, parallel_entities, part.source.get_source_identifier() + "::doc_header")
        if part.lists and part.lists.children:
            recursive_collect_doc_entities(part.lists.children, parallel_entities, part.source.get_source_identifier() + "::doc_list")
    return parallel_entities

def collect_files_and_json_entities(project) -> List[EntitiesContainer]:
    parallel_entities = []
    for walk_item in project.walk_items:
        root = walk_item.root
        files = walk_item.files
        dirs = walk_item.dirs
        relative_root = Path(root).relative_to(project.project_root)
        parallel_files = EntitiesContainer(str(relative_root), "file")
        parallel_dirs = EntitiesContainer(str(relative_root), "directory")
        for f in files:
            e = Entity(f.stem, f)
            if f.suffix.lower() in [".yaml", ".yml", ".json", ".xml"]:
                collect_json_keys(f, parallel_entities)
            parallel_files.append(e)
        for d in dirs:
            e = Entity(d)
            parallel_dirs.append(e)
        if parallel_dirs.entities:
            parallel_entities.append(parallel_dirs)
        if parallel_files.entities:
            parallel_entities.append(parallel_files)
    return parallel_entities
