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
