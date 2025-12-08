"""
Python language analyzer using tree-sitter.
"""

from pathlib import Path
from typing import Set
import tree_sitter_python as ts_python
from tree_sitter import Language, Node

from src.core.code.language import LanguageAnalyzer
from src.core.entity import Entity, EntitiesContainer


class PythonAnalyzer(LanguageAnalyzer):
    """Python-specific code analyzer using tree-sitter."""
    
    def _get_language(self) -> Language:
        """Return the tree-sitter Language object for Python."""
        return Language(ts_python.language())
    
    def collect_entities(self, file_path: Path, entities: list) -> None:
        """
        Collect Python code entities (functions, classes, properties, etc.) from a file.
        
        Args:
            file_path: Path to the Python source file
            entities: List to append EntitiesContainer objects to
        """
        root_node = self.parse_file(file_path)
        if root_node is None:
            return
        
        str_file_path = str(file_path)
        
        # Collect module-level functions
        module_functions = EntitiesContainer(str_file_path, "module_functions")
        
        # Collect module-level classes
        module_classes = EntitiesContainer(str_file_path, "module_classes")
        
        # Collect module-level dictionary keys, values, and list elements (per variable)
        module_dict_keys_containers = {}
        module_dict_values_containers = {}
        module_list_elements_containers = {}
        
        for child in root_node.children:
            # Function definitions at module level
            if child.type == "function_definition":
                func_name = self._get_function_name(child)
                if func_name:
                    module_functions.append(Entity(func_name, child))
                    # Collect function arguments
                    self._collect_function_arguments(child, str_file_path, func_name, entities)
            
            # Class definitions at module level (including decorated classes)
            elif child.type == "class_definition":
                class_name = self._get_class_name(child)
                if class_name:
                    module_classes.append(Entity(class_name, child))
                    # Process class body
                    self._process_class(child, str_file_path, class_name, entities)
            
            # Decorated definitions (could be decorated classes like @dataclass)
            elif child.type == "decorated_definition":
                # Find class_definition inside decorator
                for decorator_child in child.children:
                    if decorator_child.type == "class_definition":
                        class_name = self._get_class_name(decorator_child)
                        if class_name:
                            module_classes.append(Entity(class_name, decorator_child))
                            # Process class body
                            self._process_class(decorator_child, str_file_path, class_name, entities)
                        break
            
            # Assignment statements (potential dictionaries or lists)
            elif child.type == "expression_statement":
                self._extract_dict_keys_from_statement(child, module_dict_keys_containers, str_file_path)
                self._extract_dict_values_from_statement(child, module_dict_values_containers, str_file_path)
                self._extract_list_elements_from_statement(child, module_list_elements_containers, str_file_path)
        
        # Add containers if they have entities
        if module_functions.entities:
            entities.append(module_functions)
        if module_classes.entities:
            entities.append(module_classes)
        for container in module_dict_keys_containers.values():
            if container.entities:
                entities.append(container)
        for container in module_dict_values_containers.values():
            if container.entities:
                entities.append(container)
        for container in module_list_elements_containers.values():
            if container.entities:
                entities.append(container)
    
    def collect_imports(self, file_path: Path) -> Set[str]:
        """
        Collect all imported module names from a Python file.
        
        Args:
            file_path: Path to the Python source file
            
        Returns:
            Set of module names that are imported
        """
        root_node = self.parse_file(file_path)
        if root_node is None:
            return set()
        
        imports = set()
        self._extract_python_imports(root_node, imports)
        return imports
    
    def _get_function_name(self, node: Node) -> str:
        """Extract function name from function_definition node."""
        for child in node.children:
            if child.type == "identifier":
                return child.text.decode("utf8")
        return ""
    
    def _get_class_name(self, node: Node) -> str:
        """Extract class name from class_definition node."""
        for child in node.children:
            if child.type == "identifier":
                return child.text.decode("utf8")
        return ""
    
    def _collect_function_arguments(self, func_node: Node, file_path: str, func_name: str, entities: list) -> None:
        """Collect function/method arguments as entities."""
        arguments_container = EntitiesContainer(f"{file_path}::{func_name}", "function_arguments")
        
        # Find parameters node
        for child in func_node.children:
            if child.type == "parameters":
                for param in child.children:
                    if param.type == "identifier":
                        arg_name = param.text.decode("utf8")
                        if arg_name not in ("self", "cls"):  # Skip self/cls
                            arguments_container.append(Entity(arg_name, param))
                    elif param.type in ("typed_parameter", "default_parameter", "typed_default_parameter"):
                        # Extract identifier from typed, default, or typed_default parameters
                        for subparam in param.children:
                            if subparam.type == "identifier":
                                arg_name = subparam.text.decode("utf8")
                                if arg_name not in ("self", "cls"):
                                    arguments_container.append(Entity(arg_name, subparam))
                                break
        
        if arguments_container.entities:
            entities.append(arguments_container)
    
    def _process_class(self, class_node: Node, file_path: str, class_name: str, entities: list) -> None:
        """Process a class definition to extract methods and properties."""
        class_methods = EntitiesContainer(f"{file_path}::{class_name}", "class_methods")
        class_properties = EntitiesContainer(f"{file_path}::{class_name}", "class_properties")
        class_dict_keys_containers = {}
        class_dict_values_containers = {}
        class_list_elements_containers = {}
        
        # Find class body
        for child in class_node.children:
            if child.type == "block":
                for statement in child.children:
                    # Handle direct function definitions or decorated definitions
                    func_node = None
                    if statement.type == "function_definition":
                        func_node = statement
                    elif statement.type == "decorated_definition":
                        # Find function_definition inside decorator
                        for decorator_child in statement.children:
                            if decorator_child.type == "function_definition":
                                func_node = decorator_child
                                break
                    
                    if func_node:
                        method_name = self._get_function_name(func_node)
                        if method_name:
                            class_methods.append(Entity(method_name, func_node))
                            # Collect method arguments
                            self._collect_function_arguments(func_node, f"{file_path}::{class_name}", method_name, entities)
                            # Extract properties from method body (like self.x = y)
                            self._extract_properties_from_node(func_node, class_properties)
                            # Extract dictionary keys, values, and list elements from method body
                            method_dict_keys_containers = {}
                            method_dict_values_containers = {}
                            method_list_elements_containers = {}
                            self._extract_dict_keys_from_node(func_node, method_dict_keys_containers, f"{file_path}::{class_name}::{method_name}")
                            self._extract_dict_values_from_node(func_node, method_dict_values_containers, f"{file_path}::{class_name}::{method_name}")
                            self._extract_list_elements_from_node(func_node, method_list_elements_containers, f"{file_path}::{class_name}::{method_name}")
                            for container in method_dict_keys_containers.values():
                                if container.entities:
                                    entities.append(container)
                            for container in method_dict_values_containers.values():
                                if container.entities:
                                    entities.append(container)
                            for container in method_list_elements_containers.values():
                                if container.entities:
                                    entities.append(container)
                    
                    # Handle class-level assignments (potential dictionaries or lists)
                    elif statement.type == "expression_statement":
                        # Extract field names from type-annotated assignments (for dataclasses)
                        self._extract_annotated_field_names(statement, class_properties)
                        
                        self._extract_dict_keys_from_statement(statement, class_dict_keys_containers, f"{file_path}::{class_name}")
                        self._extract_dict_values_from_statement(statement, class_dict_values_containers, f"{file_path}::{class_name}")
                        self._extract_list_elements_from_statement(statement, class_list_elements_containers, f"{file_path}::{class_name}")
        
        # Add containers if they have entities
        if class_methods.entities:
            entities.append(class_methods)
        if class_properties.entities:
            entities.append(class_properties)
        for container in class_dict_keys_containers.values():
            if container.entities:
                entities.append(container)
        for container in class_dict_values_containers.values():
            if container.entities:
                entities.append(container)
        for container in class_list_elements_containers.values():
            if container.entities:
                entities.append(container)
    
    def _extract_properties_from_node(self, node: Node, properties_container: EntitiesContainer) -> None:
        """Recursively extract property names from a node and its children."""
        # Check if this node is an assignment with self.property
        if node.type == "assignment":
            for child in node.children:
                if child.type == "attribute":
                    # Look for self.property pattern
                    object_node = None
                    attribute_node = None
                    for attr_child in child.children:
                        if attr_child.type == "identifier":
                            text = attr_child.text.decode("utf8")
                            if text == "self":
                                object_node = attr_child
                            elif object_node is not None:
                                attribute_node = attr_child
                    
                    if attribute_node:
                        prop_name = attribute_node.text.decode("utf8")
                        # Avoid duplicates
                        existing_names = [e.name for e in properties_container.entities]
                        if prop_name not in existing_names:
                            properties_container.append(Entity(prop_name, attribute_node))
        
        # Recursively process children
        for child in node.children:
            self._extract_properties_from_node(child, properties_container)
    
    def _extract_annotated_field_names(self, statement: Node, properties_container: EntitiesContainer) -> None:
        """Extract field names from type-annotated assignments (e.g., dataclass fields)."""
        # Look for assignment nodes with type annotations
        # Pattern: identifier : type = value OR just identifier : type
        for child in statement.children:
            if child.type == "assignment":
                # The first child should be an identifier (field name)
                field_name = None
                has_type_annotation = False
                
                for assign_child in child.children:
                    if assign_child.type == "identifier" and field_name is None:
                        field_name = assign_child.text.decode("utf8")
                    elif assign_child.text == b":":  # Check for colon token
                        has_type_annotation = True
                
                # Only add if it has a type annotation (to distinguish from regular assignments)
                if field_name and has_type_annotation:
                    # Avoid duplicates
                    existing_names = [e.name for e in properties_container.entities]
                    if field_name not in existing_names:
                        properties_container.append(Entity(field_name, child))
    
    def _extract_string_keys_from_dict(self, dict_node: Node) -> list[str]:
        """Extract static string keys from a dictionary node (only if ALL keys are static strings)."""
        keys = []
        
        # First pass: check if ALL keys are static strings
        for child in dict_node.children:
            if child.type == "pair":
                # The first non-colon child is the key
                key_node = None
                for pair_child in child.children:
                    if pair_child.type != ":":
                        key_node = pair_child
                        break
                
                # If key is not a string, don't extract from this dict
                if key_node and key_node.type != "string":
                    return []  # Return empty list if any key is not static string
        
        # Second pass: extract all string keys
        for child in dict_node.children:
            if child.type == "pair":
                for pair_child in child.children:
                    if pair_child.type == "string":
                        # Extract the string value without quotes
                        key_text = pair_child.text.decode("utf8")
                        # Remove surrounding quotes
                        if len(key_text) >= 2 and key_text[0] in ('"', "'") and key_text[-1] in ('"', "'"):
                            keys.append(key_text[1:-1])
                        break
        
        return keys
    
    def _extract_string_values_from_dict(self, dict_node: Node) -> list[str]:
        """Extract static string values from a dictionary node (only if ALL values are static strings)."""
        values = []
        
        # First pass: check if ALL values are static strings
        for child in dict_node.children:
            if child.type == "pair":
                # The value is after the colon
                value_node = None
                found_colon = False
                for pair_child in child.children:
                    if pair_child.type == ":":
                        found_colon = True
                    elif found_colon and pair_child.type != ":": 
                        value_node = pair_child
                        break
                
                # If value is not a string, don't extract from this dict
                if value_node and value_node.type != "string":
                    return []  # Return empty list if any value is not static string
        
        # Second pass: extract all string values
        for child in dict_node.children:
            if child.type == "pair":
                found_colon = False
                for pair_child in child.children:
                    if pair_child.type == ":":
                        found_colon = True
                    elif found_colon and pair_child.type == "string":
                        # Extract the string value without quotes
                        value_text = pair_child.text.decode("utf8")
                        # Remove surrounding quotes
                        if len(value_text) >= 2 and value_text[0] in ('"', "'") and value_text[-1] in ('"', "'"):
                            values.append(value_text[1:-1])
                        break
        
        return values
    
    def _extract_string_elements_from_list(self, list_node: Node) -> list[str]:
        """Extract static string elements from a list node (only if ALL elements are static strings)."""
        elements = []
        
        # First pass: check if ALL elements are static strings
        for child in list_node.children:
            if child.type == "string":
                continue  # String element, good
            elif child.type in (",", "[", "]"):
                continue  # Syntax elements, ignore
            else:
                # Non-string element found
                return []  # Return empty list if any element is not static string
        
        # Second pass: extract all string elements
        for child in list_node.children:
            if child.type == "string":
                # Extract the string value without quotes
                element_text = child.text.decode("utf8")
                # Remove surrounding quotes
                if len(element_text) >= 2 and element_text[0] in ('"', "'") and element_text[-1] in ('"', "'"):
                    elements.append(element_text[1:-1])
        
        return elements
    
    def _extract_dict_keys_from_statement(self, statement: Node, dict_keys_containers: dict, parent_path: str) -> None:
        """Extract dictionary keys from assignment statements like VAR = {...}."""
        # Look for assignment nodes
        for child in statement.children:
            if child.type == "assignment":
                # Find the variable name (left side) and dictionary value (right side)
                var_name = None
                dict_node = None
                
                for assign_child in child.children:
                    if assign_child.type == "identifier" and var_name is None:
                        var_name = assign_child.text.decode("utf8")
                    elif assign_child.type == "attribute" and var_name is None:
                        # Handle self.var_name assignments
                        for attr_child in assign_child.children:
                            if attr_child.type == "identifier":
                                text = attr_child.text.decode("utf8")
                                if text != "self":
                                    var_name = text
                    elif assign_child.type == "dictionary":
                        dict_node = assign_child
                
                if var_name and dict_node:
                    keys = self._extract_string_keys_from_dict(dict_node)
                    if keys:
                        # Create or get container for this variable
                        if var_name not in dict_keys_containers:
                            dict_keys_containers[var_name] = EntitiesContainer(
                                f"{parent_path}::{var_name}", 
                                "dict_keys"
                            )
                        
                        container = dict_keys_containers[var_name]
                        existing_keys = [e.name for e in container.entities]
                        for key in keys:
                            if key not in existing_keys:
                                container.append(Entity(key, dict_node))
    
    def _extract_dict_keys_from_node(self, node: Node, dict_keys_containers: dict, parent_path: str) -> None:
        """Recursively extract dictionary keys from a node and its children."""
        # Check if this node is an assignment with a dictionary
        if node.type == "assignment":
            # Find the variable name (left side) and dictionary value (right side)
            var_name = None
            dict_node = None
            
            for child in node.children:
                if child.type == "identifier" and var_name is None:
                    var_name = child.text.decode("utf8")
                elif child.type == "attribute" and var_name is None:
                    # Handle self.var_name assignments
                    for attr_child in child.children:
                        if attr_child.type == "identifier":
                            text = attr_child.text.decode("utf8")
                            if text != "self":
                                var_name = text
                elif child.type == "dictionary":
                    dict_node = child
            
            if var_name and dict_node:
                keys = self._extract_string_keys_from_dict(dict_node)
                if keys:
                    # Create or get container for this variable
                    if var_name not in dict_keys_containers:
                        dict_keys_containers[var_name] = EntitiesContainer(
                            f"{parent_path}::{var_name}", 
                            "dict_keys"
                        )
                    
                    container = dict_keys_containers[var_name]
                    existing_keys = [e.name for e in container.entities]
                    for key in keys:
                        if key not in existing_keys:
                            container.append(Entity(key, dict_node))
        
        # Recursively process children
        for child in node.children:
            self._extract_dict_keys_from_node(child, dict_keys_containers, parent_path)
    
    def _extract_dict_values_from_statement(self, statement: Node, dict_values_containers: dict, parent_path: str) -> None:
        """Extract dictionary values from assignment statements like VAR = {...}."""
        # Look for assignment nodes
        for child in statement.children:
            if child.type == "assignment":
                # Find the variable name (left side) and dictionary value (right side)
                var_name = None
                dict_node = None
                
                for assign_child in child.children:
                    if assign_child.type == "identifier" and var_name is None:
                        var_name = assign_child.text.decode("utf8")
                    elif assign_child.type == "attribute" and var_name is None:
                        # Handle self.var_name assignments
                        for attr_child in assign_child.children:
                            if attr_child.type == "identifier":
                                text = attr_child.text.decode("utf8")
                                if text != "self":
                                    var_name = text
                    elif assign_child.type == "dictionary":
                        dict_node = assign_child
                
                if var_name and dict_node:
                    values = self._extract_string_values_from_dict(dict_node)
                    if values:
                        # Create or get container for this variable
                        if var_name not in dict_values_containers:
                            dict_values_containers[var_name] = EntitiesContainer(
                                f"{parent_path}::{var_name}", 
                                "dict_values"
                            )
                        
                        container = dict_values_containers[var_name]
                        existing_values = [e.name for e in container.entities]
                        for value in values:
                            if value not in existing_values:
                                container.append(Entity(value, dict_node))
    
    def _extract_dict_values_from_node(self, node: Node, dict_values_containers: dict, parent_path: str) -> None:
        """Recursively extract dictionary values from a node and its children."""
        # Check if this node is an assignment with a dictionary
        if node.type == "assignment":
            # Find the variable name (left side) and dictionary value (right side)
            var_name = None
            dict_node = None
            
            for child in node.children:
                if child.type == "identifier" and var_name is None:
                    var_name = child.text.decode("utf8")
                elif child.type == "attribute" and var_name is None:
                    # Handle self.var_name assignments
                    for attr_child in child.children:
                        if attr_child.type == "identifier":
                            text = attr_child.text.decode("utf8")
                            if text != "self":
                                var_name = text
                elif child.type == "dictionary":
                    dict_node = child
            
            if var_name and dict_node:
                values = self._extract_string_values_from_dict(dict_node)
                if values:
                    # Create or get container for this variable
                    if var_name not in dict_values_containers:
                        dict_values_containers[var_name] = EntitiesContainer(
                            f"{parent_path}::{var_name}", 
                            "dict_values"
                        )
                    
                    container = dict_values_containers[var_name]
                    existing_values = [e.name for e in container.entities]
                    for value in values:
                        if value not in existing_values:
                            container.append(Entity(value, dict_node))
        
        # Recursively process children
        for child in node.children:
            self._extract_dict_values_from_node(child, dict_values_containers, parent_path)
    
    def _extract_list_elements_from_statement(self, statement: Node, list_elements_containers: dict, parent_path: str) -> None:
        """Extract list elements from assignment statements like VAR = [...]."""
        # Look for assignment nodes
        for child in statement.children:
            if child.type == "assignment":
                # Find the variable name (left side) and list value (right side)
                var_name = None
                list_node = None
                
                for assign_child in child.children:
                    if assign_child.type == "identifier" and var_name is None:
                        var_name = assign_child.text.decode("utf8")
                    elif assign_child.type == "attribute" and var_name is None:
                        # Handle self.var_name assignments
                        for attr_child in assign_child.children:
                            if attr_child.type == "identifier":
                                text = attr_child.text.decode("utf8")
                                if text != "self":
                                    var_name = text
                    elif assign_child.type == "list":
                        list_node = assign_child
                
                if var_name and list_node:
                    elements = self._extract_string_elements_from_list(list_node)
                    if elements:
                        # Create or get container for this variable
                        if var_name not in list_elements_containers:
                            list_elements_containers[var_name] = EntitiesContainer(
                                f"{parent_path}::{var_name}", 
                                "list_elements"
                            )
                        
                        container = list_elements_containers[var_name]
                        existing_elements = [e.name for e in container.entities]
                        for element in elements:
                            if element not in existing_elements:
                                container.append(Entity(element, list_node))
    
    def _extract_list_elements_from_node(self, node: Node, list_elements_containers: dict, parent_path: str) -> None:
        """Recursively extract list elements from a node and its children."""
        # Check if this node is an assignment with a list
        if node.type == "assignment":
            # Find the variable name (left side) and list value (right side)
            var_name = None
            list_node = None
            
            for child in node.children:
                if child.type == "identifier" and var_name is None:
                    var_name = child.text.decode("utf8")
                elif child.type == "attribute" and var_name is None:
                    # Handle self.var_name assignments
                    for attr_child in child.children:
                        if attr_child.type == "identifier":
                            text = attr_child.text.decode("utf8")
                            if text != "self":
                                var_name = text
                elif child.type == "list":
                    list_node = child
            
            if var_name and list_node:
                elements = self._extract_string_elements_from_list(list_node)
                if elements:
                    # Create or get container for this variable
                    if var_name not in list_elements_containers:
                        list_elements_containers[var_name] = EntitiesContainer(
                            f"{parent_path}::{var_name}", 
                            "list_elements"
                        )
                    
                    container = list_elements_containers[var_name]
                    existing_elements = [e.name for e in container.entities]
                    for element in elements:
                        if element not in existing_elements:
                            container.append(Entity(element, list_node))
        
        # Recursively process children
        for child in node.children:
            self._extract_list_elements_from_node(child, list_elements_containers, parent_path)
    
    def _extract_python_imports(self, node: Node, imports: set) -> None:
        """Extract Python import statements."""
        if node.type == "import_statement":
            # import foo, bar.baz
            for child in node.children:
                if child.type == "dotted_name":
                    module_name = child.text.decode("utf8")
                    imports.add(module_name)
                elif child.type == "aliased_import":
                    # import foo as f
                    for subchild in child.children:
                        if subchild.type == "dotted_name":
                            module_name = subchild.text.decode("utf8")
                            imports.add(module_name)
                            break
        
        elif node.type == "import_from_statement":
            # from foo.bar import baz
            for child in node.children:
                if child.type == "dotted_name":
                    module_name = child.text.decode("utf8")
                    # Skip relative imports starting with '.'
                    if not module_name.startswith('.'):
                        imports.add(module_name)
                    break
        
        # Recurse through children
        for child in node.children:
            self._extract_python_imports(child, imports)
