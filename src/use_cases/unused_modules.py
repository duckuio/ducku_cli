from pathlib import Path
from typing import Set, Dict
from src.core.base_usecase import BaseUseCase
from src.core.project import Project
from src.core.code.dispatcher import collect_imports_from_content, is_supported_format


class UnusedModules(BaseUseCase):
    """
    A use case to find modules that are defined but never imported anywhere in the project.
    Uses tree-sitter for accurate import extraction across multiple languages.
    """

    def __init__(self, project: Project):
        super().__init__(project)
        self.name = "unused_modules"

    def get_module_name_from_file(self, file_path: Path) -> str:
        """Extract module name from file path."""
        # Remove extension and get the name
        module_name = file_path.stem
        
        # For files in subdirectories, consider the directory structure
        relative_path = file_path.relative_to(self.project.project_root)
        parts = list(relative_path.parts[:-1])  # Exclude the filename
        
        # Skip common source directories
        common_src_dirs = {'src', 'lib', 'app', 'source', 'code'}
        filtered_parts = [part for part in parts if part not in common_src_dirs]
        
        if filtered_parts:
            # Create a module path like "package.subpackage.module"
            return '.'.join(filtered_parts + [module_name])
        else:
            return module_name

    def is_test_file(self, file_path: Path) -> bool:
        """Check if a file is a test file based on common patterns."""
        file_str = str(file_path).lower()
        
        # Common test file patterns
        test_patterns = [
            '/test/',
            '/tests/',
            '/testing/',
            'test_',
            '_test.',
            '.test.',
            'spec_',
            '_spec.',
            '.spec.',
        ]
        
        return any(pattern in file_str for pattern in test_patterns)
    
    def is_entry_point_file(self, file_path: Path) -> bool:
        """Check if file is likely an entry point (executable, main file, framework convention)."""
        file_str = str(file_path).lower()
        
        # Entry point patterns (global)
        entry_patterns = [
            '/bin/',           # Executable scripts
            '/features/step_definitions/',  # Cucumber steps (auto-loaded)
            '/features/support/',           # Cucumber support files
            '/vendor/',        # Vendored dependencies (bundled gems, loaded dynamically)
            '/packages/',      # Monorepo packages (each has its own entry points)
        ]
        
        # Check patterns
        if any(pattern in file_str for pattern in entry_patterns):
            return True
        
        # Check if it's named like a main entry point
        file_name = file_path.name.lower()
        if file_name in ('main.py', 'main.rb', 'main.js', 'main.ts', 'main.java', 
                         'index.py', 'index.rb', 'index.js', 'index.ts',
                         'cli.py', 'cli.rb', 'cli.js', 'cli.ts',
                         '__main__.py', 'app.py', 'app.rb', 'server.py', 'server.rb'):
            return True
        
        # Language-specific entry point detection
        ext = file_path.suffix.lower()
        if self._is_language_specific_entry_point(file_path, ext):
            return True
        
        # Check if file name matches project name (common entry point pattern)
        file_stem = file_path.stem.lower()
        
        # Handle both string and Path objects for project_root
        if isinstance(self.project.project_root, Path):
            project_root_name = self.project.project_root.name.lower()
        else:
            project_root_name = Path(self.project.project_root).name.lower()
        
        # Remove common prefixes/suffixes to find the core name
        for prefix in ['aws-', 'aws_', 'amazon-', 'amazon_']:
            if project_root_name.startswith(prefix):
                project_root_name = project_root_name[len(prefix):]
                break
        
        # If the file stem contains the project name, it might be an entry point
        if project_root_name in file_stem or file_stem in project_root_name:
            return True
        
        return False
    
    def _is_language_specific_entry_point(self, file_path: Path, ext: str) -> bool:
        """Check language-specific patterns for entry points and non-imported files."""
        file_name = file_path.name.lower()
        file_str = str(file_path).lower()
        
        # Ruby-specific
        if ext == '.rb':
            ruby_entry_patterns = ['winagent', 'register.rb']
            if any(pattern in file_str for pattern in ruby_entry_patterns):
                return True
        
        # JavaScript-specific
        elif ext == '.js':
            # Config files (used by build tools, not imported)
            js_config_patterns = [
                'webpack.config', 'rollup.config', 'vite.config', 'babel.config',
                'jest.config', 'eslint.config', 'prettier.config', 'postcss.config',
                'tailwind.config', 'next.config', 'nuxt.config', 'svelte.config',
                '.config.js'  # Generic config suffix
            ]
            if any(pattern in file_name for pattern in js_config_patterns):
                return True
        
        # TypeScript-specific
        elif ext == '.ts':
            # Declaration files are type definitions, not imported directly
            if file_name.endswith('.d.ts'):
                return True
            # Config files
            ts_config_patterns = [
                'webpack.config', 'rollup.config', 'vite.config',
                'jest.config', 'eslint.config', '.config.ts'
            ]
            if any(pattern in file_name for pattern in ts_config_patterns):
                return True
        
        # Java-specific
        elif ext == '.java':
            # Model/DTO classes in certain paths are often used via reflection
            # (JSON serialization, Eclipse plugin extension points, etc.)
            java_reflection_patterns = [
                '/models/',       # Model/DTO classes
                '/model/',        # Model/DTO classes
                '/dto/',          # Data Transfer Objects
                '/entities/',     # JPA entities
                '/handlers/',     # Eclipse handlers (registered via plugin.xml)
            ]
            if any(pattern in file_str for pattern in java_reflection_patterns):
                return True
        
        return False

    def collect_all_modules(self) -> Dict[str, Path]:
        """Collect all potential modules in the project, excluding test files and entry points."""
        modules = {}
        
        for file in self.project.project_files:
            file_path = Path(file)  # file is already a CachedPath (which inherits from Path)
            
            # Skip test files
            if self.is_test_file(file_path):
                continue
            
            # Skip entry point files (they're meant to be executed, not imported)
            if self.is_entry_point_file(file_path):
                continue
            
            # Check if file is supported
            if is_supported_format(file_path.suffix.lower()):
                module_name = self.get_module_name_from_file(file_path)
                modules[module_name] = file_path
        
        return modules

    def collect_all_imports(self) -> Set[str]:
        """Collect all imported modules across the project using tree-sitter."""
        all_imports = set()
        
        for file in self.project.project_files:
            file_path = Path(file)  # file is already a CachedPath (which inherits from Path)
            
            # Check if file is supported - now including test files since they use modules
            if is_supported_format(file_path.suffix.lower()):
                imports = collect_imports_from_content(file_path)
                all_imports.update(imports)
                
                # Also add all sub-paths of the import
                # For example, if we import "src.core.configuration", 
                # also add "core.configuration" and "configuration"
                for import_name in list(imports):
                    parts = import_name.split('.')
                    for i in range(1, len(parts) + 1):
                        sub_import = '.'.join(parts[-i:])  # Get suffix parts
                        all_imports.add(sub_import)
                    
                    # For Ruby/Unix paths with slashes, also split those
                    if '/' in import_name:
                        slash_parts = import_name.split('/')
                        for i in range(1, len(slash_parts) + 1):
                            sub_import = '/'.join(slash_parts[-i:])
                            all_imports.add(sub_import)
                            # Also add dot-separated version
                            sub_import_dots = '.'.join(slash_parts[-i:])
                            all_imports.add(sub_import_dots)
        
        return all_imports

    def find_unused_modules(self) -> Dict[str, Path]:
        """Find modules that are defined but never imported."""
        all_modules = self.collect_all_modules()
        all_imports = self.collect_all_imports()
        
        unused_modules = {}
        
        for module_name, file_path in all_modules.items():
            # Check if this module is imported in various ways
            is_imported = False
            
            # Check exact match
            if module_name in all_imports:
                is_imported = True
                continue
            
            # Check if any import matches this module
            module_parts = module_name.split('.')
            
            for import_name in all_imports:
                import_parts = import_name.split('.')
                
                # Check if the import ends with our module path
                # For example: "src.core.configuration" should match "core.configuration"
                if len(import_parts) >= len(module_parts):
                    if import_parts[-len(module_parts):] == module_parts:
                        is_imported = True
                        break
                
                # Check if our module path ends with the import
                # For example: "core.configuration" should match "configuration"
                if len(module_parts) >= len(import_parts):
                    if module_parts[-len(import_parts):] == import_parts:
                        is_imported = True
                        break
            
            if not is_imported:
                unused_modules[module_name] = file_path
        
        return unused_modules

    def report(self) -> str:
        """Generate a report of unused modules."""
        unused_modules = self.find_unused_modules()
        
        if not unused_modules:
            return ""
        
        report = f"Found {len(unused_modules)} unused modules:\n\n"
        
        # Group by extension for better organization
        by_extension = {}
        for module_name, file_path in unused_modules.items():
            ext = file_path.suffix.lower()
            if ext not in by_extension:
                by_extension[ext] = []
            by_extension[ext].append((module_name, file_path))
        
        for ext, modules in by_extension.items():
            report += f"\n{ext} modules:\n"
            report += "-" * (len(ext) + 9) + "\n"
            
            for module_name, file_path in sorted(modules):
                relative_path = file_path.relative_to(self.project.project_root)
                report += f"  - {module_name} ({relative_path})\n"
        
        report += f"\nTotal unused modules: {len(unused_modules)}"
        return report
