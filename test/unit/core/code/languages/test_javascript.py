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
            func_names = [e.content for e in func_container.entities]
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
            func_names = [e.content for e in func_container.entities]
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
            class_names = [e.content for e in class_container.entities]
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
            method_names = [e.content for e in methods_container.entities]
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
            func_names = [e.content for e in func_container.entities]
            self.assertIn("myFunction", func_names)
            self.assertIn("myArrow", func_names)
        finally:
            temp_path.unlink()

class TestJavaScriptFunctionArguments(unittest.TestCase):
    
    def setUp(self):
        self.analyzer = JavaScriptAnalyzer()
    
    def test_function_arguments(self):
        """Test collecting JavaScript function arguments."""
        code = """
function calculate(x, y, operation) {
    return operation(x, y);
}

function greet(name, greeting = "Hello") {
    return `${greeting}, ${name}`;
}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
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
        """Test collecting method arguments from classes."""
        code = """
class Calculator {
    constructor(precision) {
        this.precision = precision;
    }
    
    add(a, b) {
        return (a + b).toFixed(this.precision);
    }
}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(code)
            temp_path = Path(f.name)
        
        try:
            entities = []
            self.analyzer.collect_entities(temp_path, entities)
            
            # Find function_arguments containers
            args_containers = [e for e in entities if e.type == "function_arguments"]
            self.assertEqual(len(args_containers), 2)  # constructor, add
            
            # Check constructor arguments
            constructor_args = next((e for e in args_containers if "constructor" in e.parent), None)
            self.assertIsNotNone(constructor_args)
            arg_names = [e.content for e in constructor_args.entities]
            self.assertIn("precision", arg_names)
            
            # Check add arguments
            add_args = next((e for e in args_containers if "add" in e.parent), None)
            self.assertIsNotNone(add_args)
            arg_names = [e.content for e in add_args.entities]
            self.assertIn("a", arg_names)
            self.assertIn("b", arg_names)
        finally:
            temp_path.unlink()


class TestJavaScriptTableRecords(unittest.TestCase):
    
    def setUp(self):
        self.analyzer = JavaScriptAnalyzer()
    
    def test_table_records_uniform_objects(self):
        """Test collecting table records from uniform array of objects."""
        code = """
const PATTERN_DEFS = [
    {
        name: "Unix path",
        handler: "contains_path",
    },
    {
        name: "Windows path",
        handler: "contains_path",
    },
    {
        name: "Filename",
        handler: "contains_file",
    },
];
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
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

if __name__ == "__main__":
    unittest.main()
