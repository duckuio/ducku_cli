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
        
        # Collect module-level table records
        module_table_records_containers = {}
        
        # Collect table records from module-level assignments
        for node in root_node.children:
            if node.type == "assignment":
                self._extract_table_records_from_assignment(node, module_table_records_containers, str_file_path)
        
        # Traverse top-level nodes
        for node in root_node.children:
            # Method definitions at top level
            if node.type == "method":
                method_name = self._get_method_name(node)
                if method_name:
                    module_functions.append(Entity(method_name, node))
                    # Collect method arguments
                    self._collect_method_arguments(node, str_file_path, method_name, entities)
            
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
        for key_containers in module_table_records_containers.values():
            for container in key_containers.values():
                if container.entities:
                    entities.append(container)
    
    def _get_method_name(self, node: Node) -> str:
        """Extract method name from method node."""
        for child in node.children:
            if child.type == "identifier":
                return child.text.decode("utf8")
        return ""
    
    def _collect_method_arguments(self, method_node: Node, file_path: str, method_name: str, entities: list) -> None:
        """Collect method arguments as entities."""
        from src.core.entity import Entity, EntitiesContainer
        
        arguments_container = EntitiesContainer(f"{file_path}::{method_name}", "function_arguments")
        
        # Find method_parameters node
        for child in method_node.children:
            if child.type == "method_parameters":
                for param in child.children:
                    if param.type == "identifier":
                        arg_name = param.text.decode("utf8")
                        arguments_container.append(Entity(arg_name, param))
                    elif param.type == "optional_parameter":
                        # Default parameters
                        for subparam in param.children:
                            if subparam.type == "identifier":
                                arg_name = subparam.text.decode("utf8")
                                arguments_container.append(Entity(arg_name, subparam))
                                break
        
        if arguments_container.entities:
            entities.append(arguments_container)
    
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
                            # Collect method arguments
                            self._collect_method_arguments(statement, f"{file_path}::{class_name}", method_name, entities)
        
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
                            # Collect method arguments
                            self._collect_method_arguments(statement, f"{file_path}::{module_name}", method_name, entities)
        
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
                if method_name in ("require", "require_relative", "load"):
                    args_node = node.child_by_field_name("arguments")
                    if args_node:
                        for child in args_node.children:
                            if child.type == "string":
                                module_str = child.text.decode("utf8").strip('\'"')
                                # Add original path with slashes
                                imports.add(module_str)
                                # Also add normalized version with dots for matching
                                normalized = module_str.replace('/', '.')
                                imports.add(normalized)
                                # Add just the filename without extension
                                if '/' in module_str:
                                    basename = module_str.split('/')[-1].replace('.rb', '')
                                    imports.add(basename)
        
        # Recurse through children
        for child in node.children:
            self._extract_ruby_imports(child, imports)
    
    def _extract_table_records_from_assignment(self, assignment_node: Node, table_records_containers: dict, parent_path: str) -> None:
        """Extract table-like records from array assignments."""
        from src.core.entity import Entity, EntitiesContainer
        
        var_name = None
        array_node = None
        
        for child in assignment_node.children:
            if child.type in ("constant", "identifier"):
                var_name = child.text.decode("utf8")
            elif child.type == "array":
                array_node = child
        
        if var_name and array_node:
            self._process_table_array_ruby(array_node, var_name, table_records_containers, parent_path)
    
    def _process_table_array_ruby(self, array_node: Node, var_name: str, table_records_containers: dict, parent_path: str) -> None:
        """Process a Ruby array to check if it contains uniform hashes (table-like data)."""
        from src.core.entity import Entity, EntitiesContainer
        
        hashes = []
        for child in array_node.children:
            if child.type == "hash":
                hashes.append(child)
        
        if len(hashes) < 2:
            return
        
        # Extract keys from all hashes
        all_keys_lists = []
        for hash_node in hashes:
            keys = set()
            for hash_child in hash_node.children:
                if hash_child.type == "pair":
                    for pair_child in hash_child.children:
                        if pair_child.type in ("string", "simple_symbol"):
                            key_text = pair_child.text.decode("utf8")
                            if key_text.startswith('"') or key_text.startswith("'"):
                                key_text = key_text[1:-1]
                            elif key_text.startswith(":"):
                                key_text = key_text[1:]
                            keys.add(key_text)
                            break
            all_keys_lists.append(keys)
        
        if not all_keys_lists:
            return
        
        first_keys = all_keys_lists[0]
        if not all(keys == first_keys for keys in all_keys_lists):
            return
        
        if var_name not in table_records_containers:
            table_records_containers[var_name] = {}
        
        for key in first_keys:
            values = []
            for hash_node in hashes:
                for hash_child in hash_node.children:
                    if hash_child.type == "pair":
                        found_key = None
                        value = None
                        for pair_child in hash_child.children:
                            if pair_child.type in ("string", "simple_symbol") and found_key is None:
                                key_text = pair_child.text.decode("utf8")
                                if key_text.startswith('"') or key_text.startswith("'"):
                                    key_text = key_text[1:-1]
                                elif key_text.startswith(":"):
                                    key_text = key_text[1:]
                                found_key = key_text
                            elif pair_child.type == "=>":
                                continue
                            elif found_key == key and pair_child.type == "string":
                                value_text = pair_child.text.decode("utf8")
                                if len(value_text) >= 2 and value_text[0] in ('"', "'"):
                                    value = value_text[1:-1]
                        
                        if found_key == key and value:
                            values.append(value)
                            break
            
            if values:
                if key not in table_records_containers[var_name]:
                    table_records_containers[var_name][key] = EntitiesContainer(
                        f"{parent_path}::{var_name}::{key}",
                        "table_records"
                    )
                
                container = table_records_containers[var_name][key]
                existing_values = [e.content for e in container.entities]
                for value in values:
                    if value not in existing_values:
                        container.append(Entity(value, array_node))
