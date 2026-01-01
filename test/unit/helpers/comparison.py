from src.helpers.comparison import fuzzy_intersection, string_similar, token_similar, tokenize_string

def test_tokenize_string():
    assert tokenize_string("simple test") == ["simple", "test"], "Tokenize by space"
    assert tokenize_string("he/him") == ["he", "him"], "Tokenize by slash"
    assert tokenize_string("127.0.0.1") == ["127", "0", "0", "1"], "Tokenize by dot"
    assert tokenize_string("ForgetMeNot") == ["Forget", "Me", "Not"], "Tokenize camel case"
    assert tokenize_string("Spell-Checker") == ["Spell-Checker"]

# def test_token_similar():
#     assert token_similar("spell", "spellcheck") >= 0.5, "Similar tokens should have high similarity"
#     assert token_similar("checker", "spellcheck") >= 0.8, "Similar tokens should have high similarity"
    


def test_string_similar():
    
    # Test partial token match
    score = string_similar("user profile settings", "user profile", True)
    assert score > 0.5, "2 out of 3 tokens exact match, should be legit"
    
    # Test similar tokens (fuzzy match within tokens)
    score = string_similar("users", "user", True)
    assert score >= 0.7, "Similar tokens should match with high score"
    
    # Test no match
    score = string_similar("apple", "orange")
    assert score == 0, "No token overlap should give 0"
    
    # Test empty strings
    score = string_similar("", "test")
    assert score == 0, "Empty string should give 0"
    
    # Test case insensitivity
    score = string_similar("User Profile", "user profile", True)
    assert score > 0.8, "Case should not matter. Because of rarity boost can be less that 1"
    
    # Test with special characters and normalization
    score = string_similar("user_profile_settings", "user profile settings")
    assert score >= 0.8, "Normalization should handle hyphens and underscores"
    
    # Test complex multi-token similarity
    score = string_similar("pattern search module", "pattern searching modules")
    assert score >= 0.66, "Similar multi-token strings should have reasonable similarity"

    # Test token similarity path (ts > 0)
    score = string_similar("user profile", "profile user")
    assert score < 0.78, "Exact tokens, different positions, penalty. Also frequent"
    
    score = string_similar("user settings", "user profile", True)
    assert score < 0.67, "Partial token overlap should use token similarity. Also frequent"
    
    # Test fuzzy fallback (ts == 0, no token overlap)
    score = string_similar("apple", "aple")
    assert score >= 0.5, "Similar missplelled strings, should still match reasonably"
    
    score = string_similar("test", "testing")
    assert score > 0.5, "Similar strings should have reasonable fuzzy score"
    
    # Test case insensitivity
    score = string_similar("User", "user")
    assert score >= 0.9, "Case should not matter"
    
    # Test normalization
    score = string_similar("user profile", "user_profile")
    assert score >= 0.8, "Normalization should handle separators"
    
    # False positives - strings that should NOT match highly
    score = string_similar("user", "server")
    assert score <= 0.6, "Different words should have low similarity"
    
    score = string_similar("apple", "orange")
    assert score < 0.4, "Completely different words should have very low similarity"
    
    score = string_similar("pattern", "parent")
    assert score < 0.75, "Similar-looking but different words should not match highly"
    
    score = string_similar("authentication", "authorization")
    assert score < 0.75, "Similar-sounding but different terms should not match highly"
    
    # Edge cases
    score = string_similar("", "test")
    assert score == 0, "Empty string should give 0"
    
    score = string_similar("a", "b")
    assert score == 0, "Single different characters should give 0"
    
    # Multi-word combinations
    score = string_similar("database connection", "database connector")
    assert score >= 0.7, "Similar phrases should match reasonably"
    
    score = string_similar("create user account", "delete user profile")
    assert score < 0.6, "Different actions should not match highly despite shared words"

    score = string_similar("list_item1", "ordered_list")
    assert score <= 0.5, "Similar multi-token strings should have reasonable similarity"

    score = string_similar("unused module detection beta", "unused modules")
    assert score >= 0.5, "Different concepts should not match highly"

    score = string_similar("Pattern Search", "1. Pattern Search 🔍")
    assert score >= 0.8, "Should be similar despite extra characters"

    score = string_similar("partial_lists", "3. Partial Match Detection 🎯", True)
    assert score >= 0.5, "Should be similar despite extra characters"

    score = string_similar("fail_on_issues items", "False items")
    assert score < 0.5, "Partially similar but don't actually match"

    score = string_similar("registry", "entry")
    assert score < 0.5, "Mid-word substring matches should not count highly"

    score = string_similar("Configuration", "🤝 Contributing items")
    assert score < 0.5, "Different concepts should not match highly"

    # now "2. Spell-Checker ✏️" vs "spellcheck" must be >= 0.5
    score = string_similar("2. Spell-Checker ✏️", "spellcheck")
    assert score >= 0.5, "Should be similar despite formatting differences"

    score = string_similar("_parse_list", "ordered_list")
    assert score < 0.5, "too frequent and bad positioning"

    score = string_similar("script", "Schritt 2: Retagging-Batch erstellen", True)
    assert score < 0.5, "different length, false positive levenstein. Must be low"

    # Needs semantic understanding to match
    #score = string_similar("UploadObjectUnitTests", "Upload a directory", True)
    #assert score < 0.5, "different concepts, should be low, although the first token overlaps"

def test_fuzzy_lists():
    readme_headers = ['ordered_list', 'ordered_list', 'ordered_list']
    proj = ['_inline_text', '_collect_headings', '_build_headers_tree', '_parse_list', '_parse_code_block']
    res = fuzzy_intersection(proj, readme_headers, True)
    assert res is None

    readme_headers = ['embedding', 'pdf2task', 'agentic', 'task2json', 'tjson2text', 'documents', 'querying']
    folders = ['pdf2task', 'task2json', 'tjson2text', 'embedding']
    res = fuzzy_intersection(folders, readme_headers, False)
    assert res is not None

    readme_headers = ["1. Pattern Search 🔍", "2. Spell-Chcker ✏️", "3. Partial Match Detection 🎯", "4. Unused Module Detection (beta)"]
    folders = ["pattern_search", "spellcheck", "partial_match", "unused_modules", "to_report"]
    res = fuzzy_intersection(folders, readme_headers, False)
    assert res is not None
    assert res.only_a == ['to_report']

    print("==========================")
    proj = ['image', 'stage', 'variables', 'services', 'rules', 'tags', 'script', 'needs /Users/rax/work/db/db_billing/.gitlab-ci.yml::test_python (json_keys)']
    readme = ['Schritt 2: Retagging-Batch erstellen', 'Schritt 3: Ressourcen hinzufügen', 'Schritt 4: Tag-Ã„nderungen festlegen', 'Schritt 5: Validierung und Vorschau', 'Schritt 6: Batch einreichen', 'Schritt 7: Status überwachen', 'Schritt 8: Fehleranalyse (bei Bedarf)']
    res = fuzzy_intersection(proj, readme, True)
    assert res is None


