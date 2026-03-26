import re
import json
from typing import List, Dict
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
    profile = fm.get_tags(slot['category'])
    mandatory = profile.get('mandatory', [])
    optional = profile.get('optional', [])[:3]  # max 3
    exclude = profile.get('exclude', [])
    # Unique: remove if in mandatory
    optional = [t for t in optional if t not in mandatory]
    # + for pos_tags + mandatory
    pos_plus = sorted(set(slot['pos_tags'] + mandatory))  # unique sorted
    pos_str = '+' + ' +'.join(pos_plus) if pos_plus else ''
    # no prefix for optional
    optional_str = ' '.join(optional)
    # - for neg_tags + universal + exclude
    neg = sorted(set(slot['neg_tags'] + fm.profile['universal_negatives'] + exclude))
    neg_str = '-' + ' -'.join(neg) if neg else ''
    query = f"{pos_str} {optional_str} {neg_str}".strip()
    return query

class FlavorManager:
    def __init__(self):
        with open('data/flavor_profiles.json', 'r') as f:
            self.profiles = json.load(f)
        self.profile = self.profiles['gritty_medieval']

    def get_tags(self, category: str) -> Dict[str, List[str]]:
        return self.profile.get(category, {})

def get_flavor_query(category: str) -> str:
    flavors = {
        'Combat': 'metallic heavy gritty dark fantasy souls-like',
        'Movement': 'organic stone wood creak whoosh low reverb',
        'UI': 'ethereal chime ting clean short'
    }
    return flavors.get(category, 'dark fantasy souls-like')
