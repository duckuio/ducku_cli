import os
import sys
from pathlib import Path
from src.core.configuration import parse_documentory_yaml
from src.core.documentation import Documentation, Source

folders_to_skip = [
    "node_modules", ".venv", "venv", "virtualenv", ".git", "build", 
    ".coverage", ".pytest_cache", ".gradle", ".next", ".nuxt", "coverage",
    ".cache", "jspm_packages", "bower_components",
    "dist", "out", "target", "__pycache__", ".idea", ".vscode",
    ".terraform", ".serverless", ".mypy_cache", ".ruff_cache", ".tox", ".eggs"
]

files_to_skip = [
    "package-lock.json",
    "pdm.lock",
    "__init__.py",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "Pipfile.lock",
    "Gemfile.lock",
    "composer.lock",
    "Cargo.lock",
    "go.sum",
    ".DS_Store"
]

cached_files = {}
cache_bytes = 0
CACHE_LIMIT = 200 * 1024 * 1024

class WalkItem:
    def __init__(self, project, root, dirs, files):
        self.project = project
        self.root = root
        # Filter out directories that should be skipped
        self.dirs = [d for d in dirs if d not in folders_to_skip]
        self.files = []
        for file in files:
            if Path(file).name in files_to_skip:
                continue
            full_path = root + os.sep + file
            f = CachedPath(full_path)
            # @TODO extend how documentation is collected
            if f.name.startswith('README'):
                project.doc_paths.append(f)
            self.files.append(f)
        self.relative_root = Path(root).relative_to(project.project_root)

class Project:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.doc_paths: list[Path] = []
        self.documentation: Documentation
        self.config = parse_documentory_yaml(project_root)
        if self.config and "documentation_paths" in self.config:
            for p in self.config["documentation_paths"]:
                if Path(p).is_absolute():
                    self.doc_paths.append(Path(p))
                else:
                    self.doc_paths.append(Path(str(project_root) / Path(p)))
        self.parallel_entities = []
        self.walk_items = []
        for root, dirs, files in os.walk(project_root):
            # Modify dirs in-place to skip folders in folders_to_skip
            # This prevents os.walk from descending into these directories
            dirs[:] = [d for d in dirs if d not in folders_to_skip]
            
            if not self.folder_to_skip(root, files):
                self.walk_items.append(WalkItem(self, root, dirs, files))
        self.documentation = Documentation().from_project(self)

    def folder_to_skip(self, root, _files=None):
        # _files parameter is kept for backward compatibility but not used
        return Path(root).name in folders_to_skip

    def contains_string(self, artefact: str) -> bool:
        for walk_item in self.walk_items:
            for file in walk_item.files:
                content = file.read_text()
                if artefact in content:
                    #print("Found in file", file)
                    return True
        return False

    def contains_path(self, artifact: str, source: Source) -> bool:
        # sometimes files appear as examples
        MOCKS_TO_SKIP = [
            "hello", "my", "input", "output", "data", "file", "files", "path", "xxx", "yyy", "zzz", "example", "sample", "test", "demo", "log"
        ]
        # Skip common OS root paths (Unix/Linux and Windows)
        os_root_paths = [
            "~/","/usr/", "/opt/", "/bin/", "/mnt", "/sbin/", "/lib/", "/etc/", "/var/", "/tmp/", "/home/", "/root/",
            "C:\\", "D:\\", "E:\\", "F:\\", "G:\\", "H:\\", "I:\\", "J:\\", "K:\\", "L:\\", "M:\\",
            "N:\\", "O:\\", "P:\\", "Q:\\", "R:\\", "S:\\", "T:\\", "U:\\", "V:\\", "W:\\", "X:\\", "Y:\\", "Z:\\",
            "C:/", "D:/", "E:/", "F:/", "G:/", "H:/", "I:/", "J:/", "K:/", "L:/", "M:/",
            "N:/", "O:/", "P:/", "Q:/", "R:/", "S:/", "T:/", "U:/", "V:/", "W:/", "X:/", "Y:/", "Z:/"
        ]
        if any(artifact.startswith(path) for path in os_root_paths):
            return False
            
        cand = Path(artifact.lstrip("/"))  # normalize absolute-like paths
        if any(excl in str(cand).lower() for excl in MOCKS_TO_SKIP):
            return False
        if len(cand.parts) == 1:  # single/relative file
            return self.contains_file(str(cand))
        source_root = source.get_root()
        if source_root:
            root = Path(source_root).resolve(strict=False)
            target = (root / cand).resolve(strict=False)
            if target.exists():
                return True
            else:
                # try relative to project root
                target = (self.project_root / cand).resolve(strict=False)
                if target.exists():
                    return True
                return False
        else:
            root = self.project_root
            target = (root / cand).resolve(strict=False)
            ex = target.exists()
            return ex
    
    # try to find anywhere in the project
    def contains_file(self, artifact: str) -> bool:
        for walk_item in self.walk_items:
            for file in walk_item.files:
                if file.name == artifact:
                    return True
        return False

class CachedPath(Path):
    def __init__(self, *args: str | os.PathLike[str]) -> None:
        super().__init__(*args)

    def read_text(self, *args, **kwargs):
        global cache_bytes
        abs_path = str(self.absolute())
        if abs_path in cached_files:
            return cached_files[abs_path]
        try:
            content = super().read_text(*args, **kwargs)
            size = sys.getsizeof(content)
            if cache_bytes + size <= CACHE_LIMIT:
                cached_files[abs_path] = content
                cache_bytes += size
            return content
        except UnicodeDecodeError:
            # Try with a different encoding or use errors='replace'
            kwargs['errors'] = 'replace'
            content = super().read_text(*args, **kwargs)
            size = sys.getsizeof(content)
            if cache_bytes + size <= CACHE_LIMIT:
                cached_files[abs_path] = content
                cache_bytes += size
            return content