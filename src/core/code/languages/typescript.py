"""
TypeScript language analyzer using tree-sitter.
"""

from pathlib import Path
from typing import Set
import tree_sitter_typescript as ts_ts
from tree_sitter import Language, Node

from src.core.code.language import LanguageAnalyzer


class TypeScriptAnalyzer(LanguageAnalyzer):
    """TypeScript-specific code analyzer using tree-sitter."""
    
    def __init__(self, use_tsx: bool = False):
        """
        Initialize TypeScript analyzer.
        
        Args:
            use_tsx: If True, use TSX parser (for .tsx files), otherwise TypeScript
        """
        self.use_tsx = use_tsx
        super().__init__()
    
    def _get_language(self) -> Language:
        """Return the tree-sitter Language object for TypeScript or TSX."""
        if self.use_tsx:
            return Language(ts_ts.language_tsx())
        return Language(ts_ts.language_typescript())
    
    def collect_entities(self, file_path: Path, entities: list) -> None:
        """
        Collect TypeScript code entities (functions, classes, etc.) from a file.
        
        Args:
            file_path: Path to the TypeScript source file
            entities: List to append EntitiesContainer objects to
        """
        from src.core.entity import Entity, EntitiesContainer
        
        root_node = self.parse_file(file_path)
        if root_node is None:
            return
        
        str_file_path = str(file_path)
        
        # Collect module-level functions
        module_functions = EntitiesContainer(str_file_path, "module_functions")
        
        # Collect module-level classes
        module_classes = EntitiesContainer(str_file_path, "module_classes")
        
        # Collect module-level table records
        module_table_records_containers = {}
        
        # Traverse top-level nodes
        for node in root_node.children:
            # Function declarations
            if node.type == "function_declaration":
                func_name = self._get_function_name(node)
                if func_name:
                    module_functions.append(Entity(func_name, node))
                    # Collect function arguments
                    self._collect_function_arguments(node, str_file_path, func_name, entities)
            
            # Arrow functions / const assignments
            elif node.type in ("lexical_declaration", "variable_declaration"):
                self._extract_arrow_functions(node, module_functions)
                self._extract_table_records_from_declaration(node, module_table_records_containers, str_file_path)
            
            # Class declarations
            elif node.type == "class_declaration":
                class_name = self._get_class_name(node)
                if class_name:
                    module_classes.append(Entity(class_name, node))
                    # Extract methods from the class
                    self._process_class(node, str_file_path, class_name, entities)
            
            # Export statements
            elif node.type == "export_statement":
                self._process_export(node, module_functions, module_classes, str_file_path, entities)
        
        # Add containers if they have entities
        if module_functions.entities:
            entities.append(module_functions)
        if module_classes.entities:
            entities.append(module_classes)
        for key_containers in module_table_records_containers.values():
            for container in key_containers.values():
                if container.entities:
                    entities.append(container)
    
    def _get_function_name(self, node: Node) -> str:
        """Extract function name from function_declaration."""
        for child in node.children:
            if child.type == "identifier":
                return child.text.decode("utf8")
        return ""
    
    def _get_class_name(self, node: Node) -> str:
        """Extract class name from class_declaration."""
        for child in node.children:
            if child.type == "type_identifier" or child.type == "identifier":
                return child.text.decode("utf8")
        return ""
    
    def _collect_function_arguments(self, func_node: Node, file_path: str, func_name: str, entities: list) -> None:
        """Collect function/method arguments as entities."""
        from src.core.entity import Entity, EntitiesContainer
        
        arguments_container = EntitiesContainer(f"{file_path}::{func_name}", "function_arguments")
        
        # Find formal_parameters or required_parameters node
        for child in func_node.children:
            if child.type in ("formal_parameters", "required_parameters"):
                for param in child.children:
                    if param.type == "identifier":
                        arg_name = param.text.decode("utf8")
                        arguments_container.append(Entity(arg_name, param))
                    elif param.type == "required_parameter":
                        # Typed parameters
                        for subparam in param.children:
                            if subparam.type == "identifier":
                                arg_name = subparam.text.decode("utf8")
                                arguments_container.append(Entity(arg_name, subparam))
                                break
                    elif param.type == "optional_parameter":
                        # Default parameters
                        for subparam in param.children:
                            if subparam.type == "identifier":
                                arg_name = subparam.text.decode("utf8")
                                arguments_container.append(Entity(arg_name, subparam))
                                break
        
        if arguments_container.entities:
            entities.append(arguments_container)
    
    def _extract_arrow_functions(self, declaration: Node, functions_container) -> None:
        """Extract arrow functions from lexical/variable declarations."""
        from src.core.entity import Entity
        
        for child in declaration.children:
            if child.type == "variable_declarator":
                func_name = None
                is_arrow = False
                
                for declarator_child in child.children:
                    if declarator_child.type == "identifier":
                        func_name = declarator_child.text.decode("utf8")
                    elif declarator_child.type in ("arrow_function", "function"):
                        is_arrow = True
                
                if func_name and is_arrow:
                    functions_container.append(Entity(func_name, child))
    
    def _process_class(self, class_node: Node, file_path: str, class_name: str, entities: list) -> None:
        """Extract methods from a class."""
        from src.core.entity import Entity, EntitiesContainer
        
        class_methods = EntitiesContainer(f"{file_path}::{class_name}", "class_methods")
        
        for child in class_node.children:
            if child.type == "class_body":
                for body_child in child.children:
                    if body_child.type in ("method_definition", "public_field_definition"):
                        method_name = self._get_method_name(body_child)
                        if method_name:
                            class_methods.append(Entity(method_name, body_child))
                            # Collect method arguments
                            self._collect_function_arguments(body_child, f"{file_path}::{class_name}", method_name, entities)
        
        if class_methods.entities:
            entities.append(class_methods)
    
    def _get_method_name(self, node: Node) -> str:
        """Extract method name from method_definition or field_definition."""
        for child in node.children:
            if child.type == "property_identifier":
                return child.text.decode("utf8")
        return ""
    
    def _process_export(self, export_node: Node, functions_container, classes_container, 
                       file_path: str, entities: list) -> None:
        """Process export statements."""
        from src.core.entity import Entity
        
        for child in export_node.children:
            # export function foo() {}
            if child.type == "function_declaration":
                func_name = self._get_function_name(child)
                if func_name:
                    functions_container.append(Entity(func_name, child))
            
            # export const foo = () => {}
            elif child.type in ("lexical_declaration", "variable_declaration"):
                self._extract_arrow_functions(child, functions_container)
            
            # export class Foo {}
            elif child.type == "class_declaration":
                class_name = self._get_class_name(child)
                if class_name:
                    classes_container.append(Entity(class_name, child))
                    self._process_class(child, file_path, class_name, entities)
    
    def collect_imports(self, file_path: Path) -> Set[str]:
        """
        Collect all imported module names from a TypeScript file.
        
        Args:
            file_path: Path to the TypeScript source file
            
        Returns:
            Set of module names that are imported
        """
        root_node = self.parse_file(file_path)
        if root_node is None:
            return set()
        
        imports = set()
        self._extract_ts_imports(root_node, imports)
        return imports
    
    def _extract_ts_imports(self, node: Node, imports: set) -> None:
        """Extract TypeScript import statements (same as JavaScript)."""
        if node.type == "import_statement":
            # import ... from 'foo'
            for child in node.children:
                if child.type == "string":
                    # Remove quotes and get module name
                    module_str = child.text.decode("utf8").strip('\'"')
                    # Skip relative imports
                    if not module_str.startswith('.') and not module_str.startswith('/'):
                        imports.add(module_str)
        
        elif node.type == "call_expression":
            # require('foo') or import('foo')
            func_node = node.child_by_field_name("function")
            if func_node and func_node.type == "identifier":
                func_name = func_node.text.decode("utf8")
                if func_name in ("require", "import"):
                    args_node = node.child_by_field_name("arguments")
                    if args_node:
                        for child in args_node.children:
                            if child.type == "string":
                                module_str = child.text.decode("utf8").strip('\'"')
                                if not module_str.startswith('.') and not module_str.startswith('/'):
                                    imports.add(module_str)
        
        # Recurse through children
        for child in node.children:
            self._extract_ts_imports(child, imports)
    
    def _extract_table_records_from_declaration(self, declaration: Node, table_records_containers: dict, parent_path: str) -> None:
        """Extract table-like records from const/let/var declarations."""
        from src.core.entity import Entity, EntitiesContainer
        
        for child in declaration.children:
            if child.type == "variable_declarator":
                var_name = None
                array_node = None
                
                for declarator_child in child.children:
                    if declarator_child.type == "identifier":
                        var_name = declarator_child.text.decode("utf8")
                    elif declarator_child.type == "array":
                        array_node = declarator_child
                
                if var_name and array_node:
                    self._process_table_array(array_node, var_name, table_records_containers, parent_path)
    
    def _process_table_array(self, array_node: Node, var_name: str, table_records_containers: dict, parent_path: str) -> None:
        """Process an array to check if it contains uniform objects (table-like data)."""
        from src.core.entity import Entity, EntitiesContainer
        
        objects = []
        for child in array_node.children:
            if child.type == "object":
                objects.append(child)
        
        if len(objects) < 2:
            return
        
        # Extract keys from all objects
        all_keys_lists = []
        for obj_node in objects:
            keys = set()
            for obj_child in obj_node.children:
                if obj_child.type == "pair":
                    for pair_child in obj_child.children:
                        if pair_child.type in ("property_identifier", "string"):
                            key_text = pair_child.text.decode("utf8")
                            if key_text.startswith('"') or key_text.startswith("'"):
                                key_text = key_text[1:-1]
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
            for obj_node in objects:
                for obj_child in obj_node.children:
                    if obj_child.type == "pair":
                        found_key = None
                        value = None
                        for pair_child in obj_child.children:
                            if pair_child.type in ("property_identifier", "string") and found_key is None:
                                key_text = pair_child.text.decode("utf8")
                                if key_text.startswith('"') or key_text.startswith("'"):
                                    key_text = key_text[1:-1]
                                found_key = key_text
                            elif pair_child.type == ":":
                                continue
                            elif found_key == key and pair_child.type == "string":
                                value_text = pair_child.text.decode("utf8")
                                if len(value_text) >= 2 and value_text[0] in ('"', "'", "`"):
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
