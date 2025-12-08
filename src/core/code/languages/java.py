"""
Java language analyzer using tree-sitter.
"""

from pathlib import Path
from typing import Set
import tree_sitter_java as ts_java
from tree_sitter import Language, Node

from src.core.code.language import LanguageAnalyzer


class JavaAnalyzer(LanguageAnalyzer):
    """Java-specific code analyzer using tree-sitter."""
    
    def _get_language(self) -> Language:
        """Return the tree-sitter Language object for Java."""
        return Language(ts_java.language())
    
    def collect_entities(self, file_path: Path, entities: list) -> None:
        """
        Collect Java code entities (classes, methods, etc.) from a file.
        
        Args:
            file_path: Path to the Java source file
            entities: List to append EntitiesContainer objects to
        """
        from src.core.entity import Entity, EntitiesContainer
        
        root_node = self.parse_file(file_path)
        if root_node is None:
            return
        
        str_file_path = str(file_path)
        
        # Collect module-level classes
        module_classes = EntitiesContainer(str_file_path, "module_classes")
        
        # Traverse top-level nodes
        for node in root_node.children:
            # Class declarations
            if node.type == "class_declaration":
                class_name = self._get_class_name(node)
                if class_name:
                    module_classes.append(Entity(class_name, node))
                    # Extract methods from the class
                    self._process_class(node, str_file_path, class_name, entities)
            
            # Interface declarations
            elif node.type == "interface_declaration":
                interface_name = self._get_interface_name(node)
                if interface_name:
                    module_classes.append(Entity(interface_name, node))
                    self._process_interface(node, str_file_path, interface_name, entities)
            
            # Enum declarations
            elif node.type == "enum_declaration":
                enum_name = self._get_enum_name(node)
                if enum_name:
                    module_classes.append(Entity(enum_name, node))
        
        # Add containers if they have entities
        if module_classes.entities:
            entities.append(module_classes)
    
    def _get_class_name(self, node: Node) -> str:
        """Extract class name from class_declaration."""
        for child in node.children:
            if child.type == "identifier":
                return child.text.decode("utf8")
        return ""
    
    def _get_interface_name(self, node: Node) -> str:
        """Extract interface name from interface_declaration."""
        for child in node.children:
            if child.type == "identifier":
                return child.text.decode("utf8")
        return ""
    
    def _get_enum_name(self, node: Node) -> str:
        """Extract enum name from enum_declaration."""
        for child in node.children:
            if child.type == "identifier":
                return child.text.decode("utf8")
        return ""
    
    def _process_class(self, class_node: Node, file_path: str, class_name: str, entities: list) -> None:
        """Extract methods from a class."""
        from src.core.entity import Entity, EntitiesContainer
        
        class_methods = EntitiesContainer(f"{file_path}::{class_name}", "class_methods")
        
        for child in class_node.children:
            if child.type == "class_body":
                for body_child in child.children:
                    if body_child.type == "method_declaration":
                        method_name = self._get_method_name(body_child)
                        if method_name:
                            class_methods.append(Entity(method_name, body_child))
        
        if class_methods.entities:
            entities.append(class_methods)
    
    def _process_interface(self, interface_node: Node, file_path: str, interface_name: str, entities: list) -> None:
        """Extract methods from an interface."""
        from src.core.entity import Entity, EntitiesContainer
        
        interface_methods = EntitiesContainer(f"{file_path}::{interface_name}", "class_methods")
        
        for child in interface_node.children:
            if child.type == "interface_body":
                for body_child in child.children:
                    if body_child.type == "method_declaration":
                        method_name = self._get_method_name(body_child)
                        if method_name:
                            interface_methods.append(Entity(method_name, body_child))
        
        if interface_methods.entities:
            entities.append(interface_methods)
    
    def _get_method_name(self, node: Node) -> str:
        """Extract method name from method_declaration."""
        for child in node.children:
            if child.type == "identifier":
                return child.text.decode("utf8")
        return ""
    
    def collect_imports(self, file_path: Path) -> Set[str]:
        """
        Collect all imported module names from a Java file.
        
        Args:
            file_path: Path to the Java source file
            
        Returns:
            Set of package/class names that are imported
        """
        root_node = self.parse_file(file_path)
        if root_node is None:
            return set()
        
        imports = set()
        self._extract_java_imports(root_node, imports)
        return imports
    
    def _extract_java_imports(self, node: Node, imports: set) -> None:
        """Extract Java import statements."""
        if node.type == "import_declaration":
            for child in node.children:
                if child.type == "scoped_identifier" or child.type == "identifier":
                    module_name = child.text.decode("utf8")
                    imports.add(module_name)
        
        # Recurse through children
        for child in node.children:
            self._extract_java_imports(child, imports)
