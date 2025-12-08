"""
Ruby language analyzer using tree-sitter.
"""

from pathlib import Path
from typing import Set
import tree_sitter_ruby as ts_ruby
from tree_sitter import Language, Node

from src.core.code.language import LanguageAnalyzer


class RubyAnalyzer(LanguageAnalyzer):
    """Ruby-specific code analyzer using tree-sitter."""
    
    def _get_language(self) -> Language:
        """Return the tree-sitter Language object for Ruby."""
        return Language(ts_ruby.language())
    
    def collect_entities(self, file_path: Path, entities: list) -> None:
        """
        Collect Ruby code entities (classes, methods, modules, etc.) from a file.
        
        Args:
            file_path: Path to the Ruby source file
            entities: List to append EntitiesContainer objects to
        """
        from src.core.entity import Entity, EntitiesContainer
        
        root_node = self.parse_file(file_path)
        if root_node is None:
            return
        
        str_file_path = str(file_path)
        
        # Collect module-level functions (methods defined at top level)
        module_functions = EntitiesContainer(str_file_path, "module_functions")
        
        # Collect module-level classes and modules
        module_classes = EntitiesContainer(str_file_path, "module_classes")
        
        # Traverse top-level nodes
        for node in root_node.children:
            # Method definitions at top level
            if node.type == "method":
                method_name = self._get_method_name(node)
                if method_name:
                    module_functions.append(Entity(method_name, node))
            
            # Class definitions
            elif node.type == "class":
                class_name = self._get_class_name(node)
                if class_name:
                    module_classes.append(Entity(class_name, node))
                    # Process class methods
                    self._process_class(node, str_file_path, class_name, entities)
            
            # Module definitions
            elif node.type == "module":
                module_name = self._get_module_name(node)
                if module_name:
                    module_classes.append(Entity(module_name, node))
                    # Process module methods
                    self._process_module(node, str_file_path, module_name, entities)
        
        # Add containers if they have entities
        if module_functions.entities:
            entities.append(module_functions)
        if module_classes.entities:
            entities.append(module_classes)
    
    def _get_method_name(self, node: Node) -> str:
        """Extract method name from method node."""
        for child in node.children:
            if child.type == "identifier":
                return child.text.decode("utf8")
        return ""
    
    def _get_class_name(self, node: Node) -> str:
        """Extract class name from class node."""
        for child in node.children:
            if child.type == "constant":
                return child.text.decode("utf8")
        return ""
    
    def _get_module_name(self, node: Node) -> str:
        """Extract module name from module node."""
        for child in node.children:
            if child.type == "constant":
                return child.text.decode("utf8")
        return ""
    
    def _process_class(self, class_node: Node, file_path: str, class_name: str, entities: list) -> None:
        """Extract methods from a class."""
        from src.core.entity import Entity, EntitiesContainer
        
        class_methods = EntitiesContainer(f"{file_path}::{class_name}", "class_methods")
        
        for child in class_node.children:
            if child.type == "body_statement":
                # Body of the class
                for statement in child.children:
                    if statement.type == "method":
                        method_name = self._get_method_name(statement)
                        if method_name:
                            class_methods.append(Entity(method_name, statement))
        
        if class_methods.entities:
            entities.append(class_methods)
    
    def _process_module(self, module_node: Node, file_path: str, module_name: str, entities: list) -> None:
        """Extract methods from a module."""
        from src.core.entity import Entity, EntitiesContainer
        
        module_methods = EntitiesContainer(f"{file_path}::{module_name}", "class_methods")
        
        for child in module_node.children:
            if child.type == "body_statement":
                # Body of the module
                for statement in child.children:
                    if statement.type == "method":
                        method_name = self._get_method_name(statement)
                        if method_name:
                            module_methods.append(Entity(method_name, statement))
        
        if module_methods.entities:
            entities.append(module_methods)
    
    def collect_imports(self, file_path: Path) -> Set[str]:
        """
        Collect all required module names from a Ruby file.
        
        Args:
            file_path: Path to the Ruby source file
            
        Returns:
            Set of module names that are required
        """
        root_node = self.parse_file(file_path)
        if root_node is None:
            return set()
        
        imports = set()
        self._extract_ruby_imports(root_node, imports)
        return imports
    
    def _extract_ruby_imports(self, node: Node, imports: set) -> None:
        """Extract Ruby require statements."""
        if node.type == "call":
            method_node = node.child_by_field_name("method")
            if method_node and method_node.type == "identifier":
                method_name = method_node.text.decode("utf8")
                if method_name in ("require", "require_relative"):
                    args_node = node.child_by_field_name("arguments")
                    if args_node:
                        for child in args_node.children:
                            if child.type == "string":
                                module_str = child.text.decode("utf8").strip('\'"')
                                imports.add(module_str)
        
        # Recurse through children
        for child in node.children:
            self._extract_ruby_imports(child, imports)
