"""Tests for Python code entity collection."""

import unittest
import tempfile
from pathlib import Path
from src.core.code.languages.python import PythonAnalyzer


class TestPythonFunctionArguments(unittest.TestCase):
    
    def setUp(self):
        self.analyzer = PythonAnalyzer()
    
    def test_function_arguments(self):
        """Test collecting function arguments."""
        code = """
def calculate(x, y, operation):
    return operation(x, y)

def greet(name, greeting="Hello"):
    return f"{greeting}, {name}"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_path = Path(f.name)
        
        try:
            entities = []
            self.analyzer.collect_entities(temp_path, entities)
            
            # Find function_arguments containers
            args_containers = [e for e in entities if e.type == "function_arguments"]
            self.assertEqual(len(args_containers), 2)
            
            # Check calculate arguments
            calc_args = next((e for e in args_containers if "calculate" in e.parent), None)
            self.assertIsNotNone(calc_args)
            arg_names = [e.content for e in calc_args.entities]
            self.assertIn("x", arg_names)
            self.assertIn("y", arg_names)
            self.assertIn("operation", arg_names)
            
            # Check greet arguments
            greet_args = next((e for e in args_containers if "greet" in e.parent), None)
            self.assertIsNotNone(greet_args)
            arg_names = [e.content for e in greet_args.entities]
            self.assertIn("name", arg_names)
            self.assertIn("greeting", arg_names)
        finally:
            temp_path.unlink()
    
    def test_method_arguments(self):
        """Test collecting method arguments including constructors."""
        code = """
class Calculator:
    def __init__(self, precision):
        self.precision = precision
    
    def add(self, a, b):
        return round(a + b, self.precision)
    
    def multiply(self, x, y, factor=1.0):
        return round(x * y * factor, self.precision)
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_path = Path(f.name)
        
        try:
            entities = []
            self.analyzer.collect_entities(temp_path, entities)
            
            # Find function_arguments containers for methods
            args_containers = [e for e in entities if e.type == "function_arguments"]
            self.assertEqual(len(args_containers), 3)  # __init__, add, multiply
            
            # Check __init__ arguments (constructor)
            init_args = next((e for e in args_containers if "__init__" in e.parent), None)
            self.assertIsNotNone(init_args)
            arg_names = [e.content for e in init_args.entities]
            self.assertIn("precision", arg_names)
            self.assertNotIn("self", arg_names)  # self should be excluded
            
            # Check add arguments
            add_args = next((e for e in args_containers if "add" in e.parent), None)
            self.assertIsNotNone(add_args)
            arg_names = [e.content for e in add_args.entities]
            self.assertIn("a", arg_names)
            self.assertIn("b", arg_names)
            
            # Check multiply arguments
            multiply_args = next((e for e in args_containers if "multiply" in e.parent), None)
            self.assertIsNotNone(multiply_args)
            arg_names = [e.content for e in multiply_args.entities]
            self.assertIn("x", arg_names)
            self.assertIn("y", arg_names)
            self.assertIn("factor", arg_names)
        finally:
            temp_path.unlink()


class TestPythonTableRecords(unittest.TestCase):
    
    def setUp(self):
        self.analyzer = PythonAnalyzer()
    
    def test_table_records_uniform_dicts(self):
        """Test collecting table records from uniform list of dictionaries."""
        code = """
PATTERN_DEFS = [
    {
        "name": "Unix path",
        "pattern": r"/some/path",
        "handler": "contains_path",
    },
    {
        "name": "Windows path",
        "pattern": r"C:\\\\path",
        "handler": "contains_path",
    },
    {
        "name": "Filename",
        "pattern": r"file\\.txt",
        "handler": "contains_file",
    },
]
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_path = Path(f.name)
        
        try:
            entities = []
            self.analyzer.collect_entities(temp_path, entities)
            
            # Find table_records containers
            table_containers = [e for e in entities if e.type == "table_records"]
            self.assertGreater(len(table_containers), 0)
            
            # Debug: print what we found
            for container in table_containers:
                if "PATTERN_DEFS" in container.parent:
                    print(f"Found container: {container.parent}")
                    print(f"  Values: {[e.content for e in container.entities]}")
            
            # Check that we have containers for each key (at least name and handler which have string values)
            container_keys = set()
            for container in table_containers:
                if "PATTERN_DEFS" in container.parent:
                    # Extract the key name from parent path
                    parts = container.parent.split("::")
                    if len(parts) >= 3:
                        container_keys.add(parts[-1])
            
            self.assertIn("name", container_keys)
            self.assertIn("handler", container_keys)
            
            # Check name values
            name_container = next((e for e in table_containers if "PATTERN_DEFS::name" in e.parent), None)
            self.assertIsNotNone(name_container)
            name_values = [e.content for e in name_container.entities]
            self.assertIn("Unix path", name_values)
            self.assertIn("Windows path", name_values)
            self.assertIn("Filename", name_values)
            
            # Check handler values
            handler_container = next((e for e in table_containers if "PATTERN_DEFS::handler" in e.parent), None)
            self.assertIsNotNone(handler_container)
            handler_values = [e.content for e in handler_container.entities]
            self.assertIn("contains_path", handler_values)
            self.assertIn("contains_file", handler_values)
            
            # Note: pattern values are raw strings, not plain strings, so they won't be extracted
        finally:
            temp_path.unlink()
    
    def test_table_records_non_uniform_dicts(self):
        """Test that non-uniform dictionaries are not collected as table records."""
        code = """
CONFIG = [
    {
        "name": "setting1",
        "value": "test",
    },
    {
        "name": "setting2",
        "different_key": "value",
    },
]
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_path = Path(f.name)
        
        try:
            entities = []
            self.analyzer.collect_entities(temp_path, entities)
            
            # Should not find table_records for CONFIG since dicts have different keys
            table_containers = [e for e in entities if e.type == "table_records" and "CONFIG" in e.parent]
            self.assertEqual(len(table_containers), 0)
        finally:
            temp_path.unlink()
    
    def test_table_records_single_dict(self):
        """Test that a list with single dictionary is not collected as table records."""
        code = """
DATA = [
    {
        "key": "value",
    },
]
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_path = Path(f.name)
        
        try:
            entities = []
            self.analyzer.collect_entities(temp_path, entities)
            
            # Should not find table_records for DATA since there's only one dict
            table_containers = [e for e in entities if e.type == "table_records" and "DATA" in e.parent]
            self.assertEqual(len(table_containers), 0)
        finally:
            temp_path.unlink()


if __name__ == '__main__':
    unittest.main()
