from typing import List, Optional
from utils.slots import get_slots, Slot

class SFXLibrary:
    def __init__(self) -> None:
        self.slots: List[Slot] = get_slots()

    def get_slots(self) -> List[Slot]:
        return self.slots

    def get_slot(self, name: str) -> Optional[Slot]:
        for slot in self.slots:
            if slot['name'] == name:
                return slot
        return None

    def filename_from_slot(self, slot: Slot) -> str:
        return f"{slot['name']}.wav"
