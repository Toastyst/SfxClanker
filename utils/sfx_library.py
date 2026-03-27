import json
import re
from typing import List, Optional
from utils.slots import Slot

class SFXLibrary:
    def __init__(self) -> None:
        self.slots: List[Slot] = self._load_slots()

    def _load_slots(self) -> List[Slot]:
        with open('prompts.json', 'r') as f:
            data = json.load(f)
        slots = []
        for p in data:
            if p['category'] == 'Test':
                continue
            slot = Slot(
                name=self._to_filename(p['name']),
                display_name=p['name'],
                category=p['category'],
                fallbacks=p['fallbacks'],
                id=p.get('id')
            )
            slots.append(slot)
        return slots

    def _to_filename(self, name: str) -> str:
        return re.sub(r'\W+', '_', name.lower()).strip('_')

    def get_slots(self) -> List[Slot]:
        return self.slots

    def get_slot(self, name: str) -> Optional[Slot]:
        for slot in self.slots:
            if slot['name'] == name:
                return slot
        return None

    def filename_from_slot(self, slot: Slot) -> str:
        return f"{slot['name']}.wav"
