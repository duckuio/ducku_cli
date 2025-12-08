from difflib import SequenceMatcher
import re
from typing import List
from rapidfuzz.distance import Levenshtein

def normalize_string(s):
    s = s.lower()
    s = re.sub(r'[\-_ ]+', ' ', s)
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

# levenshtein distnace related normalized string lengths [0, 1]
def normalized_levenshtein(s1, s2):
    d = Levenshtein.distance(s1, s2)
    return 1 - d / max(len(s1), len(s2))

def fuzzy_intersection(a: List[str], b: List[str], debug = False) -> bool:
    def log(*args):
        if debug:
            print(*args)
    
    a = [normalize_string(s) for s in a]
    b = [normalize_string(s) for s in b]

    if len(a) < 3 or len(b) < 3: # too short lists to make any decisions
        return False

    # make lists unique
    a = list(set(a))
    b = list(set(b))
    matches = 0
    comparable = len(a)/len(b) if len(a) < len(b) else len(b)/len(a)
    log("Comparable:", comparable)
    if comparable < 0.3: # lists are too different
        return False
    avg_len = (len(a) + len(b)) / 2
    log("avg_len", avg_len)
    for s1 in a:
        found = False
        for s2 in b:
            if not s1 or not s2:
                continue
            nl = hybrid_similarity(s1, s2)
            log(s1, " <  === >", s2, nl)
            # Increased threshold from 0.6 to 0.8 for stricter matching
            if nl >= 0.8:
                log("Match found:", s1, "<==>", s2, "(", nl, ")")
                matches += 1
                found = True
                break
        if found: # since we filtered for unique values, there can be only one match
            continue

    # Require at least 2 actual matches (not just percentage)
    if matches < 2:
        return False
    
    ni = matches / avg_len # normalize against length
    log("matches", matches)
    log("matches / avg_len", ni)
    # Require significant overlap - 50% is reasonable for partial lists
    if ni >= 0.5: # lists must have significant overlap
        return True
    return False





#========================
NOISE = {"alpha", "beta", "and", "or", "a", "the", "of", "in", "on", "for", "with", "to", "is", "are", "by", "an", "this", "that", "it", "as", "at", "from", "but", "not", "be", "was", "were", "which"}

def tokenize(s):
    return [t for t in normalize_string(s).split() if t not in NOISE]

def fuzzy(a, b):
    return SequenceMatcher(None, normalize_string(a), normalize_string(b)).ratio()

def token_similarity(a, b):
    ta = tokenize(a)
    tb = tokenize(b)
    if not ta or not tb:
        return 0
    overlaps = 0
    for x in ta:
        for y in tb:
            if x == y:
                overlaps += 1
            elif SequenceMatcher(None, x, y).ratio() > 0.8:
                overlaps += 1
    return overlaps / max(len(ta), len(tb))

def hybrid_similarity(a, b, debug=False):
    def log(*args):
        if debug:
            print(*args)
    
    ts = token_similarity(a, b)
    log(f"Token similarity for '{a}' vs '{b}': {ts}")
    if ts > 0:
        log(f"Using token similarity: {ts}")
        return ts
    f = fuzzy(a, b)
    log(f"Using fuzzy similarity: {f}")
    return f