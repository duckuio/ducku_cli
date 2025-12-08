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
            func_names = [e.name for e in func_container.entities]
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
            class_names = [e.name for e in class_container.entities]
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
            method_names = [e.name for e in methods_container.entities]
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
            class_names = [e.name for e in class_container.entities]
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


if __name__ == "__main__":
    unittest.main()
