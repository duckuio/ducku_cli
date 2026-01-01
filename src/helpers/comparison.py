from dataclasses import dataclass
import re
import math
from typing import List, Optional
from collections import Counter
from rapidfuzz.distance import Levenshtein

TOKENIZE_TRANS_TABLE = str.maketrans({c: " " for c in "_,.;:/|()[]{}*\\"})
MIN_COMPARED_LIST_LENGTH = 3
MAX_LIST_LENGTHS_DIFF = 3
LISTS_SIMILARITY_THRESHOLD = 0.5
TOKENS_SIMILARITY_THRESHOLD = 0.5
TOKEN_LEN_BOOST_WEIGHT = 0.1
MAX_LEN_BOOST = 12
# 2 - important, 4 - more or less important, > 4 not important, 0 - exact match
TOKENS_ORDER_IMPORTANCE = 2
TOKENS_FIRST_POS_IMPORTANCE = 2.0
COVERAGE_ALPHA = 0.6 # too adjust end result not to force values to be too low by coverage
GENERIC_TOKENS = {
    "user", "users", "profile", "settings", "config", "data", "list", "item", "items",
    "get", "set", "create", "update", "delete", "add", "remove", "default", "script"
}


@dataclass
class ListsIntersectionReport:
    matched_debug: List[str] # ["users => user", ..]
    only_a: List[str] # items without matches in the first list
    only_b: List[str] # items without matches in the second list

def normalize_string(s: str) -> str:
    s = s.lower()
    s = re.sub(r'[^A-Za-z0-9]', "", s) # removing trash characters
    s = re.sub(r"^[0-9]+$", "", s) # number-only are not useful
    return s

def tokenize_string(s: str):
    camel_re = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|\d+")
    raw = s.translate(TOKENIZE_TRANS_TABLE).split()
    out = []
    for tok in raw:
        if not tok.isalnum():
            out.append(tok)
        elif not tok.isupper() and any(c.isupper() for c in tok[1:]):
            out.extend(camel_re.findall(tok))
        else:
            out.append(tok)
    return out

def token_similar(a: str, b: str) -> float:
    if len(a) < 2 or len(b) < 2:
        return 0.0
    # Require at least 2 matching prefix characters for similarity
    if a[:2] != b[:2]:
        return 0.0
    return Levenshtein.normalized_similarity(a, b)

def positional_penalty(i, j):
    return math.exp(-abs(i - j) / TOKENS_ORDER_IMPORTANCE)

def pos_weight(i: int, tau: float = 1.5) -> float:
    return math.exp(-i / tau)

def info_weight(t: str) -> float:
    return 0.35 if t in GENERIC_TOKENS else 1.0

def soft_overlap_avglen(tokens_a: List[str], tokens_b: List[str], debug: bool = False) -> float:
    """
    Compute weighted fuzzy overlap between two token lists [0-1]
    Accounts for token mirror position, informativeness, and Levenshtein similarity.
    """
    if not tokens_a and not tokens_b:
        return 1.0
    if not tokens_a or not tokens_b:
        return 0.0

    n = len(tokens_a)
    m = len(tokens_b)

    best_for_b = [0.0] * m
    matched_sum = 0.0

    if debug:
        print("=========================")

    for i, a in enumerate(tokens_a):
        best = 0.0
        best_j = -1
        wa_i = pos_weight(i) * info_weight(tokens_a[i])
        for j, b in enumerate(tokens_b):
            base = token_similar(a, b)
            if base == 0.0:
                if debug:
                    print("Comparing tokens '{}' and '{}': similarity=0.0, skipping".format(a, b))
                continue
            p = positional_penalty(i, j)
            wb_j = pos_weight(j) * info_weight(tokens_b[j])
            cand = base * p * min(wa_i, wb_j)
            if cand > best:
                best = cand
                best_j = j
            if cand > best_for_b[j]:
                best_for_b[j] = cand
            if debug:
                print(f"Comparing tokens '{a}' and '{b}': similarity={base}, penalty={p}, wa={wa_i}, wb={wb_j}, cand={cand}")
        matched_sum += best
        if debug:
            if best_j >= 0:
                print(f"BEST for '{tokens_a[i]}' => '{tokens_b[best_j]}' : {best}")
            else:
                print(f"BEST for '{tokens_a[i]}' => None : 0.0")

    for j in range(m):
        if best_for_b[j] == 0.0:
            continue
        matched_sum += best_for_b[j]

    denom = sum(pos_weight(i) * info_weight(tokens_a[i]) for i in range(n)) + sum(pos_weight(j) * info_weight(tokens_b[j]) for j in range(m))
    if denom <= 0.0:
        return 0.0

    score = matched_sum / denom
    if score < 0.0:
        return 0.0
    if score > 1.0:
        return 1.0
    return score

