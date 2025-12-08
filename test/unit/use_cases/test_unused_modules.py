import unittest
from pathlib import Path
from unittest.mock import Mock
from src.use_cases.unused_modules import UnusedModules
from src.core.project import Project
from src.core.code.dispatcher import collect_imports_from_content, is_supported_format
import tempfile


class TestUnusedModules(unittest.TestCase):
    
    def setUp(self):
        self.project = Mock(spec=Project)
        self.project.project_root = Path("/fake/project")
        self.unused_modules = UnusedModules(self.project)
    
    def test_is_supported_format(self):
        """Test file format support detection."""
        test_cases = [
            (".py", True),
            (".js", True),
            (".java", True),
            (".go", True),
            (".rb", True),
            (".php", False),  # Not yet implemented
            (".ts", True),
            (".tsx", True),
            (".jsx", True),
            (".rs", False),  # Not yet implemented
            (".unknown", False),
        ]
        
        for ext, expected in test_cases:
            with self.subTest(extension=ext):
                result = is_supported_format(ext)
                self.assertEqual(result, expected)
    
    def test_extract_imports_python(self):
        """Test Python import extraction using tree-sitter."""
        content = """
import os
import sys
from pathlib import Path
from typing import Dict, List
import numpy as np
from .local_module import something
from src.core.configuration import parse_yaml
        """
        
        # Create a temporary file to test
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)
        
        try:
            imports = collect_imports_from_content(temp_path)
            # Should contain the non-relative imports
            expected_imports = {"os", "sys", "pathlib", "typing", "numpy", "src.core.configuration"}
            for expected_import in expected_imports:
                self.assertIn(expected_import, imports)
            
            # Should NOT contain relative imports (starting with .)
            self.assertNotIn(".local_module", imports)
        finally:
            temp_path.unlink()
    
    def test_extract_imports_javascript(self):
        """Test JavaScript import extraction using tree-sitter."""
        content = """
import React from 'react';
import { Component } from 'react';
const fs = require('fs');
import('./dynamic-module');
        """
        
        # Create a temporary file to test
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)
        
        try:
            imports = collect_imports_from_content(temp_path)
            # Should contain non-relative imports
            self.assertIn("react", imports)
            self.assertIn("fs", imports)
        finally:
            temp_path.unlink()
    
    def test_get_module_name_from_file(self):
        """Test module name extraction from file paths."""
        test_cases = [
            (Path("/fake/project/utils.py"), "utils"),
            (Path("/fake/project/src/helpers/validator.py"), "helpers.validator"),
            (Path("/fake/project/lib/core/entity.py"), "core.entity"),
            (Path("/fake/project/app/models/user.py"), "models.user"),
        ]
        
        for file_path, expected_module in test_cases:
            with self.subTest(file_path=file_path):
                result = self.unused_modules.get_module_name_from_file(file_path)
                self.assertEqual(result, expected_module)
    
    def test_is_test_file(self):
        """Test test file detection."""
        test_cases = [
            (Path("/project/test/unit/test_something.py"), True),
            (Path("/project/tests/integration/user_test.py"), True),
            (Path("/project/src/models/user.py"), False),
            (Path("/project/spec/user_spec.py"), True),
            (Path("/project/testing/mock_data.py"), True),
            (Path("/project/src/utils.py"), False),
            (Path("/project/test_config.py"), True),
            (Path("/project/config_test.py"), True),
        ]
        
        for file_path, expected_is_test in test_cases:
            with self.subTest(file_path=file_path):
                result = self.unused_modules.is_test_file(file_path)
                self.assertEqual(result, expected_is_test)


if __name__ == "__main__":
    unittest.main()
