"""Tests for TypeScript analyzer."""

import unittest
import tempfile
from pathlib import Path
from src.core.code.languages.typescript import TypeScriptAnalyzer


class TestTypeScriptAnalyzer(unittest.TestCase):
    
    def setUp(self):
        self.analyzer = TypeScriptAnalyzer()
    
    def test_collect_functions(self):
        """Test collecting function declarations."""
        code = """
function greet(name: string): string {
    return `Hello, ${name}`;
}

function calculate(a: number, b: number): number {
    return a + b;
}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as f:
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
            self.assertIn("calculate", func_names)
        finally:
            temp_path.unlink()
    
    def test_collect_arrow_functions(self):
        """Test collecting arrow functions with types."""
        code = """
const add = (a: number, b: number): number => a + b;
const multiply: (x: number, y: number) => number = (x, y) => {
    return x * y;
};
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as f:
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
    constructor(private name: string) {}
    
    greet(): string {
        return `Hello, I'm ${this.name}`;
    }
}

interface Animal {
    speak(): void;
}

class Dog implements Animal {
    speak(): void {
        console.log('Woof!');
    }
}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as f:
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
            self.assertIn("Dog", class_names)
        finally:
            temp_path.unlink()
    
    def test_collect_imports(self):
        """Test collecting import statements."""
        code = """
import React from 'react';
import { useState, useEffect } from 'react';
import type { FC } from 'react';
const fs = require('fs');
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as f:
            f.write(code)
            temp_path = Path(f.name)
        
        try:
            imports = self.analyzer.collect_imports(temp_path)
            self.assertIn("react", imports)
            self.assertIn("fs", imports)
        finally:
            temp_path.unlink()


if __name__ == "__main__":
    unittest.main()