def consists_of_duplicates(lst: List[str]) -> bool:
    return all(
        string_similar(a_item, b_item) > LISTS_SIMILARITY_THRESHOLD
        for i, a_item in enumerate(lst) for j, b_item in enumerate(lst)
        if i != j
        )


def string_similar(a: str, b: str, debug=False) -> float:
    a_tokens = [nt for t in tokenize_string(a) if (nt := normalize_string(t))]
    b_tokens = [nt for t in tokenize_string(b) if (nt := normalize_string(t))]
    return soft_overlap_avglen(a_tokens, b_tokens, debug=debug)

def fuzzy_intersection(list_a: List[str], list_b: List[str], debug = False) -> Optional[ListsIntersectionReport]:
    """
    This function compares 2 lists of string for similarity
    Goal is to find out if the lists belong to the same domain, describing the same properties
    Lists can be not full or identical. That could be a reason for drift.
    In case of discrepancies found - report is returned, else - None

    Rules:
    1. Small lists cause false positives [MIN_COMPARED_LIST_LENGTH]
    2. Lists must be similar length [MAX_LIST_LENGTHS_DIFF]
    3. Lists are similar when at least one (smallest) list completely matches items in another one
    4. If lists are completely identical, it's not our case, nothing is missing
    """
    #print(f"DEBUG: fuzzy_intersection called with list_a={list_a}, list_b={list_b}, debug={debug}")
    
    # small lists are 90% false-positives
    if len(list_a) < MIN_COMPARED_LIST_LENGTH or len(list_b) < MIN_COMPARED_LIST_LENGTH:
        if debug:
            print("Lists too small for reliable comparison", len(list_a), len(list_b), MIN_COMPARED_LIST_LENGTH)
        return None
    
    if abs(len(list_a) - len(list_b)) > MAX_LIST_LENGTHS_DIFF:
        if debug:
            print("Lists length difference too large for reliable comparison", len(list_a), len(list_b), MAX_LIST_LENGTHS_DIFF)
        return None

    matched_a_is = []
    matched_b_is = []
    matched_debug = []
    for a_i, a_item in enumerate(list_a):
        found_b_i_for_a = None
        for b_i, b_item in enumerate(list_b):
            if b_i in matched_b_is:
                continue
            score = string_similar(a_item, b_item)
            debug_str = f"{a_item} => {b_item} ({score})"
            if debug:
                print(debug_str)
            if score > LISTS_SIMILARITY_THRESHOLD:
                
                found_b_i_for_a = b_i
                matched_debug.append(debug_str)
                # matched items in the second list must not match anything else to avoid duplicated scores
                matched_b_is.append(b_i)
        matched_a_is.append(found_b_i_for_a) # no match for this item

    only_a = [list_a[i] for i, matched_b_i in enumerate(matched_a_is) if matched_b_i is None]
    only_b = [list_b[i] for i in range(len(list_b)) if i not in matched_b_is]

    # we expect that at least one smallest list will match completely
    if only_a and only_b:
        if debug:
            print("Both contain unmatched items:", only_a, only_b)
        return None
    # lists are completely identical, nothing is missing, nothing to report
    if not only_a and not only_b:
        if debug:
            print("Lists are completely identical, nothing to report")
        return None
    
    # We cosider lists here being similar. Last check, one list can contain identical items, which has gained the scores.
    # Checking every list for duplicates, not doing it for every pair to improve performance
    if consists_of_duplicates(list_a) or consists_of_duplicates(list_b):
        if debug:
            print("One of the lists consists of duplicates, unreliable comparison")
        return None

    return ListsIntersectionReport(
        matched_debug=matched_debug,
        only_a=only_a,
        only_b=only_b
    )