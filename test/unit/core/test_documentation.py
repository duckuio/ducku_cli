from pathlib import Path
from unittest.mock import MagicMock

from anytree import RenderTree
from src.core.entity import collect_docs_entities
from src.core.documentation import Documentation

def test_parse_md():
    txt = """
# Header H1

Some text

## Header H2

More text

### Header H3

Here goes the list

* Bullet 1
* Bullet 2
  * Bullet 22
  * Bullet 23
* Bullet 3

Another type

- Item 1
- Item 2
  - Subitem 22
  - Subitem 23

### Header H3 number 2"""
    global_doc = Documentation().from_string(txt, "markdown")
    doc = global_doc.doc_parts[0]
    
    print(doc.headers)
    print(doc.lists)

    # Check that headers were parsed
    assert len(doc.headers.children) > 0
    assert doc.headers.children[0].name == "Header H1"
    assert doc.headers.children[0].level == 1
    
    # Check that lists were parsed
    assert len(doc.lists.children) > 0

    for pre, fill, node in RenderTree(doc.lists):
        print("%s%s" % (pre, node.name))


    for pre, fill, node in RenderTree(doc.headers):
        print("%s%s" % (pre, node.name))

    print(f"Found {len(doc.headers.children)} header trees and {len(doc.lists.children)} lists")

    res = collect_docs_entities(global_doc)
    print(res)


def test_doc_entities_with_header_namespace():
    """Test that documentation entities include header names in their namespace."""
    markdown_content = """
# Installation Guide

This is the main installation section.

## Prerequisites

- Python 3.8+
- pip package manager

## Step-by-Step

1. Clone repository
2. Install dependencies

# Configuration

## Environment Variables

- API_KEY
- DATABASE_URL

## Settings File

Edit config.yaml
"""
    
    doc = Documentation().from_string(markdown_content, "markdown")
    entities = collect_docs_entities(doc)
    
    # Find all entity containers
    containers_by_parent = {c.parent: c for c in entities}
    
    # Test that h1 headers are in namespace for doc_header type
    h1_installation_key = None
    h1_configuration_key = None
    for key in containers_by_parent.keys():
        if "::h1::Installation Guide" in key and "::h2::" not in key:
            h1_installation_key = key
        if "::h1::Configuration" in key and "::h2::" not in key:
            h1_configuration_key = key
    
    # Check that Installation Guide header container exists
    assert h1_installation_key is not None, "Should have container with 'Installation Guide' in namespace"
    installation_container = containers_by_parent[h1_installation_key]
    entity_names = [e.name for e in installation_container.entities]
    assert "Prerequisites" in entity_names, "Installation Guide should contain Prerequisites"
    assert "Step-by-Step" in entity_names, "Installation Guide should contain Step-by-Step"
    
    # Check that Configuration header container exists
    assert h1_configuration_key is not None, "Should have container with 'Configuration' in namespace"
    config_container = containers_by_parent[h1_configuration_key]
    entity_names = [e.name for e in config_container.entities]
    assert "Settings File" in entity_names, "Configuration should contain Settings File header"
    
    # Verify list items are captured with header context
    list_containers = [c for c in entities if "bullet_list" in c.parent or "ordered_list" in c.parent]
    assert len(list_containers) >= 2, "Should have at least 2 list containers"
    
    # Check that list items have header context in their parent path
    prereq_list = [c for c in list_containers if "Prerequisites" in c.parent]
    assert len(prereq_list) > 0, "Should have list under Prerequisites with header in path"
    
    env_var_list = [c for c in list_containers if "Environment Variables" in c.parent]
    assert len(env_var_list) > 0, "Should have list under Environment Variables with header in path"
    
    # Verify the full header path is in the list container parent
    env_var_container = env_var_list[0]
    assert "::h1::Configuration::h2::Environment Variables" in env_var_container.parent, \
        "Environment Variables list should have full header hierarchy in parent path"
    
    # Check specific list items
    prereq_items = []
    for c in list_containers:
        if "Prerequisites" in c.parent:
            prereq_items.extend([e.name for e in c.entities])
    assert "Python 3.8+" in prereq_items, "Should capture Python 3.8+ from Prerequisites"
    assert "pip package manager" in prereq_items, "Should capture pip from Prerequisites"


def test_nested_doc_headers_in_namespace():
    """Test that nested headers create hierarchical namespaces."""
    markdown_content = """
# API Reference

## Authentication

### OAuth2

- client_id
- client_secret

### API Keys

- api_key
- secret_key

## Endpoints

### Users

- GET /users
- POST /users
"""
    
    doc = Documentation().from_string(markdown_content, "markdown")
    entities = collect_docs_entities(doc)
    
    # Find containers with nested header paths
    auth_container = None
    endpoints_container = None
    
    for c in entities:
        if "::h1::API Reference::h2::Authentication" in c.parent:
            auth_container = c
        if "::h1::API Reference::h2::Endpoints" in c.parent:
            endpoints_container = c
    
    # Verify Authentication subsection
    assert auth_container is not None, "Should have container for Authentication under API Reference"
    auth_entities = [e.name for e in auth_container.entities]
    assert "OAuth2" in auth_entities, "Authentication should contain OAuth2"
    assert "API Keys" in auth_entities, "Authentication should contain API Keys"
    
    # Verify Endpoints subsection
    assert endpoints_container is not None, "Should have container for Endpoints under API Reference"
    endpoints_entities = [e.name for e in endpoints_container.entities]
    assert "Users" in endpoints_entities, "Endpoints should contain Users"
    
    # Verify the hierarchy is clear in parent path
    assert "::h1::API Reference::h2::Authentication" in auth_container.parent
    assert "::h1::API Reference::h2::Endpoints" in endpoints_container.parent
