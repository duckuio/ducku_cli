"""Tests for JavaScript analyzer."""

import unittest
import tempfile
from pathlib import Path
from src.core.code.languages.javascript import JavaScriptAnalyzer


class TestJavaScriptAnalyzer(unittest.TestCase):
    
    def setUp(self):
        self.analyzer = JavaScriptAnalyzer()
    
    def test_collect_functions(self):
        """Test collecting function declarations."""
        code = """
function greet(name) {
    return `Hello, ${name}`;
}

function calculate(a, b) {
    return a + b;
}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(code)
            temp_path = Path(f.name)
        
        try:
            entities = []
            self.analyzer.collect_entities(temp_path, entities)
            
            # Find module_functions container
            func_container = None
            for e in entities:
                if e.type == "module_functions":
                    func_container = e
                    break
            
            self.assertIsNotNone(func_container)
            func_names = [e.name for e in func_container.entities]
            self.assertIn("greet", func_names)
            self.assertIn("calculate", func_names)
            self.assertEqual(len(func_names), 2)
        finally:
            temp_path.unlink()
    
    def test_collect_arrow_functions(self):
        """Test collecting arrow functions."""
        code = """
const add = (a, b) => a + b;
const multiply = (x, y) => {
    return x * y;
};
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
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
            self.assertIn("add", func_names)
            self.assertIn("multiply", func_names)
        finally:
            temp_path.unlink()
    
    def test_collect_classes(self):
        """Test collecting class declarations."""
        code = """
class Person {
    constructor(name) {
        this.name = name;
    }
    
    greet() {
        return `Hello, I'm ${this.name}`;
    }
}

class Animal {
    speak() {
        console.log('Sound');
    }
}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
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
class Calculator {
    add(a, b) {
        return a + b;
    }
    
    subtract(a, b) {
        return a - b;
    }
}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
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
    
    def test_collect_imports(self):
        """Test collecting import statements."""
        code = """
import React from 'react';
import { useState } from 'react';
const fs = require('fs');
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(code)
            temp_path = Path(f.name)
        
        try:
            imports = self.analyzer.collect_imports(temp_path)
            self.assertIn("react", imports)
            self.assertIn("fs", imports)
        finally:
            temp_path.unlink()
    
    def test_export_function(self):
        """Test collecting exported functions."""
        code = """
export function myFunction() {
    return 42;
}

export const myArrow = () => 'hello';
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
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
            self.assertIn("myFunction", func_names)
            self.assertIn("myArrow", func_names)
        finally:
            temp_path.unlink()


if __name__ == "__main__":
    unittest.main()
