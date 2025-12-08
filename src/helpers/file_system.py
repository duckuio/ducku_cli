import os
import sys
from pathlib import Path

# Folders to skip during project walking
folders_to_skip = [
    "node_modules", ".venv", "venv", "virtualenv", ".git", "build", 
    ".coverage", ".pytest_cache", ".gradle", ".next", ".nuxt", "coverage",
    ".cache", "jspm_packages", "bower_components",
    "dist", "out", "target", "__pycache__", ".idea", ".vscode",
    ".terraform", ".serverless", ".mypy_cache", ".ruff_cache", ".tox", ".eggs", ".docusaurus"
]

# Files to skip during project walking
files_to_skip = [
    "__init__.py",
    "package-lock.json",
    "pdm.lock",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "Pipfile.lock",
    "Gemfile.lock",
    "composer.lock",
    "Cargo.lock",
    "go.sum",
    ".DS_Store",
    ".ducku.yaml"
]

# Cache for file contents
cached_files = {}
cache_bytes = 0
CACHE_LIMIT = 200 * 1024 * 1024


class CachedPath(Path):
    """Path subclass that caches file contents in memory to avoid repeated disk reads."""
    
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



class WalkItem:
    """Represents a single directory level during filesystem traversal."""
    
    def __init__(self, root: Path, dirs: list[str], files: list[CachedPath], relative_root: Path):
        self.root = root
        self.dirs = dirs  # Already filtered
        self.files = files  # Already filtered and converted to CachedPath
        self.relative_root = relative_root


class FileSystemFolder:
    """Manages filesystem traversal and filtering for a project folder."""
    
    def __init__(self, folder_path: str | Path, paths_to_skip: list[Path] | None = None):
        """
        Initialize the filesystem folder scanner.
        
        Args:
            folder_path: Root directory to traverse
            paths_to_skip: List of paths (files or directories) to exclude
        """
        self.folder_path = Path(folder_path)
        self.paths_to_skip = [Path(p).resolve() for p in paths_to_skip] if paths_to_skip is not None else []
        self.walk_items: list[WalkItem] = []
        
    def get_all_files(self) -> list[CachedPath]:
        """
        Get all file paths within the folder recursively, with filtering and caching.
        During traversal, populates self.walk_items with WalkItem instances.
        
        Returns:
            List of CachedPath objects for all files (excluding skipped folders/files)
        """
        all_files = []
        self.walk_items = []  # Reset walk items

        for root, dirs, files in os.walk(self.folder_path):
            root_path = Path(root).resolve()
            
            # Check if current directory or any of its parents should be skipped
            should_skip = False
            for skip_path in self.paths_to_skip:
                try:
                    # Check if root_path is skip_path or a subdirectory of skip_path
                    root_path.relative_to(skip_path)
                    should_skip = True
                    break
                except ValueError:
                    # root_path is not relative to skip_path, continue checking
                    continue
            
            if should_skip:
                # Clear dirs to prevent os.walk from descending into subdirectories
                dirs[:] = []
                continue
            
            # Filter out directories that should be skipped (modifies in-place)
            filtered_dirs = [d for d in dirs if d not in folders_to_skip]
            dirs[:] = filtered_dirs

            # Skip if the current directory itself should be skipped
            if Path(root).name in folders_to_skip:
                continue
            
            # Process files in current directory
            walk_item_files = []
            for file in files:
                if Path(file).name in files_to_skip:
                    continue
                
                full_path = Path(root) / file
                
                # Check if this specific file should be skipped
                full_path_resolved = full_path.resolve()
                if full_path_resolved in self.paths_to_skip:
                    continue
                
                cached_file = CachedPath(full_path)
                all_files.append(cached_file)
                walk_item_files.append(cached_file)
            
            # Create WalkItem for this directory level
            relative_root = Path(root).relative_to(self.folder_path)
            walk_item = WalkItem(
                root=Path(root),
                dirs=filtered_dirs,
                files=walk_item_files,
                relative_root=relative_root
            )
            self.walk_items.append(walk_item)
        
        return all_files


