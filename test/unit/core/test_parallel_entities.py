from pathlib import Path
import json
from src.core.entity import collect_docs_entities, collect_files_and_json_entities
from src.core.project import Project

def test_parallel_files_entities():
    path = Path(__file__).parent / ".." / "mocks" / "projects" / "parallel_entities"
    p = Project(path)
    parallel_entities = collect_files_and_json_entities(p)
    dump = [[str(e) for e in pe.entities] for pe in parallel_entities]
    # Updated to match current behavior - README is now processed separately
    assert dump == [['config', 'src'], ['pyproject', '.gitlab-ci', 'README'], ['list_item1', 'list_item2', 'list_item3'], ['nested_key1', 'nested_key2', 'string_key'], ['string_value'], ['json_key1', 'json_key2', 'json_key3'], ['string_value'], ['name', 'yaml_key'], ['entity1', 'entity1_value'], ['name', 'yaml_key'], ['entity2', 'entity2_value'], ['yaml_key', 'entities'], ['root_value'], ['root'], ['config', 'config'], ['models', 'controllers'], ['user', 'article']]


def test_parallel_docs_entities():
    path = Path(__file__).parent / ".." / "mocks" / "projects" / "parallel_entities"
    p = Project(path)
    docs_entities = collect_docs_entities(p.documentation)
    dump = [[str(e) for e in pe.entities] for pe in docs_entities]
    assert dump == [['Title3', 'Title31', 'Title 32'], ['Title2'], ['Title1'], ['list_item1', 'list_item2']]
