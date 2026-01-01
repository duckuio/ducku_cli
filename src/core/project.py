from pathlib import Path
import re
from src.core.configuration import parse_ducku_yaml, Configuration
from src.core.documentation import Documentation, Source
from src.helpers.file_system import FileSystemFolder, folders_to_skip

# Common OS root paths (Unix/Linux and Windows) - not project-specific
OS_ROOT_PATHS = [
    "~/", "/usr/", "/opt/", "/bin/", "/mnt", "/sbin/", "/lib/", "/etc/", "/var/", "/tmp/", "/home/", "/root/",
    "/path/to", "/directory/",
    "C:\\", "D:\\", "E:\\", "F:\\", "G:\\", "H:\\", "I:\\", "J:\\", "K:\\", "L:\\", "M:\\",
    "N:\\", "O:\\", "P:\\", "Q:\\", "R:\\", "S:\\", "T:\\", "U:\\", "V:\\", "W:\\", "X:\\", "Y:\\", "Z:\\",
    "C:/", "D:/", "E:/", "F:/", "G:/", "H:/", "I:/", "J:/", "K:/", "L:/", "M:/",
    "N:/", "O:/", "P:/", "Q:/", "R:/", "S:/", "T:/", "U:/", "V:/", "W:/", "X:/", "Y:/", "Z:/"
]

class Project:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.doc_paths: list[Path] = []
        self.documentation: Documentation
        self.config = parse_ducku_yaml(project_root)
        docs_paths_to_ignore = []
        project_paths_to_ignore = []
        if self.config:
            if self.config.documentation_paths:
                for p in self.config.documentation_paths:
                    self.doc_paths.append(self.resolve_path_from_root(p))
            if self.config.documentation_paths_to_ignore:
                for p in self.config.documentation_paths_to_ignore:
                    self.doc_paths.append(self.resolve_path_from_root(p))
            if self.config.code_paths_to_ignore:
                for p in self.config.code_paths_to_ignore:
                    project_paths_to_ignore.append(self.resolve_path_from_root(p))
        self.parallel_entities = []
        
        # Scan filesystem to get all files
        self.fs_folder = FileSystemFolder(project_root, paths_to_skip=project_paths_to_ignore)
        self.project_files = self.fs_folder.get_all_files()
        self.walk_items = self.fs_folder.walk_items
        
        # Automatically detect and add README files to documentation paths
        for file in self.project_files:
            if file.name.startswith('README') and file not in self.doc_paths:
                self.doc_paths.append(file)
        
        self.documentation = Documentation(docs_paths_to_ignore).from_project(self)

    def resolve_path_from_root(self, p: str) -> Path:
        path = Path(p)
        if path.is_absolute():
            return path
        else:
            return self.project_root / path

    def folder_to_skip(self, root, _files=None):
        # _files parameter is kept for backward compatibility but not used
        return Path(root).name in folders_to_skip

    def contains_string(self, string: str, source: Source) -> bool:
        for file in self.project_files:
            if file in self.doc_paths:
                continue
            content = file.read_text()
            if string in content:
                return True
        return False

    def _extract_route_path(self, txt: str) -> str:
        """Extract path from full URL or return path as-is."""
        url_match = re.match(r'https?://[^/]+(/.*)', txt)
        if url_match:
            return url_match.group(1)
        return txt

    def contains_route(self, route: str, source: Source) -> bool:
        """Check if route exists in project, filtering out filesystem paths."""
        route_path = self._extract_route_path(route)
        
        # Exclude file extensions - these are files, not routes
        file_extensions = ['.md', '.txt', '.html', '.htm', '.xml', '.json', '.yaml', '.yml', 
                          '.py', '.js', '.ts', '.go', '.java', '.rb', '.css', '.scss']
        if any(route_path.lower().endswith(ext) for ext in file_extensions):
            return True  # Skip - it's a file, not a missing route
        
        # Exclude OS/filesystem path prefixes
        if any(route_path.startswith(prefix) for prefix in OS_ROOT_PATHS):
            return True  # Skip - it's a filesystem path, not a route
        
        # Check if first path segment is an existing folder in project root
        if route_path.startswith('/'):
            parts = route_path.strip('/').split('/')
            if parts and parts[0]:
                first_segment = parts[0]
                potential_folder = Path(self.project_root) / first_segment
                if potential_folder.exists() and potential_folder.is_dir():
                    return True  # Skip - first segment matches project folder
        
        # Now check if the route actually exists in the codebase
        return self.contains_string(route_path, source)

    def contains_path(self, path: str, source: Source) -> bool:
        # sometimes files appear as examples - skip placeholder-like filenames only
        # Only skip if the filename (not directory) contains these patterns
        MOCK_FILENAME_PATTERNS = [
            "hello", "my_", "path_to", "xxx", "yyy", "zzz", "log_", "log.", "logs.",
            "myfile", "yourfile"  # common placeholder filenames in docs
        ]
        # Skip paths containing these placeholder directory names
        MOCK_DIR_PATTERNS = [
            "/some-dir/", "/some_dir/", "/somedir/",  # generic placeholder dirs
        ]
        # Skip only if the path is JUST an example placeholder (not a real example directory)
        MOCK_PATH_PATTERNS = [
            "/example.py", "/example.js", "/example.ts",  # example.ext files
            "/sample.py", "/sample.js", "/sample.ts",     # sample.ext files
        ]
        # Skip common OS root paths
        if any(path.startswith(prefix) for prefix in OS_ROOT_PATHS):
            return False

        cand = Path(path.lstrip("/"))  # normalize absolute-like paths
        filename = cand.name.lower()
        # Only skip mock patterns in the filename, not in directory names
        if any(excl in filename for excl in MOCK_FILENAME_PATTERNS):
            return False
        # Skip paths with placeholder directory names
        path_lower = path.lower()
        if any(pattern in path_lower for pattern in MOCK_DIR_PATTERNS):
            return False
        # Skip explicit example/sample placeholder files
        if any(path_lower.endswith(pattern) for pattern in MOCK_PATH_PATTERNS):
            return False
        if len(cand.parts) == 1:  # single/relative file
            return self.contains_file(cand.name, source)  # Use normalized filename

        # Check absolute paths
        # if Path(path).is_absolute():
        #     return Path(path).exists()

        # Check relative to source document's directory first
        source_root = source.get_root()
        if source_root:
            source_target = (source_root / cand).resolve(strict=False)
            if source_target.exists():
                return True

        # Check relative to project root
        root = self.project_root
        target = (root / cand).resolve(strict=False)
        if target.exists():
            return True
        
        # Check relative to each documentation path
        for doc_path in self.doc_paths:
            if doc_path.is_dir():
                doc_target = (doc_path / cand).resolve(strict=False)
                if doc_target.exists():
                    return True
            elif doc_path.is_file():
                # If doc_path is a file, check relative to its parent directory
                doc_target = (doc_path.parent / cand).resolve(strict=False)
                if doc_target.exists():
                    return True
        
        return False
    
    # try to find anywhere in the project
    def contains_file(self, file_name: str, source: Source) -> bool:
        # First check relative to source document's directory
        source_root = source.get_root()
        if source_root:
            source_file = source_root / file_name
            if source_file.exists() and source_file.is_file():
                return True
        
        # Then check in all project files
        for file in self.project_files:
            if file.name == file_name:
                return True
        return False
