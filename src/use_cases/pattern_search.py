from src.core.documentation import Source
from src.core.search_pattern import SearchPattern

exts = (
    r'(?:ya?ml|jsonl?|toml|ini|cfg|conf|properties|props|xml|html?|xhtml|css|less|scss|'
    r'js|mjs|cjs|jsx|ts|tsx|py|ipynb|rb|php|java|kt|kts|scala|go|rs|c|h|hh|hpp|hxx|cc|cxx|'
    r'cpp|cs|swift|m|mm|pl|pm|sh|bash|zsh|ps1|psm1|bat|cmd|lua|r|jl|sql|csv|tsv|parquet|'
    r'orc|avro|proto|thrift|graphql|gql|md|markdown|adoc|rst|log|txt)'
)

path_patterns = [
    # @TODO things like ./file.txt can be prepared over cd PATH.
    SearchPattern(
        "Unix path",
        rf'(?:(?<=^)|(?<=\s)|(?<=[\(\[\{{"\'`]))'
        rf'(?:\.{{0,2}}/|~/|/(?!/))(?![^\s\'"\)\]>\{{\}}<>]*//)'
        rf'[^\s\'"\)\]>\{{\}}<>]+\.{exts}\b',
        ["not_mocked"]
    ),
    SearchPattern(
        "Windows path",
        rf'(?:(?<=^)|(?<=\s)|(?<=[\(\[\{{"\'`]))'
        rf'(?:[A-Za-z]:\\|\\\\)'
        rf'[^\s\'"\)\]>\{{\}}<>]+\.{exts}\b'
    )
]

files_patterns = [
        SearchPattern(
        "Filename",
        rf'(?<!\w)(?<!://)[A-Za-z0-9._-]+\.{exts}\b',
        ["file_not_in_url", "file_not_in_exclusions", "file_is_not_path"],
    ),
]

string_patterns = [
    SearchPattern("TCP port", r'(?:(?<=^)|(?<=[ :]))(?:0|[1-9]\d{0,4})(?![.\w-])', ["is_port_context"]), # TCP ports (0-65535) with port context check
    # env var is just any capital case word, but must be in the right context and contain "_". Without underscore it would be too many false positives
    SearchPattern("Environment variable", r'(?<!\w)(?:[A-Z][A-Z0-9_]{2,63})\b', ["is_env_var_context", "contains_"]), # Environment variables (minimum 3 chars to avoid false positives)
]

class Artifact:
    def __init__(self, pattern: SearchPattern, match: str, source: Source):
        self.pattern: SearchPattern = pattern
        self.match: str = match # pattern match
        self.source: Source = source

def collect_docs_artifacts(p, patterns: list[SearchPattern]) -> list[Artifact]:
    artefacts = []
    cache = {}
    for pattern in patterns:
        for dp in p.documentation.doc_parts:
            try:
                # Skip binary files or files with non-text content
                content = dp.read()
                if '\0' in content or sum(1 for c in content[:1000] if ord(c) < 32 and c not in '\n\r\t') > 30:
                    continue
                
                matches = pattern.find_all(dp)
                for m in matches:
                    match = m.group(0)
                    # Skip artifacts that contain control characters
                    if sum(1 for c in match if ord(c) < 32 and c not in '\n\r\t') > 0:
                        continue
                    if match not in cache: # don't collect duplicates
                        cache[match] = Artifact(
                            pattern=pattern,
                            match=match,
                            source=dp.source,
                        )
                        artefacts.append(cache[match])
                    cache[match] = True
            except (UnicodeError, ValueError, OSError):
                # Skip files that can't be processed
                continue
    return artefacts

def report(p):
    result = ""

    artifacts = collect_docs_artifacts(p, string_patterns)
    for artifact in artifacts:
        if not p.contains_string(artifact.match):
            result += f"String '{artifact.match}' found in {artifact.source.get_source_identifier()}, but nowhere in the project. Probably outdated artifact\n"

    artifacts = collect_docs_artifacts(p, path_patterns)
    for artifact in artifacts:
        found = p.contains_path(artifact.match, artifact.source)
        if not found:
            result += f"Path '{artifact.match}' found in {artifact.source.get_source_identifier()}, but nowhere in the project. Probably outdated artifact\n"

    artifacts = collect_docs_artifacts(p, files_patterns)
    for artifact in artifacts:
        found = p.contains_file(artifact.match)
        if not found:
            result += f"File '{artifact.match}' found in {artifact.source.get_source_identifier()}, but nowhere in the project. Probably outdated artifact\n"
    return result