import re
from src.core.documentation import DocPart

class SearchPattern:
    def __init__(self, name: str, regexp: str, project_handler, postfilters: list[str] = []):
        """
        Args:
            name (str): The name of the pattern.
            regexp (str): Regular expression pattern to compile.
            project_handler: Project class member function to handle the pattern
            postfilters (list[str], optional): List of postfilter functions to apply. They are SearchPattern class members. 
        """
        self.postfilters = postfilters
        self.regexp = re.compile(regexp)
        self.name = name
        self.project_handler = project_handler

    def _extract_line_context(self, text: str, match_start: int, match_end: int) -> str:
        # Find the start of the line
        line_start = text.rfind('\n', 0, match_start)
        if line_start == -1:
            line_start = 0
        else:
            line_start += 1  # Skip the newline character
        
        # Find the end of the line
        line_end = text.find('\n', match_end)
        if line_end == -1:
            line_end = len(text)
        
        return text[line_start:line_end]

    def contains_(self, m: re.Match, context: str) -> bool:
        return '_' in m.group(0)

    # Postifilters should return true to keep the match, False to discard it
    def is_in(self, ds: DocPart) -> re.Match | None:
        text = ds.read()
        for m in self.regexp.finditer(text):
            # Extract the entire line containing the match
            context = self._extract_line_context(text, m.start(), m.end())
            
            if all(getattr(self, pf)(m, context) for pf in self.postfilters):
                return m
        return None
        
    def find_all(self, ds: DocPart) -> list[re.Match]:
        """Find all matches in the document part that also pass the postfilters"""
        matches = []
        text = ds.read()
        for m in self.regexp.finditer(text):
            # Extract the entire line containing the match
            context = self._extract_line_context(text, m.start(), m.end())
            
            if all(getattr(self, pf)(m, context) for pf in self.postfilters):
                matches.append(m)
        return matches

    def file_is_not_path(self, m: re.Match, context: str) -> bool:
        txt = m.group(0).lower()
        return not ("/" in txt or "\\" in txt)

    def file_not_in_url(self, m: re.Match, context: str) -> bool:
        return not ("://" in context)
    
    def file_not_in_exclusions(self, m: re.Match, context: str) -> bool:
        exclusions = ["next.js", "vue.js", "nuxt.js", "react.js", "angular.js", "svelte.js", "ember.js",
    "django.py", "flask.py", "rails.rb", "sinatra.rb", "spring.java",
    "laravel.php", "symfony.php",
    "dotnet.cs", "asp.net"]
        txt = m.group(0).lower()
        return not any(ex in txt for ex in exclusions)
    
    def file_correct_context(self, m: re.Match, context: str) -> bool:
        indicators = ['create', 'save']
        return not self.are_indicators_in_context(indicators, m, context)
    

    def is_route_context(self, m: re.Match, context: str) -> bool:
        route_indicators = ['route', 'endpoint', 'url', 'request', 'get', 'post', 'put', 'delete', 'patch', 'curl']
        return self.are_indicators_in_context(route_indicators, m, context)

    def not_mocked(self, m: re.Match, context: str) -> bool:
        common_mocked_parts = ["path", "to"]
        txt = m.group(0)
        sep = "/" if "/" in txt else "\\"
        parts = txt.split(sep)
        return not any(p in common_mocked_parts for p in parts)

    # indicators is a list of strings to look for in the context in lower case
    def are_indicators_in_context(self, indicators, m, context: str | None = None):
        # Use provided context or extract the full line from the match
        if context is None:
            context = self._extract_line_context(m.string, m.start(), m.end())
        
        context_lower = context.lower()
        return any(indicator.lower() in context_lower for indicator in indicators)

    def is_port_context(self, m: re.Match, context: str | None = None) -> bool:
        # Use provided context or extract the full line from the match
        if context is None:
            context = self._extract_line_context(m.string, m.start(), m.end())
        
        context_lower = context.lower()
        
        # Strong port indicators (these are good signs it's actually a port)
        strong_indicators = ['port ', ':' + m.group(0), 'localhost:', '127.0.0.1:', 
                           'listen', 'socket', 'bind', 'connection', 'address', 'tcp', 'udp']
        
        # Check for strong indicators first
        if any(indicator in context_lower for indicator in strong_indicators):
            return True
            
        # Weaker indicators that need additional validation
        weak_indicators = ['port', 'http', 'server']
        
        # For weak indicators, make sure they're not part of compound words
        for indicator in weak_indicators:
            if indicator in context_lower:
                # Find the position of the indicator
                indicator_pos = context_lower.find(indicator)
                # Check if it's a standalone word (not part of "portkey", "support", etc.)
                before_char = context_lower[indicator_pos - 1] if indicator_pos > 0 else ' '
                after_pos = indicator_pos + len(indicator)
                after_char = context_lower[after_pos] if after_pos < len(context_lower) else ' '
                
                # It's a standalone word if surrounded by non-alphanumeric characters
                if not before_char.isalnum() and not after_char.isalnum():
                    return True
        
        return False
    
    def is_env_var_context(self, m: re.Match, context: str) -> bool:
        env_indicators = ['variable', 'environment', 'env', 'var', 'envvar', 'env_var']
        return self.are_indicators_in_context(env_indicators, m, context)
    
    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name
