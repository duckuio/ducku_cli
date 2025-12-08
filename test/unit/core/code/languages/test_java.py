"""Tests for Java analyzer."""

import unittest
import tempfile
from pathlib import Path
from src.core.code.languages.java import JavaAnalyzer


class TestJavaAnalyzer(unittest.TestCase):
    
    def setUp(self):
        self.analyzer = JavaAnalyzer()
    
    def test_collect_classes(self):
        """Test collecting class declarations."""
        code = """
package com.example;

public class Person {
    private String name;
    
    public Person(String name) {
        this.name = name;
    }
    
    public String getName() {
        return name;
    }
}

class Animal {
    void speak() {
        System.out.println("Sound");
    }
}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
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
    
    def test_collect_methods(self):
        """Test collecting methods from classes."""
        code = """
public class Calculator {
    public int add(int a, int b) {
        return a + b;
    }
    
    public int subtract(int a, int b) {
        return a - b;
    }
}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
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
    
    def test_collect_interface(self):
        """Test collecting interface declarations."""
        code = """
public interface Drawable {
    void draw();
    void resize(int width, int height);
}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
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
            self.assertIn("Drawable", class_names)
        finally:
            temp_path.unlink()
    
    def test_collect_imports(self):
        """Test collecting import statements."""
        code = """
import java.util.ArrayList;
import java.util.List;
import com.example.MyClass;
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
            f.write(code)
            temp_path = Path(f.name)
        
        try:
            imports = self.analyzer.collect_imports(temp_path)
            self.assertIn("java.util.ArrayList", imports)
            self.assertIn("java.util.List", imports)
            self.assertIn("com.example.MyClass", imports)
        finally:
            temp_path.unlink()


if __name__ == "__main__":
    unittest.main()
