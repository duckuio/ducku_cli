"""
Abstract base class for language-specific code analysis.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Set
from tree_sitter import Language, Parser, Node


class LanguageAnalyzer(ABC):
    """
    Abstract base class for language-specific code analysis.
    Each language implementation provides its own tree-sitter parsing logic.
    """
    
    def __init__(self):
        self.language: Language = self._get_language()
        self.parser: Parser = Parser(self.language)
    
    @abstractmethod
    def _get_language(self) -> Language:
        """Return the tree-sitter Language object for this language."""
        pass
    
    @abstractmethod
    def collect_entities(self, file_path: Path, entities: list) -> None:
        """
        Collect code entities (functions, classes, properties, etc.) from a file.
        
        Args:
            file_path: Path to the source file
            entities: List to append EntitiesContainer objects to
        """
        pass
    
    @abstractmethod
    def collect_imports(self, file_path: Path) -> Set[str]:
        """
        Collect all imported module names from a file.
        
        Args:
            file_path: Path to the source file
            
        Returns:
            Set of module names that are imported
        """
        pass
    
    def parse_file(self, file_path: Path) -> Node:
        """
        Parse a file and return the root AST node.
        
        Args:
            file_path: Path to the source file
            
        Returns:
            Root node of the parsed tree
        """
        try:
            content = file_path.read_text(encoding="utf8", errors="ignore")
        except (OSError, UnicodeDecodeError):
            return None
        
        tree = self.parser.parse(bytes(content, "utf8"))
        return tree.root_node
