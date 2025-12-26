"""Tests for Ruby analyzer."""

import unittest
import tempfile
from pathlib import Path
from src.core.code.languages.ruby import RubyAnalyzer


class TestRubyAnalyzer(unittest.TestCase):
    
    def setUp(self):
        self.analyzer = RubyAnalyzer()
    
    def test_collect_methods(self):
        """Test collecting top-level method definitions."""
        code = """
def greet(name)
  "Hello, #{name}"
end

def add(a, b)
  a + b
end
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rb', delete=False) as f:
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
    
    def test_collect_classes(self):
        """Test collecting class declarations."""
        code = """
class Person
  def initialize(name)
    @name = name
  end
  
  def greet
    "Hello, I'm #{@name}"
  end
end

class Animal
  def speak
    puts 'Sound'
  end
end
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rb', delete=False) as f:
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
    
    def test_collect_class_methods(self):
        """Test collecting methods from classes."""
        code = """
class Calculator
  def add(a, b)
    a + b
  end
  
  def subtract(a, b)
    a - b
  end
end
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rb', delete=False) as f:
            f.write(code)
            temp_path = Path(f.name)
        
        try:
            entities = []
            self.analyzer.collect_entities(temp_path, entities)
            
            # Find class_methods container
            methods_container = None
            for e in entities:
                if e.type == "class_methods" and "Calculator" in e.parent:
                    methods_container = e
                    break
            
            self.assertIsNotNone(methods_container)
            method_names = [e.content for e in methods_container.entities]
            self.assertIn("add", method_names)
            self.assertIn("subtract", method_names)
        finally:
            temp_path.unlink()
    
    def test_collect_modules(self):
        """Test collecting module declarations."""
        code = """
module Greetable
  def greet
    "Hello!"
  end
end
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rb', delete=False) as f:
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
            self.assertIn("Greetable", class_names)
        finally:
            temp_path.unlink()
    
    def test_collect_imports(self):
        """Test collecting require statements."""
        code = """
require 'json'
require 'net/http'
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rb', delete=False) as f:
            f.write(code)
            temp_path = Path(f.name)
        
        try:
            imports = self.analyzer.collect_imports(temp_path)
            self.assertIn("json", imports)
            self.assertIn("net/http", imports)
        finally:
            temp_path.unlink()


class TestRubyFunctionArguments(unittest.TestCase):
    
    def setUp(self):
        self.analyzer = RubyAnalyzer()
    
    def test_function_arguments(self):
        """Test collecting Ruby method arguments."""
        code = """
def calculate(x, y, operation)
    operation.call(x, y)
end

def greet(name, greeting = "Hello")
    "#{greeting}, #{name}"
end
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rb', delete=False) as f:
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
        finally:
            temp_path.unlink()
    
    def test_method_arguments(self):
        """Test collecting Ruby class method arguments."""
        code = """
class Calculator
    def initialize(precision)
        @precision = precision
    end
    
    def add(a, b)
        (a + b).round(@precision)
    end
    
    def multiply(x, y, factor = 1.0)
        (x * y * factor).round(@precision)
    end
end
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rb', delete=False) as f:
            f.write(code)
            temp_path = Path(f.name)
        
        try:
            entities = []
            self.analyzer.collect_entities(temp_path, entities)
            
            # Find function_arguments containers
            args_containers = [e for e in entities if e.type == "function_arguments"]
            self.assertEqual(len(args_containers), 3)  # initialize, add, multiply
            
            # Check initialize arguments
            init_args = next((e for e in args_containers if "initialize" in e.parent), None)
            self.assertIsNotNone(init_args)
            arg_names = [e.content for e in init_args.entities]
            self.assertIn("precision", arg_names)
        finally:
            temp_path.unlink()


class TestRubyTableRecords(unittest.TestCase):
    
    def setUp(self):
        self.analyzer = RubyAnalyzer()
    
    def test_table_records_uniform_hashes(self):
        """Test collecting table records from uniform array of hashes."""
        code = """
PATTERN_DEFS = [
    {
        :name => "Unix path",
        :handler => "contains_path",
    },
    {
        :name => "Windows path",
        :handler => "contains_path",
    },
    {
        :name => "Filename",
        :handler => "contains_file",
    },
]
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rb', delete=False) as f:
            f.write(code)
            temp_path = Path(f.name)
        
        try:
            entities = []
            self.analyzer.collect_entities(temp_path, entities)
            
            # Find table_records containers
            table_containers = [e for e in entities if e.type == "table_records"]
            self.assertGreater(len(table_containers), 0)
            
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
        finally:
            temp_path.unlink()


if __name__ == '__main__':
    unittest.main()
