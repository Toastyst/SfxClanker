from typing import List
from utils.slots import Slot

def simple_query(slot: Slot, flavor: str = "") -> str:
    base = slot["display_name"] + " " + (slot["fallbacks"][0] if slot["fallbacks"] else "")
    return (base + " " + flavor).strip() if flavor else base
