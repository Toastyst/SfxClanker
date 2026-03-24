from typing import TypedDict, Dict, List, Optional
import json

class Prompt(TypedDict):
    category: str
    name: str
    fallbacks: List[str]
    id: Optional[str]

class SFXLibrary:
    def __init__(self) -> None:
        with open('prompts.json', 'r') as f:
            data = json.load(f)
        self.prompts: Dict[str, Dict[str, Prompt]] = {}
        for item in data:
            cat = item['category']
            if cat not in self.prompts:
                self.prompts[cat] = {}
            self.prompts[cat][item['name']] = {
                'fallbacks': item['fallbacks'],
                'id': item.get('id'),
                'category': cat,
                'name': item['name']
            }

    def get_prompt(self, category: str, name: str) -> Optional[Prompt]:
        if category in self.prompts and name in self.prompts[category]:
            return self.prompts[category][name]
        return None

    def get_names(self, category: str) -> List[str]:
        if category in self.prompts:
            return list(self.prompts[category].keys())
        return []