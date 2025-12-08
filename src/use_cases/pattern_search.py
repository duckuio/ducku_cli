from src.core.base_usecase import BaseUseCase
from src.core.documentation import Source
from src.core.project import Project
from dataclasses import dataclass
from src.core.search_pattern import SearchPattern

exts = (
    r'(?:ya?ml|jsonl?|toml|ini|cfg|conf|properties|props|xml|html?|xhtml|css|less|scss|'
    r'js|mjs|cjs|jsx|ts|tsx|py|ipynb|rb|php|java|kt|kts|scala|go|rs|c|h|hh|hpp|hxx|cc|cxx|'
    r'cpp|cs|swift|m|mm|pl|pm|sh|bash|zsh|ps1|psm1|bat|cmd|lua|r|jl|sql|csv|tsv|parquet|'
    r'orc|avro|proto|thrift|graphql|gql|md|markdown|adoc|rst|log|txt)'
)

all_patterns = [
    SearchPattern(
        "Unix path",
        rf'(?:(?<=^)|(?<=\s)|(?<=[\(\[\{{"\'`]))'
        rf'(?:\.{{0,2}}/|~/|/(?!/))(?![^\s\'"\)\]>\{{\}}<>]*//)'
        rf'[^\s\'"\)\]>\{{\}}<>]+\.{exts}\b',
        "contains_path",
        ["not_mocked"]
    ),
    SearchPattern(
        "Windows path",
        rf'(?:(?<=^)|(?<=\s)|(?<=[\(\[\{{"\'`]))'
        rf'(?:[A-Za-z]:\\|\\\\)'
        rf'[^\s\'"\)\]>\{{\}}<>]+\.{exts}\b',
        "contains_path",
        ["not_mocked"]
    ),
    SearchPattern(
        "Filename",
        rf'(?<!\w)(?<!://)[A-Za-z0-9._-]+\.{exts}\b',
        "contains_file",
        ["file_not_in_url", "file_not_in_exclusions", "file_is_not_path", "file_correct_context"]
    ),
    SearchPattern(
        "Port Number", # TCP ports (0-65535) with port context check
        r'(?:(?<=^)|(?<=[ :]))(?:0|[1-9]\d{0,4})(?![.\w,_-])',
        "contains_string",
        ["is_port_context"]
    ),
    SearchPattern(
        "Environment variable", # env var is just any capital case word, but must be in the right context and contain "_". Without underscore it would be too many false positives
        r'(?<!\w)(?:[A-Z][A-Z0-9_]{2,63})\b',
        "contains_string",
        ["is_env_var_context", "contains_"]
    ),
    SearchPattern(
        "HTTP Route",
        r'(?:(?<=^)|(?<=\s)|(?<=[\(\[\{{"\'`]))'
        r'(?:'
        r'(?:https?://)?localhost(?::\d+)?/(?![/*])'  # localhost URLs with optional protocol and port
        r'|'
        r'/(?![/*])'  # relative paths starting with /
        r')'
        r'(?:[A-Za-z0-9._~!$&\'()*+,;=:@%/-]|{{|}}|<|>)+'
        r'(?:\?(?:[A-Za-z0-9._~!$&\'()*+,;=:@%/?-]|{{|}}|<|>)+)?'
        r'(?:#(?:[A-Za-z0-9._~!$&\'()*+,;=:@%/?-]|{{|}}|<|>)+)?',
        "contains_string",
        ["is_route_context"]
    ),
]

def get_patterns_yaml_list() -> str:
    return "\n".join([f"  - {p.name}" for p in all_patterns])


@dataclass
class Artifact:
    pattern: SearchPattern
    match: str  # pattern match
    source: Source
        
class PatternSearch(BaseUseCase):

    def __init__(self, project: Project):
        super().__init__(project)
        self.name = "pattern_search"

    def collect_docs_artifacts(self, patterns: list[SearchPattern]) -> list[Artifact]:
        artefacts = []
        cache = {}
        for pattern in patterns:
            if self.project.config.use_case_options.pattern_search.disabled_patterns and pattern.name in self.project.config.use_case_options.pattern_search.disabled_patterns:
                continue
            for dp in self.project.documentation.doc_parts:
                try:
                    # Skip binary files or files with non-text content
                    content = dp.read()
                    if '\0' in content or sum(1 for c in content[:1000] if ord(c) < 32 and c not in '\n\r\t') > 30:
                        print("WAS SKIPPED")
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

    def report(self):
        result = ""

        artifacts = self.collect_docs_artifacts(all_patterns)
        # handing everything that was found in docs
        for artifact in artifacts:
            handler = getattr(self.project, artifact.pattern.project_handler)
            if not handler(artifact.match, artifact.source):
                result += f"{artifact.pattern.name} '{artifact.match}' found in {artifact.source.get_source_identifier()}, but nowhere in the project. Probably outdated artifact\n"

        return result