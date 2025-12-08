"""
JavaScript language analyzer using tree-sitter.
"""

from pathlib import Path
from typing import Set
import tree_sitter_javascript as ts_js
from tree_sitter import Language, Node

from src.core.code.language import LanguageAnalyzer


class JavaScriptAnalyzer(LanguageAnalyzer):
    """JavaScript-specific code analyzer using tree-sitter."""
    
    def _get_language(self) -> Language:
        """Return the tree-sitter Language object for JavaScript."""
        return Language(ts_js.language())
    
    def collect_entities(self, file_path: Path, entities: list) -> None:
        """
        Collect JavaScript code entities (functions, classes, etc.) from a file.
        
        Args:
            file_path: Path to the JavaScript source file
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
        
        for child in root_node.children:
            # Function declarations at module level
            if child.type == "function_declaration":
                func_name = self._get_function_name(child)
                if func_name:
                    module_functions.append(Entity(func_name, child))
            
            # Arrow functions assigned to variables (const foo = () => {})
            elif child.type in ("lexical_declaration", "variable_declaration"):
                self._extract_arrow_functions(child, module_functions)
            
            # Class declarations at module level
            elif child.type == "class_declaration":
                class_name = self._get_class_name(child)
                if class_name:
                    module_classes.append(Entity(class_name, child))
                    # Process class methods
                    self._process_class(child, str_file_path, class_name, entities)
            
            # Export statements that contain functions/classes
            elif child.type == "export_statement":
                self._process_export(child, module_functions, module_classes, str_file_path, entities)
        
        # Add containers if they have entities
        if module_functions.entities:
            entities.append(module_functions)
        if module_classes.entities:
            entities.append(module_classes)
    
    def collect_imports(self, file_path: Path) -> Set[str]:
        """
        Collect all imported module names from a JavaScript file.
        
        Args:
            file_path: Path to the JavaScript source file
            
        Returns:
            Set of module names that are imported
        """
        root_node = self.parse_file(file_path)
        if root_node is None:
            return set()
        
        imports = set()
        self._extract_js_imports(root_node, imports)
        return imports
    
    def _extract_js_imports(self, node: Node, imports: set) -> None:
        """Extract JavaScript/TypeScript import statements."""
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
            self._extract_js_imports(child, imports)
    
    def _get_function_name(self, node: Node) -> str:
        """Extract function name from function_declaration node."""
        for child in node.children:
            if child.type == "identifier":
                return child.text.decode("utf8")
        return ""
    
    def _get_class_name(self, node: Node) -> str:
        """Extract class name from class_declaration node."""
        for child in node.children:
            if child.type == "identifier":
                return child.text.decode("utf8")
        return ""
    
    def _extract_arrow_functions(self, declaration: Node, functions_container) -> None:
        """Extract arrow functions from const/let/var declarations."""
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
        """Process a class declaration to extract methods."""
        from src.core.entity import Entity, EntitiesContainer
        
        class_methods = EntitiesContainer(f"{file_path}::{class_name}", "class_methods")
        
        # Find class body
        for child in class_node.children:
            if child.type == "class_body":
                for statement in child.children:
                    if statement.type == "method_definition":
                        method_name = self._get_method_name(statement)
                        if method_name:
                            class_methods.append(Entity(method_name, statement))
        
        # Add container if it has entities
        if class_methods.entities:
            entities.append(class_methods)
    
    def _get_method_name(self, node: Node) -> str:
        """Extract method name from method_definition node."""
        for child in node.children:
            if child.type == "property_identifier":
                return child.text.decode("utf8")
        return ""
    
    def _process_export(self, export_node: Node, functions_container, classes_container, file_path: str, entities: list) -> None:
        """Process export statements to extract exported functions/classes."""
        from src.core.entity import Entity
        
        for child in export_node.children:
            if child.type == "function_declaration":
                func_name = self._get_function_name(child)
                if func_name:
                    functions_container.append(Entity(func_name, child))
            elif child.type == "class_declaration":
                class_name = self._get_class_name(child)
                if class_name:
                    classes_container.append(Entity(class_name, child))
                    self._process_class(child, file_path, class_name, entities)
            elif child.type == "lexical_declaration":
                self._extract_arrow_functions(child, functions_container)

