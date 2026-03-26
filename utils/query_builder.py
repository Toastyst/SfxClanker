import re
from typing import List
from utils.slots import Slot

def build_search_query(raw_term: str) -> str:
    words = re.findall(r'\w+', raw_term.lower())
    words = [w for w in words if len(w) >= 3][:4]
    query = ' +'.join(words)
    if any(x in raw_term.lower() for x in ['attack hit', 'sword']):
        query += ' +sword'
    if 'level up' in raw_term.lower():
        query += ' +chime'
    if any(x in raw_term.lower() for x in ['wall crumble', 'secret']):
        query += ' +stone +break'
    return query

def enhance_query(query: str) -> str:
    return query + " dark fantasy souls-like low reverb gritty armor medieval dark souls style"

def get_progressive_queries(name: str, fallbacks: List[str]) -> List[str]:
    queries = [name] + fallbacks
    flavor_terms = ["dark", "fantasy", "souls-like", "low reverb", "gritty", "armor", "medieval", "dark souls style"]
    progressive = []
    for base in queries:
        simple = build_search_query(base)
        progressive.append(simple)
        for i in range(1, len(flavor_terms) + 1):
            enhanced = simple + " +" + " +".join(flavor_terms[:i])
            progressive.append(enhanced)
    return progressive

def build_slot_query(slot: Slot) -> str:
    pos = " ".join(slot["pos_tags"])
    neg = " -".join(slot["neg_tags"])
    return f"{pos} -{neg}"
