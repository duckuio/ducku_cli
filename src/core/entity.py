import os
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
                # Build namespace with header name for better context
                if n.kind.startswith("h"):  # Header nodes (h1, h2, h3, etc.)
                    child_parent_type = parent_type + "::" + n.kind + "::" + n.name
                else:
                    child_parent_type = parent_type + "::" + n.kind
                recursive_collect_doc_entities(n.children, parallel_entities, child_parent_type)
            if len(n.name) > 20: # skip long names. It's not entities anymore, it's sentences
                continue
            ls.append(Entity(n.name, parent_type))
        if ls.entities:
            parallel_entities.append(ls)

def collect_docs_entities(documentation: Documentation) -> List[EntitiesContainer]:
    parallel_entities = []
    for part in documentation.doc_parts:
        if part.headers and part.headers.children:
            recursive_collect_doc_entities(part.headers.children, parallel_entities, part.source.get_source_identifier())
        if part.lists and part.lists.children:
            recursive_collect_doc_entities(part.lists.children, parallel_entities, part.source.get_source_identifier())
        
        # Process code blocks if they exist
        if part.code_blocks:
            from src.core.documentation import _parse_code_block
            for code_block in part.code_blocks:
                _parse_code_block(
                    code_block['content'],
                    code_block['language'],
                    code_block['parent_path'],
                    parallel_entities
                )
    return parallel_entities

# Extends the entities list
def collect_json_entities(project, entities):
    for f in project.project_files:
        if f.suffix.lower() in [".yaml", ".yml", ".json", ".xml"]:
            collect_json_keys(f, entities)

# Extends the entities list
def collect_files_and_dirs(project, entities):
    
    for walk_item in project.walk_items:
        files = walk_item.files
        dirs = walk_item.dirs
        relative_root = walk_item.relative_root
        parallel_files = EntitiesContainer(str(relative_root), "file")
        parallel_dirs = EntitiesContainer(str(relative_root), "directory")
        for f in files:
            # Skip non-informative filenames
            if f.stem:
                e = Entity(f.stem, f)
                parallel_files.append(e)
        for d in dirs:
            e = Entity(d)
            parallel_dirs.append(e)
        if parallel_dirs.entities:
            entities.append(parallel_dirs)
        if parallel_files.entities:
            entities.append(parallel_files)
    return entities

def collect_code_entities(project, entities):
    from src.core.code.dispatcher import collect_code_entities_from_content
    for f in project.project_files:
        collect_code_entities_from_content(f, entities)

def collect_project_entities(project) -> List[EntitiesContainer]:
    entities = []
    collect_json_entities(project, entities)
    collect_files_and_dirs(project, entities)
    collect_code_entities(project, entities)
    return entities
