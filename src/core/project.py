from pathlib import Path
from src.core.configuration import parse_ducku_yaml, Configuration
from src.core.documentation import Documentation, Source
from src.helpers.file_system import FileSystemFolder, folders_to_skip

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

    def contains_path(self, path: str, source: Source) -> bool:
        # sometimes files appear as examples
        MOCKS_TO_SKIP = [
            "hello", "my_", "path_to", "xxx", "yyy", "zzz", "example", "sample", "log_", "log.", "logs."
        ]
        # Skip common OS root paths (Unix/Linux and Windows)
        os_root_paths = [
            "~/","/usr/", "/opt/", "/bin/", "/mnt", "/sbin/", "/lib/", "/etc/", "/var/", "/tmp/", "/home/", "/root/",
            "C:\\", "D:\\", "E:\\", "F:\\", "G:\\", "H:\\", "I:\\", "J:\\", "K:\\", "L:\\", "M:\\",
            "N:\\", "O:\\", "P:\\", "Q:\\", "R:\\", "S:\\", "T:\\", "U:\\", "V:\\", "W:\\", "X:\\", "Y:\\", "Z:\\",
            "C:/", "D:/", "E:/", "F:/", "G:/", "H:/", "I:/", "J:/", "K:/", "L:/", "M:/",
            "N:/", "O:/", "P:/", "Q:/", "R:/", "S:/", "T:/", "U:/", "V:/", "W:/", "X:/", "Y:/", "Z:/"
        ]
        if any(path.startswith(root_path) for root_path in os_root_paths):
            return False

        cand = Path(path.lstrip("/"))  # normalize absolute-like paths
        if any(excl in str(cand).lower() for excl in MOCKS_TO_SKIP):
            return False
        if len(cand.parts) == 1:  # single/relative file
            return self.contains_file(path, source)

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
