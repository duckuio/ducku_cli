from typing import List
from rapidfuzz.distance import Levenshtein

# levenshtein distnace related normalized string lengths [0, 1]
def normalized_levenshtein(s1, s2):
    s1 = str(s1).lower()
    s2 = str(s2).lower()
    d = Levenshtein.distance(s1, s2)
    return 1 - d / max(len(s1), len(s2))

def fuzzy_intersection(a: List[str], b: List[str], debug = False) -> bool:
    def log(*args):
        if debug:
            print(*args)
    
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
            nl = normalized_levenshtein(s1, s2)
            log(s1, " <  === >", s2, nl)
            if nl >= 0.8:
                log("Match found:", s1, "<==>", s2, "(", nl, ")")
                matches += 1
                found = True
                break
        if found: # since we filtered for unique values, there can be only one match
            continue

    ni = matches / avg_len # normalize against length
    log("matches", matches)
    log("matches / avg_len", ni)
    if ni > 0.5: # lists are mostly intersected, but there are missing items
        return True
    return False
