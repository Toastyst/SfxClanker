import re
import json
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
    return query

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
    fm = FlavorManager()
    flavor_tags = [t for t in fm.get_tags(slot['category']) if t not in slot['pos_tags']]
    pos = slot['pos_tags'] + flavor_tags
    pos_str = ' +'.join(pos)
    neg = sorted(set(slot['neg_tags'] + fm.profile['universal_negatives']))
    neg_str = ' -'.join(neg)
    return f"{pos_str} -{neg_str}"

class FlavorManager:
    def __init__(self):
        with open('data/flavor_profiles.json', 'r') as f:
            self.profiles = json.load(f)
        self.profile = self.profiles['gritty_medieval']

    def get_tags(self, category: str) -> List[str]:
        return self.profile.get(category, [])

def get_flavor_query(category: str) -> str:
    flavors = {
        'Combat': 'metallic heavy gritty dark fantasy souls-like',
        'Movement': 'organic stone wood creak whoosh low reverb',
        'UI': 'ethereal chime ting clean short'
    }
    return flavors.get(category, 'dark fantasy souls-like')
