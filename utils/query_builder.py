from typing import List
from utils.slots import Slot

def simple_query(slot: Slot, flavor: str = "") -> str:
    base = slot["display_name"] + " " + " ".join(slot["fallbacks"][:2])
    return (base + " " + flavor).strip() if flavor else base
