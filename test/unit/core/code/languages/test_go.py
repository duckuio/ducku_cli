"""Tests for Go analyzer."""

import unittest
import tempfile
from pathlib import Path
from src.core.code.languages.go import GoAnalyzer


class TestGoAnalyzer(unittest.TestCase):
    
    def setUp(self):
        self.analyzer = GoAnalyzer()
    
    def test_collect_functions(self):
        """Test collecting function declarations."""
        code = """
package main

func greet(name string) string {
    return "Hello, " + name
}

func add(a, b int) int {
    return a + b
}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.go', delete=False) as f:
            f.write(code)
            temp_path = Path(f.name)
        
        try:
            entities = []
            self.analyzer.collect_entities(temp_path, entities)
            
            func_container = None
            for e in entities:
                if e.type == "module_functions":
                    func_container = e
                    break
            
            self.assertIsNotNone(func_container)
            func_names = [e.content for e in func_container.entities]
            self.assertIn("greet", func_names)
            self.assertIn("add", func_names)
        finally:
            temp_path.unlink()
    
    def test_collect_structs(self):
        """Test collecting struct type declarations."""
        code = """
package main

type Person struct {
    Name string
    Age  int
}

type Animal struct {
    Species string
}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.go', delete=False) as f:
            f.write(code)
            temp_path = Path(f.name)
        
        try:
            entities = []
            self.analyzer.collect_entities(temp_path, entities)
            
            class_container = None
            for e in entities:
                if e.type == "module_classes":
                    class_container = e
                    break
            
            self.assertIsNotNone(class_container)
            class_names = [e.content for e in class_container.entities]
            self.assertIn("Person", class_names)
            self.assertIn("Animal", class_names)
        finally:
            temp_path.unlink()
    
    def test_collect_methods(self):
        """Test collecting methods on structs."""
        code = """
package main

type Calculator struct{}

func (c Calculator) Add(a, b int) int {
    return a + b
}

func (c *Calculator) Subtract(a, b int) int {
    return a - b
}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.go', delete=False) as f:
            f.write(code)
            temp_path = Path(f.name)
        
        try:
            entities = []
            self.analyzer.collect_entities(temp_path, entities)
            
            # Find class_methods container for Calculator
            methods_container = None
            for e in entities:
                if e.type == "class_methods" and "Calculator" in e.parent:
                    methods_container = e
                    break
            
            self.assertIsNotNone(methods_container)
            method_names = [e.content for e in methods_container.entities]
            self.assertIn("Add", method_names)
            self.assertIn("Subtract", method_names)
        finally:
            temp_path.unlink()
    
    def test_collect_imports(self):
        """Test collecting import statements."""
        code = """
package main

import (
    "fmt"
    "strings"
)
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.go', delete=False) as f:
            f.write(code)
            temp_path = Path(f.name)
        
        try:
            imports = self.analyzer.collect_imports(temp_path)
            self.assertIn("fmt", imports)
            self.assertIn("strings", imports)
        finally:
            temp_path.unlink()


class TestGoFunctionArguments(unittest.TestCase):
    
    def setUp(self):
        self.analyzer = GoAnalyzer()
    
    def test_function_arguments(self):
        """Test collecting Go function arguments."""
        code = """
package main

func calculate(x int, y int, factor float64) float64 {
    return float64(x+y) * factor
}

func greet(name string, greeting string) string {
    return greeting + ", " + name
}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.go', delete=False) as f:
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
            self.assertIn("factor", arg_names)
        finally:
            temp_path.unlink()
    
    def test_method_arguments(self):
        """Test collecting Go method arguments."""
        code = """
package main

type Calculator struct {
    precision int
}

func (c *Calculator) Add(a int, b int) int {
    return a + b
}

func (c Calculator) Multiply(x int, y int, factor int) int {
    return x * y * factor
}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.go', delete=False) as f:
            f.write(code)
            temp_path = Path(f.name)
        
        try:
            entities = []
            self.analyzer.collect_entities(temp_path, entities)
            
            # Find function_arguments containers
            args_containers = [e for e in entities if e.type == "function_arguments"]
            self.assertEqual(len(args_containers), 2)  # Add, Multiply
            
            # Check Add arguments
            add_args = next((e for e in args_containers if "Add" in e.parent), None)
            self.assertIsNotNone(add_args)
            arg_names = [e.content for e in add_args.entities]
            self.assertIn("a", arg_names)
            self.assertIn("b", arg_names)
        finally:
            temp_path.unlink()


if __name__ == '__main__':
    unittest.main()
