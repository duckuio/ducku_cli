"""
Dispatcher module for language-specific code analysis.
Routes analysis requests to the appropriate language analyzer.
"""

from pathlib import Path
from typing import Set, Optional

from src.core.code.language import LanguageAnalyzer
from src.core.code.languages.python import PythonAnalyzer
from src.core.code.languages.javascript import JavaScriptAnalyzer
from src.core.code.languages.typescript import TypeScriptAnalyzer
from src.core.code.languages.java import JavaAnalyzer
from src.core.code.languages.go import GoAnalyzer
from src.core.code.languages.ruby import RubyAnalyzer


# Supported file extensions mapped to language names
SUPPORTED_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".go": "go",
    ".rb": "ruby",
}

# Language analyzers cache (singleton instances)
_ANALYZERS: dict[str, LanguageAnalyzer] = {}


def _get_analyzer(lang_name: str) -> Optional[LanguageAnalyzer]:
    """Get or create a language analyzer for the given language."""
    if lang_name in _ANALYZERS:
        return _ANALYZERS[lang_name]
    
    # Create analyzer based on language
    if lang_name == "python":
        _ANALYZERS[lang_name] = PythonAnalyzer()
    elif lang_name == "javascript":
        _ANALYZERS[lang_name] = JavaScriptAnalyzer()
    elif lang_name == "typescript":
        _ANALYZERS[lang_name] = TypeScriptAnalyzer(use_tsx=False)
    elif lang_name == "tsx":
        _ANALYZERS[lang_name] = TypeScriptAnalyzer(use_tsx=True)
    elif lang_name == "java":
        _ANALYZERS[lang_name] = JavaAnalyzer()
    elif lang_name == "go":
        _ANALYZERS[lang_name] = GoAnalyzer()
    elif lang_name == "ruby":
        _ANALYZERS[lang_name] = RubyAnalyzer()
    # Rust and PHP not yet implemented
    else:
        return None
    
    return _ANALYZERS[lang_name]


def is_supported_format(extension: str) -> bool:
    """Check if a file extension is supported."""
    return extension in SUPPORTED_EXTENSIONS


def collect_code_entities_from_content(file_path: Path, entities: list) -> None:
    """
    Collect code entities from a source file.
    
    Args:
        file_path: Path to the source file
        entities: List to append EntitiesContainer objects to
    """
    suffix = file_path.suffix.lower()
    lang_name = SUPPORTED_EXTENSIONS.get(suffix)
    if not lang_name:
        return
    
    analyzer = _get_analyzer(lang_name)
    if analyzer:
        analyzer.collect_entities(file_path, entities)


def collect_imports_from_content(file_path: Path) -> Set[str]:
    """
    Extract all import module names from a source file.
    
    Args:
        file_path: Path to the source file
        
    Returns:
        Set of module names that are imported
    """
    suffix = file_path.suffix.lower()
    lang_name = SUPPORTED_EXTENSIONS.get(suffix)
    if not lang_name:
        return set()
    
    # Get language analyzer
    analyzer = _get_analyzer(lang_name)
    if analyzer:
        return analyzer.collect_imports(file_path)
    
    # No analyzer available for this language
    return set()
