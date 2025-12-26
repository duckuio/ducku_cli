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
            func_names = [e.content for e in func_container.entities]
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
            func_names = [e.content for e in func_container.entities]
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
            class_names = [e.content for e in class_container.entities]
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


class TestTypeScriptFunctionArguments(unittest.TestCase):
    
    def setUp(self):
        self.analyzer = TypeScriptAnalyzer()
    
    def test_function_arguments(self):
        """Test collecting TypeScript function arguments."""
        code = """
function calculate(x: number, y: number, operation: Function): number {
    return operation(x, y);
}

function greet(name: string, greeting: string = "Hello"): string {
    return `${greeting}, ${name}`;
}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as f:
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
        """Test collecting TypeScript method arguments."""
        code = """
class Calculator {
    constructor(precision: number) {
        this.precision = precision;
    }
    
    add(a: number, b: number): number {
        return a + b;
    }
}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as f:
            f.write(code)
            temp_path = Path(f.name)
        
        try:
            entities = []
            self.analyzer.collect_entities(temp_path, entities)
            
            # Find function_arguments containers
            args_containers = [e for e in entities if e.type == "function_arguments"]
            self.assertGreaterEqual(len(args_containers), 2)
            
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


class TestTypeScriptTableRecords(unittest.TestCase):
    
    def setUp(self):
        self.analyzer = TypeScriptAnalyzer()
    
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
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as f:
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
