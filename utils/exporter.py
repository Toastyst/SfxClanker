import os
import shutil
from datetime import datetime
from typing import List, Dict, Callable

def package_assets(confirmed_sounds: List[Dict], output_path: str, console_callback: Callable[[str], None]) -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_dir = os.path.join(output_path, f"SFX_Export_{timestamp}")
    os.makedirs(export_dir, exist_ok=True)
    console_callback(f"Exporting to {export_dir}")
    for sound in confirmed_sounds:
        cat = sound['category']
        slot_name = sound['slot_name']
        filename = f"{slot_name}_{sound['id']}.wav"
        cat_dir = os.path.join(export_dir, cat)
        os.makedirs(cat_dir, exist_ok=True)
        dest = os.path.join(cat_dir, filename)
        if os.path.exists(sound['path']):
            shutil.copy(sound['path'], dest)
            console_callback(f"Exported {filename}")
        else:
            console_callback(f"Warning: {sound['path']} not found, skipped {filename}")
    console_callback("Export complete.")