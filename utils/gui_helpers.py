import tkinter as tk
from typing import Dict, List, Callable
from utils.slots import Slot
from utils.search import Candidate
from utils.audio_processor import preview_audio

def build_slot_section(parent: tk.Frame, slot: Slot, cands: List[Candidate], selections: Dict[str, Dict[str, float]], allow_multiple: bool) -> None:
    # Bold header
    header = tk.Label(parent, text=slot['display_name'], font=('Arial', 12, 'bold'), bg='#2b2b2b', fg='white')
    header.pack(anchor='w', pady=5)
    # Grid for cands
    for i, cand in enumerate(cands[:5]):  # top 5
        row_frame = tk.Frame(parent, bg='#2b2b2b')
        row_frame.pack(fill='x', padx=10)
        # Chk
        var = tk.BooleanVar(value=i==0)  # top default
        chk = tk.Checkbutton(row_frame, variable=var, bg='#2b2b2b', fg='white', selectcolor='#3c3c3c')
        chk.pack(side=tk.LEFT)
        # Label name tag dur
        label_text = f"{cand['name']} • {cand['duration']:.1f}s"
        tk.Label(row_frame, text=label_text, bg='#2b2b2b', fg='white').pack(side=tk.LEFT, padx=5)
        # Scale vol
        scale = tk.Scale(row_frame, from_=0.5, to=2.0, resolution=0.1, orient=tk.HORIZONTAL, bg='#2b2b2b', fg='white')
        scale.set(1.0)
        scale.pack(side=tk.LEFT, padx=5)
        # Play btn
        def play(url=cand['preview_url'], scale=scale):
            import requests, os
            temp = f"temp_{cand['id']}.mp3"
            try:
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    with open(temp, 'wb') as f:
                        f.write(resp.content)
                    preview_audio(temp, scale.get())
            except:
                pass
        btn = tk.Button(row_frame, text="Play", command=play, bg='#4a4a4a', fg='white')
        btn.pack(side=tk.LEFT, padx=5)
        # Bind selections
        def on_change():
            slot_name = slot['name']
            id_str = cand['id']
            if var.get():
                if slot_name not in selections:
                    selections[slot_name] = {}
                selections[slot_name][id_str] = scale.get()
            else:
                if slot_name in selections and id_str in selections[slot_name]:
                    del selections[slot_name][id_str]
        var.trace_add('write', lambda *args: on_change())
        scale.config(command=lambda v: on_change())

def build_category_scrollable(notebook, cat: str, slots_cands: Dict[str, List[Candidate]], selections: Dict[str, Dict[str, float]], allow_multiple: bool) -> None:
    tab = tk.Frame(notebook, bg='#2b2b2b')
    notebook.add(tab, text=cat)
    # Scrollable canvas
    canvas = tk.Canvas(tab, bg='#2b2b2b', highlightthickness=0)
    scrollbar = tk.Scrollbar(tab, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas, bg='#2b2b2b')
    scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(-int(e.delta/120), "units"))
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    canvas.pack(fill=tk.BOTH, expand=True)
    # For each slot in cat
    for slot_name, cands in slots_cands.items():
        if slot_name.startswith(cat.lower() + '_'):
            from utils.slots import get_slots
            slots = get_slots()
            slot = next(s for s in slots if s['name'] == slot_name)
            build_slot_section(scroll_frame, slot, cands, selections, allow_multiple)