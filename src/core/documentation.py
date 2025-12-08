from abc import ABC, abstractmethod
from anytree import Node
from markdown_it import MarkdownIt
from pathlib import Path
from src.helpers.json import collect_key_values, IgnoreUnknownTagsLoader
import yaml
import json
from src.helpers.file_system import FileSystemFolder

SUPPORTED_FORMATS = [".md", ".markdown", "markdown"]

def _inline_text(inline_token):
    parts = []
    for ch in getattr(inline_token, "children", []) or []:
        t = getattr(ch, "type", None)
        if t == "text":
            parts.append(ch.content)
        elif t == "code_inline":
            parts.append(f"`{ch.content}`")
        elif t in ("softbreak", "hardbreak"):
            parts.append("\n")
        elif hasattr(ch, "children"):
            parts.append(_inline_text(ch))
    return "".join(parts)

def _collect_headings(tokens):
    out = []
    for i, t in enumerate(tokens):
        if t.type == "heading_open" and i + 1 < len(tokens) and tokens[i + 1].type == "inline":
            level = int(t.tag[1])
            text = _inline_text(tokens[i + 1]).strip()
            out.append((level, text))
    return out

def _build_headers_tree(headings, parent, i=0, base_level=0):
    while i < len(headings) and headings[i][0] > base_level:
        level, text = headings[i]
        node = Node(text, parent=parent, kind="h"+str(level), level=level)
        i = _build_headers_tree(headings, node, i + 1, base_level=level)
    return i

def _parse_list(tokens, i, parent):
    open_tok = tokens[i]
    list_kind = "ordered_list" if open_tok.type == "ordered_list_open" else "__bullet_list"
    close_t = "ordered_list_close" if list_kind == "ordered_list" else "bullet_list_close"
    list_node = Node(list_kind, parent=parent, kind=list_kind)
    i += 1
    while i < len(tokens) and tokens[i].type != close_t:
        if tokens[i].type == "list_item_open":
            item_node = Node("", parent=list_node, kind="list_item")
            i += 1
            while i < len(tokens) and tokens[i].type != "list_item_close":
                t = tokens[i]
                if t.type == "inline":
                    txt = _inline_text(t).strip()
                    if txt:
                        item_node.name = f"{item_node.name}\n{txt}" if item_node.name else txt
                elif t.type in ("bullet_list_open", "ordered_list_open"):
                    i = _parse_list(tokens, i, item_node)
                i += 1
        i += 1
    return i


def _parse_code_block(code_content: str, language: str, parent_path: str, parallel_entities):
    """Parse code blocks and extract structured data like YAML/JSON."""
    if language in ("yaml", "yml"):
        try:
            data = yaml.load(code_content, Loader=IgnoreUnknownTagsLoader)
            if data:
                collect_key_values(data, parallel_entities, parent_path + "::code_block_yaml")
        except (yaml.YAMLError, ValueError, TypeError):
            pass  # Ignore malformed YAML in code blocks
    elif language == "json":
        try:
            data = json.loads(code_content)
            if data:
                collect_key_values(data, parallel_entities, parent_path + "::code_block_json")
        except (json.JSONDecodeError, ValueError, TypeError):
            pass  # Ignore malformed JSON in code blocks

class Source:
    def __init__(self, doc_type: str, doc_format: str, metadata: dict | None = None):
        self.type = doc_type  # "string" or "file"
        self.doc_format = doc_format  # "markdown", ".py", etc.
        self.metadata = metadata or {}
    
    def get_root(self) -> Path | None:
        """Get the root path for this source, if applicable."""
        if self.type == "file" and "path" in self.metadata:
            return Path(self.metadata["path"]).parent
        return None

    def get_source_identifier(self) -> str:
        """Get a string identifier for this source."""
        if self.type == "file":
            return self.metadata.get("path", f"{self.doc_format}(file)")
        elif self.type == "string":
            return f"{self.doc_format}(string)"
        else:
            return f"{self.doc_format}({self.type})"

