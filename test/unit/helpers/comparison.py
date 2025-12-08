from src.helpers.comparison import fuzzy_intersection, normalized_levenshtein, hybrid_similarity, token_similarity, fuzzy


def test_fuzzy_score():
    score = fuzzy("User", "users")
    assert score >= 0.8
    score = fuzzy("cherry", "cheri")
    assert score >= 0.5

def test_token_similarity():
    # Test exact token match
    score = token_similarity("user profile", "profile user")
    assert score == 1.0, "Exact tokens in different order should give 1.0"
    
    # Test partial token match
    score = token_similarity("user profile settings", "user profile")
    assert 0.6 <= score <= 0.7, "2 out of 3 tokens match"
    
    # Test similar tokens (fuzzy match within tokens)
    score = token_similarity("users", "user")
    assert score > 0.8, "Similar tokens should match with high score"
    
    # Test no match
    score = token_similarity("apple", "orange")
    assert score == 0, "No token overlap should give 0"
    
    # Test empty strings
    score = token_similarity("", "test")
    assert score == 0, "Empty string should give 0"
    
    # Test case insensitivity
    score = token_similarity("User Profile", "user profile")
    assert score == 1.0, "Case should not matter"
    
    # Test with special characters and normalization
    score = token_similarity("user-profile_settings", "user profile settings")
    assert score == 1.0, "Normalization should handle hyphens and underscores"
    
    # Test complex multi-token similarity
    score = token_similarity("pattern search module", "pattern searching modules")
    assert score >= 0.66, "Similar multi-token strings should have reasonable similarity"


def test_hybrid_similarity():
    # Test token similarity path (ts > 0)
    score = hybrid_similarity("user profile", "profile user")
    assert score == 1.0, "Exact tokens should give 1.0 via token similarity"
    
    score = hybrid_similarity("user settings", "user profile")
    assert score > 0, "Partial token overlap should use token similarity"
    
    # Test fuzzy fallback (ts == 0, no token overlap)
    score = hybrid_similarity("apple", "aple")
    assert score > 0.8, "Similar strings with no token overlap should use fuzzy"
    
    score = hybrid_similarity("test", "testing")
    assert score > 0.5, "Similar strings should have reasonable fuzzy score"
    
    # Test case insensitivity
    score = hybrid_similarity("User", "user")
    assert score == 1.0, "Case should not matter"
    
    # Test normalization
    score = hybrid_similarity("user-profile", "user_profile")
    assert score == 1.0, "Normalization should handle separators"
    
    # False positives - strings that should NOT match highly
    score = hybrid_similarity("user", "server")
    assert score <= 0.6, "Different words should have low similarity"
    
    score = hybrid_similarity("apple", "orange")
    assert score < 0.4, "Completely different words should have very low similarity"
    
    score = hybrid_similarity("pattern", "parent")
    assert score < 0.75, "Similar-looking but different words should not match highly"
    
    score = hybrid_similarity("authentication", "authorization")
    assert score < 0.75, "Similar-sounding but different terms should not match highly"
    
    # Edge cases
    score = hybrid_similarity("", "test")
    assert score == 0, "Empty string should give 0"
    
    score = hybrid_similarity("a", "b")
    assert score == 0, "Single different characters should give 0"
    
    # Multi-word combinations
    score = hybrid_similarity("database connection", "database connector")
    assert score >= 0.7, "Similar phrases should match reasonably"
    
    score = hybrid_similarity("create user account", "delete user profile")
    assert score < 0.6, "Different actions should not match highly despite shared words"

    score = hybrid_similarity("list_item1", "ordered_list")
    assert score <= 0.5, "Similar multi-token strings should have reasonable similarity"

    score = hybrid_similarity("unused module detection beta", "unused modules")
    assert score >= 0.6, "Different concepts should not match highly"


def test_fuzzy_lists():

    list1 = ['metadata_extraction_job', 'auth', 'embedding', 'pdf2task', 'agentic', 'task2json', 'tjson2text', 'wa_manager', 'projector-ui', 'documents', 'querying']
    list2 = ['pdf2task', 'task2json', 'tjson2text', 'embedding']
    assert fuzzy_intersection(list1, list2, True) == True

    readme_headers = ["Pattern Search 🔍", "Spell-Chcker ✏️", "Partial Match Detection 🎯", "Unused Module Detection (beta)"]
    folders = ["pattern_search", "spellcheck", "partial_match", "unused_modules"]

    assert fuzzy_intersection(readme_headers, folders, True) == True


