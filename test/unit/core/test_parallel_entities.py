from pathlib import Path
import json
from src.core.entity import collect_docs_entities, collect_project_entities
from src.core.project import Project

def test_parallel_files_entities():
    path = Path(__file__).parent / ".." / "mocks" / "projects" / "parallel_entities"
    p = Project(path)
    parallel_entities = collect_project_entities(p)
    dump = [[str(e) for e in pe.entities] for pe in parallel_entities]
    
    # Expected containers - check by converting to sets for order-independent comparison
    expected_containers = [
        {'config', 'src'},  # Root level subdirectories
        {'pyproject', '.gitlab-ci', 'README'},  # Root level files
        {'list_item1', 'list_item2', 'list_item3'},  # JSON entities from config files
        {'nested_key1', 'nested_key2', 'string_key'},
        {'123', 'True', 'string_value'},
        {'json_key1', 'json_key2', 'json_key3'},
        {'string_value'},
        {'yaml_key'},  # 'name' filtered out by to_filter_key
        {'entity1', 'entity1_value'},
        {'yaml_key'},  # 'name' filtered out by to_filter_key
        {'entity2', 'entity2_value'},
        {'yaml_key', 'entities'},
        {'root_value'},
        {'root'},
        {'config'},  # config directory files (single item)
        {'models', 'controllers'},  # src/ level subdirectories
        {'user', 'article'},  # src/models/ files
        {'.gitkeep'}  # src/controllers/ files
    ]
    
    # Convert actual to sets
    actual_containers = [set(container) for container in dump]
    
    # Check we have the same number of containers
    assert len(actual_containers) == len(expected_containers), \
        f"Different number of entity containers: {len(actual_containers)} vs {len(expected_containers)}"
    
    # Check each expected container exists in actual (order-independent)
    for expected_set in expected_containers:
        assert expected_set in actual_containers, \
            f"Expected container {expected_set} not found in actual containers"
    
    # Check no extra containers
    for actual_set in actual_containers:
        assert actual_set in expected_containers, \
            f"Unexpected container {actual_set} found in actual containers"
    
    # Additional verification: ensure certain key entities are present
    all_entities = [item for sublist in dump for item in sublist]
    assert 'config' in all_entities, "config directory should be found"
    assert 'src' in all_entities, "src directory should be found"
    assert 'models' in all_entities, "models directory should be found"
    assert 'controllers' in all_entities, "controllers directory should be found"
    assert 'user' in all_entities, "user file should be found"
    assert 'article' in all_entities, "article file should be found"


def test_parallel_docs_entities():
    path = Path(__file__).parent / ".." / "mocks" / "projects" / "parallel_entities"
    p = Project(path)
    docs_entities = collect_docs_entities(p.documentation)
    
    # With the new implementation, headers and lists are processed separately with full hierarchy
    # We should have:
    # 1. Header hierarchy containers (from headers tree)
    # 2. List containers with their header context (from lists tree)
    
    # Find containers by their content
    title3_container = None
    title2_container = None
    title1_container = None
    list_container = None
    
    for pe in docs_entities:
        entities = [str(e) for e in pe.entities]
        if 'Title3' in entities and 'Title31' in entities and 'Title 32' in entities:
            title3_container = entities
        elif entities == ['Title2']:
            title2_container = entities
        elif entities == ['Title1']:
            title1_container = entities
        elif 'list_item1' in entities and 'list_item2' in entities:
            list_container = entities
    
    # Verify all expected containers exist
    assert title3_container is not None, "Should have container with Title3, Title31, Title 32"
    assert set(title3_container) == {'Title3', 'Title31', 'Title 32'}
    
    assert title2_container is not None, "Should have container with Title2"
    assert title2_container == ['Title2']
    
    assert title1_container is not None, "Should have container with Title1"
    assert title1_container == ['Title1']
    
    assert list_container is not None, "Should have container with list items"
    assert set(list_container) == {'list_item1', 'list_item2'}
    
    # Verify that list container has proper header hierarchy in parent
    list_parent = None
    for pe in docs_entities:
        entities = [str(e) for e in pe.entities]
        if 'list_item1' in entities:
            list_parent = pe.parent
            break
    
    assert list_parent is not None, "Should find list container parent"
    assert 'Title1' in list_parent, "List parent should include Title1 in hierarchy"
    assert 'Title2' in list_parent, "List parent should include Title2 in hierarchy"
    assert 'Title3' in list_parent, "List parent should include Title3 in hierarchy"
    assert 'bullet_list' in list_parent, "List parent should indicate it's a bullet_list"
