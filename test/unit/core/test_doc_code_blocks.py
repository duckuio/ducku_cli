from src.core.documentation import Documentation
from src.core.entity import collect_docs_entities


def test_yaml_code_block_extraction():
    """Test extraction of keys and values from YAML code blocks in markdown."""
    md_content = """
# Configuration Guide

Here's an example configuration:

```yaml
database:
  host: localhost
  port: 5432
  dbname: mydb

features:
  - authentication
  - logging
  - monitoring
```

## API Settings

```yaml
api:
  api_version: v1
  timeout: 30
  endpoints:
    - /users
    - /posts
```
"""
    
    doc = Documentation().from_string(md_content, "markdown")
    entities = collect_docs_entities(doc)
    
    # Find code block entities
    code_block_containers = [c for c in entities if 'code_block_yaml' in c.parent]
    
    # Should have 2 YAML code blocks
    assert len(code_block_containers) >= 2, f"Expected at least 2 YAML code blocks, got {len(code_block_containers)}"
    
    # Collect all entity names from code blocks
    all_names = []
    for container in code_block_containers:
        all_names.extend([e.name for e in container.entities])
    
    # Check for keys from first YAML block
    assert "database" in all_names
    assert "host" in all_names
    assert "port" in all_names
    assert "dbname" in all_names
    assert "features" in all_names
    
    # Check for values from first YAML block
    assert "localhost" in all_names
    assert "5432" in all_names
    assert "mydb" in all_names
    assert "authentication" in all_names
    assert "logging" in all_names
    assert "monitoring" in all_names
    
    # Check for keys from second YAML block
    assert "api" in all_names
    assert "api_version" in all_names
    assert "timeout" in all_names
    assert "endpoints" in all_names
    
    # Check for values from second YAML block
    assert "v1" in all_names
    assert "30" in all_names
    assert "/users" in all_names
    assert "/posts" in all_names


def test_json_code_block_extraction():
    """Test extraction of keys and values from JSON code blocks in markdown."""
    md_content = """
# JSON Example

```json
{
  "app_name": "TestApp",
  "app_version": "1.0.0",
  "dependencies": ["react", "vue"],
  "config": {
    "debug": true,
    "port": 3000
  }
}
```
"""
    
    doc = Documentation().from_string(md_content, "markdown")
    entities = collect_docs_entities(doc)
    
    # Find code block entities
    code_block_containers = [c for c in entities if 'code_block_json' in c.parent]
    
    assert len(code_block_containers) >= 1, f"Expected at least 1 JSON code block, got {len(code_block_containers)}"
    
    # Collect all entity names
    all_names = []
    for container in code_block_containers:
        all_names.extend([e.name for e in container.entities])
    
    # Check for keys
    assert "app_name" in all_names
    assert "app_version" in all_names
    assert "dependencies" in all_names
    assert "config" in all_names
    assert "debug" in all_names
    assert "port" in all_names
    
    # Check for values
    assert "TestApp" in all_names
    assert "1.0.0" in all_names
    assert "react" in all_names
    assert "vue" in all_names
    assert "3000" in all_names


def test_code_block_with_header_context():
    """Test that code blocks include header context in their parent path."""
    md_content = """
# Database

## PostgreSQL

```yaml
postgres:
  port: 5432
```

## MySQL

```yaml
mysql:
  port: 3306
```
"""
    
    doc = Documentation().from_string(md_content, "markdown")
    entities = collect_docs_entities(doc)
    
    # Find code block containers
    code_block_containers = [c for c in entities if 'code_block_yaml' in c.parent]
    
    assert len(code_block_containers) >= 2
    
    # Check that parent paths include header context
    parents = [c.parent for c in code_block_containers]
    
    # Should have header hierarchy in parent path
    postgres_containers = [p for p in parents if '::h2::PostgreSQL::' in p]
    mysql_containers = [p for p in parents if '::h2::MySQL::' in p]
    
    assert len(postgres_containers) >= 1, f"Expected PostgreSQL header in path, got: {parents}"
    assert len(mysql_containers) >= 1, f"Expected MySQL header in path, got: {parents}"


def test_malformed_yaml_ignored():
    """Test that malformed YAML in code blocks doesn't break parsing."""
    md_content = """
# Bad YAML

```yaml
this is not: valid: yaml: syntax
  - broken
    indentation
```

# Good YAML

```yaml
valid:
  yaml: works
```
"""
    
    doc = Documentation().from_string(md_content, "markdown")
    
    # Should not raise an exception
    entities = collect_docs_entities(doc)
    
    # Should have some entities from the valid YAML
    code_block_containers = [c for c in entities if 'code_block_yaml' in c.parent]
    
    # Even if bad YAML is ignored, good YAML should be processed
    all_names = []
    for container in code_block_containers:
        all_names.extend([e.name for e in container.entities])
    
    assert "valid" in all_names
    assert "yaml" in all_names
    assert "works" in all_names
