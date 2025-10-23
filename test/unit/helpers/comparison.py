from src.helpers.comparison import fuzzy_intersection, normalized_levenshtein


def test_levenshtein_distance():
    score = normalized_levenshtein("User", "users")
    assert score >= 0.8
    score = normalized_levenshtein("cherry", "cheri")
    assert score >= 0.5

def test_fuzzy_lists():
    # 2 matches. cherry => cheri: 0.66, not passing
    # list1 = ["user", "banana", "cherry"]
    # list2 = ["Users", "bannana", "cheri"]
    # # should pass with matches to len = 0.66
    # assert fuzzy_intersection(list1, list2, True) == True

    # # 2 matches, but lists are too different by length, not passing
    # list1 = ["user", "banana", "tomato", "apple", "watermelon", "peach", "grape"]
    # list2 = ["Users", "bannana", "tomato"]
    
    # assert fuzzy_intersection(list1, list2, True) == False

    list1 = ['metadata_extraction_job', 'auth', 'embedding', 'pdf2task', 'agentic', 'task2json', 'tjson2text', 'wa_manager', 'projector-ui', 'documents', 'querying']
    list2 = ['pdf2task', 'task2json', 'tjson2text', 'embedding']
    assert fuzzy_intersection(list1, list2, True) == True

