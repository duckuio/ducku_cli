"""
Go language analyzer using tree-sitter.
"""

from pathlib import Path
from typing import Set
import tree_sitter_go as ts_go
from tree_sitter import Language, Node

from src.core.code.language import LanguageAnalyzer


class GoAnalyzer(LanguageAnalyzer):
    """Go-specific code analyzer using tree-sitter."""
    
    def _get_language(self) -> Language:
        """Return the tree-sitter Language object for Go."""
        return Language(ts_go.language())
    
    def collect_entities(self, file_path: Path, entities: list) -> None:
        """
        Collect Go code entities (functions, structs, etc.) from a file.
        
        Args:
            file_path: Path to the Go source file
            entities: List to append EntitiesContainer objects to
        """
        from src.core.entity import Entity, EntitiesContainer
        
        root_node = self.parse_file(file_path)
        if root_node is None:
            return
        
        str_file_path = str(file_path)
        
        # Collect module-level functions
        module_functions = EntitiesContainer(str_file_path, "module_functions")
        
        # Collect module-level types (structs, interfaces)
        module_classes = EntitiesContainer(str_file_path, "module_classes")
        
        # Traverse top-level nodes
        for node in root_node.children:
            # Function declarations
            if node.type == "function_declaration":
                func_name = self._get_function_name(node)
                if func_name:
                    module_functions.append(Entity(func_name, node))
            
            # Method declarations
            elif node.type == "method_declaration":
                method_name = self._get_method_name(node)
                receiver = self._get_method_receiver(node)
                if method_name and receiver:
                    # Add method to appropriate receiver
                    self._add_method_to_receiver(receiver, method_name, node, str_file_path, entities)
            
            # Type declarations (struct, interface, etc.)
            elif node.type == "type_declaration":
                self._process_type_declaration(node, module_classes)
        
        # Add containers if they have entities
        if module_functions.entities:
            entities.append(module_functions)
        if module_classes.entities:
            entities.append(module_classes)
    
    def _get_function_name(self, node: Node) -> str:
        """Extract function name from function_declaration."""
        for child in node.children:
            if child.type == "identifier":
                return child.text.decode("utf8")
        return ""
    
    def _get_method_name(self, node: Node) -> str:
        """Extract method name from method_declaration."""
        for child in node.children:
            if child.type == "field_identifier":
                return child.text.decode("utf8")
        return ""
    
    def _get_method_receiver(self, node: Node) -> str:
        """Extract receiver type from method_declaration."""
        for child in node.children:
            if child.type == "parameter_list":
                # This is the receiver
                for param_child in child.children:
                    if param_child.type == "parameter_declaration":
                        for type_child in param_child.children:
                            if type_child.type == "type_identifier":
                                return type_child.text.decode("utf8")
                            elif type_child.type == "pointer_type":
                                # *TypeName
                                for ptr_child in type_child.children:
                                    if ptr_child.type == "type_identifier":
                                        return ptr_child.text.decode("utf8")
                return ""
        return ""
    
    def _add_method_to_receiver(self, receiver: str, method_name: str, node: Node, 
                                file_path: str, entities: list) -> None:
        """Add a method to its receiver type's method container."""
        from src.core.entity import Entity, EntitiesContainer
        
        # Find or create container for this receiver
        container_parent = f"{file_path}::{receiver}"
        method_container = None
        
        for e in entities:
            if e.type == "class_methods" and e.parent == container_parent:
                method_container = e
                break
        
        if method_container is None:
            method_container = EntitiesContainer(container_parent, "class_methods")
            entities.append(method_container)
        
        method_container.append(Entity(method_name, node))
    
    def _process_type_declaration(self, node: Node, classes_container) -> None:
        """Process type declarations (struct, interface, etc.)."""
        from src.core.entity import Entity
        
        for child in node.children:
            if child.type == "type_spec":
                type_name = None
                for spec_child in child.children:
                    if spec_child.type == "type_identifier":
                        type_name = spec_child.text.decode("utf8")
                        break
                
                if type_name:
                    classes_container.append(Entity(type_name, child))
    
    def collect_imports(self, file_path: Path) -> Set[str]:
        """
        Collect all imported package names from a Go file.
        
        Args:
            file_path: Path to the Go source file
            
        Returns:
            Set of package names that are imported
        """
        root_node = self.parse_file(file_path)
        if root_node is None:
            return set()
        
        imports = set()
        self._extract_go_imports(root_node, imports)
        return imports
    
    def _extract_go_imports(self, node: Node, imports: set) -> None:
        """Extract Go import statements."""
        if node.type == "import_declaration":
            for child in node.children:
                if child.type == "import_spec":
                    for subchild in child.children:
                        if subchild.type == "interpreted_string_literal":
                            module_str = subchild.text.decode("utf8").strip('\'"')
                            imports.add(module_str)
                elif child.type == "import_spec_list":
                    for spec in child.children:
                        if spec.type == "import_spec":
                            for subchild in spec.children:
                                if subchild.type == "interpreted_string_literal":
                                    module_str = subchild.text.decode("utf8").strip('\'"')
                                    imports.add(module_str)
        
        # Recurse through children
        for child in node.children:
            self._extract_go_imports(child, imports)