class DocPart(ABC):
    def __init__(self, source: Source):
        self.doc_format = source.doc_format
        self.source = source
        self.headers = Node("headers_root", kind="headers_root")
        self.lists = Node("lists_root", kind="lists_root")
        self.code_blocks = []  # List of dicts with language, content, parent_path

    @abstractmethod
    def read(self) -> str:
        ...

    def parse(self):
        if self.doc_format in SUPPORTED_FORMATS:
            return self._parse_md()
        return []

    def _parse_md(self):
        md = MarkdownIt()
        tokens = md.parse(self.read())
        headings = _collect_headings(tokens)
        _build_headers_tree(headings, self.headers)
        
        # Build a map of token positions to their header context
        current_header_path = []
        i = 0
        
        while i < len(tokens):
            t = tokens[i]
            
            # Track current header context
            if t.type == "heading_open":
                level = int(t.tag[1])
                if i + 1 < len(tokens) and tokens[i + 1].type == "inline":
                    header_text = _inline_text(tokens[i + 1]).strip()
                    
                    # Remove headers of same or higher level (lower number)
                    current_header_path = [h for h in current_header_path if h[0] < level]
                    current_header_path.append((level, header_text))
            
            # Parse code blocks
            elif t.type == "fence":
                # Extract language and content
                language = t.info.strip() if t.info else ""
                code_content = t.content
                
                # Build parent path from current header context
                parent_path = self.source.get_source_identifier()
                for level, header_text in current_header_path:
                    parent_path += f"::h{level}::{header_text}"
                
                # Store code block for later processing
                self.code_blocks.append({
                    'language': language,
                    'content': code_content,
                    'parent_path': parent_path
                })
            
            # Parse lists with header context
            elif t.type in ("bullet_list_open", "ordered_list_open"):
                # Create a parent node with header context if we have headers
                if current_header_path:
                    # Build a node path with header hierarchy
                    list_parent = self.lists
                    for level, header_text in current_header_path:
                        # Find or create header node in lists tree
                        header_node = None
                        for child in list_parent.children:
                            if child.kind == f"h{level}" and child.name == header_text:
                                header_node = child
                                break
                        if not header_node:
                            header_node = Node(header_text, parent=list_parent, kind=f"h{level}")
                        list_parent = header_node
                    
                    i = _parse_list(tokens, i, list_parent)
                else:
                    i = _parse_list(tokens, i, self.lists)
            i += 1
        return tokens

class DocString(DocPart):
    def __init__(self, content: str, doc_format: str = "markdown"):
        source = Source("string", doc_format, {"content_preview": content[:50] + "..." if len(content) > 50 else content})
        super().__init__(source)
        self._content = content

    def read(self) -> str:
        return self._content

    def __str__(self) -> str:
        return self._content

class DocFile(DocPart):
    def __init__(self, path: Path):
        doc_format = path.suffix.lower()
        metadata = {
            "path": str(path),
            "file_size": path.stat().st_size if path.exists() else 0, 
            "file_name": path.name
        }
        source = Source("file", doc_format, metadata)
        super().__init__(source)
        self.path = path
        self._content = ""

    def read(self) -> str:
        if not self._content:
            try:
                self._content = self.path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                # Try with errors='replace' if UTF-8 decoding fails
                self._content = self.path.read_text(encoding="utf-8", errors="replace")
        return self._content

    def __str__(self) -> str:
        return self.read()

class Documentation:
    def __init__(self, paths_to_ignore: list[Path] | None = None):
        self.doc_parts: list[DocPart] = []
        self.docs_separator = "\n\n"
        self._content: str | None = None
        self.paths_to_ignore = paths_to_ignore or []

    @property
    def content(self) -> str:
        if self._content is not None:
            return self._content
        return self.docs_separator.join(str(part) for part in self.doc_parts)

    def add_part(self, part: DocPart):
        self.doc_parts.append(part)

    def process_folder(self, full_path: Path):
        """Process all files in a folder recursively."""
        fs_folder = FileSystemFolder(full_path, self.paths_to_ignore)
        all_files = fs_folder.get_all_files()
        for file in all_files:
            self.process_file(file)

    def process_file(self, file: Path):
        if file.suffix.lower() in SUPPORTED_FORMATS and file.resolve() not in self.paths_to_ignore:
            self.doc_parts.append(DocFile(file))

    def process_content(self):
        for part in self.doc_parts:
            part.parse()
        return self

    def from_project(self, project):
        for path in project.doc_paths:
            if path.is_file():
                self.process_file(path)
            elif path.is_dir():
                self.process_folder(path)
        self.process_content()
        return self

    def from_string(self, content: str, doc_type: str = "markdown"):
        self.doc_parts = [DocString(content, doc_type)]
        self.process_content()
        return self
