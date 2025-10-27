from pathlib import Path
import json
from src.core.entity import collect_docs_entities, collect_files_and_json_entities
from src.core.project import Project

def test_parallel_files_entities():
    path = Path(__file__).parent / ".." / "mocks" / "projects" / "parallel_entities"
    p = Project(path)
    parallel_entities = collect_files_and_json_entities(p)
    dump = [[str(e) for e in pe.entities] for pe in parallel_entities]
    
    # Expected content - order-independent comparison for file system variations
    expected = [
        ['config', 'src'], 
        ['pyproject', '.gitlab-ci', 'README'], 
        ['list_item1', 'list_item2', 'list_item3'], 
        ['nested_key1', 'nested_key2', 'string_key'], 
        ['123', 'True', 'string_value'], 
        ['json_key1', 'json_key2', 'json_key3'], 
        ['string_value'], 
        ['name', 'yaml_key'], 
        ['entity1', 'entity1_value'], 
        ['name', 'yaml_key'], 
        ['entity2', 'entity2_value'], 
        ['yaml_key', 'entities'], 
        ['root_value'], 
        ['root'], 
        ['config', 'config'], 
        ['models', 'controllers'], 
        ['user', 'article']
    ]
    
    # Compare length first
    assert len(dump) == len(expected), f"Different number of entity containers: {len(dump)} vs {len(expected)}"
    
    # Compare each container, using sets for order-independent comparison where needed
    for i, (actual, expect) in enumerate(zip(dump, expected)):
        if len(actual) > 1 and len(expect) > 1:
            # For multi-item lists, compare as sets (order-independent)
            assert set(actual) == set(expect), f"At index {i}, content differs: {actual} vs {expect}"
        else:
            # For single items or empty lists, exact match is fine
            assert actual == expect, f"At index {i}, exact match required: {actual} vs {expect}"


def test_parallel_docs_entities():
    path = Path(__file__).parent / ".." / "mocks" / "projects" / "parallel_entities"
    p = Project(path)
    docs_entities = collect_docs_entities(p.documentation)
    dump = [[str(e) for e in pe.entities] for pe in docs_entities]
    
    expected = [['Title3', 'Title31', 'Title 32'], ['Title2'], ['Title1'], ['list_item1', 'list_item2']]
    
    # Compare length first
    assert len(dump) == len(expected), f"Different number of entity containers: {len(dump)} vs {len(expected)}"
    
    # Compare each container, using sets for order-independent comparison where needed
    for i, (actual, expect) in enumerate(zip(dump, expected)):
        if len(actual) > 1 and len(expect) > 1:
            # For multi-item lists, compare as sets (order-independent)
            assert set(actual) == set(expect), f"At index {i}, content differs: {actual} vs {expect}"
        else:
            # For single items or empty lists, exact match is fine
            assert actual == expect, f"At index {i}, exact match required: {actual} vs {expect}"
