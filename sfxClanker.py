import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import requests
import subprocess
import os
import re
import threading
import concurrent.futures
import json
import sys
import argparse
import random
import shutil
import time
import math
import queue
from datetime import datetime
from typing import List, Dict, Tuple, TypedDict, Any, Callable, Optional
from collections import defaultdict
from utils.sfx_library import SFXLibrary
from utils.query_builder import simple_query
from utils.audio_processor import process_audio, preview_audio, AudioSegment
from utils.search import weighted_search_freesound, get_sound_by_id, simple_search_slot
from utils.gui_helpers import build_category_scrollable
from utils.utils import download_sfx, generate_filename, log_message, log_failed

class Candidate(TypedDict):
    id: str
    name: str
    duration: float
    preview_url: str
    downloads: int
    quality_score: float
    analysis: Dict[str, Any]

LengthConfig = Dict[str, float]  # e.g., {'Combat': 1.0, 'UI': 0.5}

class VolumeSettings(TypedDict):
    global_volume: float  # 0.0-2.0 for boost
    loudness_target: float  # dB, e.g., -14.0
    strict_length: bool

def load_keys() -> List[str]:
    try:
        with open('freesound_key.txt', 'r') as f:
            key = f.read().strip()
        return [key] if key else []
    except:
        return []

def save_api_key(key: str) -> None:
    with open('freesound_key.txt', 'w') as f:
        f.write(key)



# Moved to utils/utils.py

# RANDOM MODE: pick from top 5 for funny packs
def process_item(item: Dict[str, Any], api_keys: List[str], normalize: bool, random_mode: bool, output_dir: str, console_callback: Callable[[str], None], trim: bool = False,
                 volume_settings: Optional[VolumeSettings] = None, length_config: Optional[LengthConfig] = None,
                 manual_candidates: Optional[List[Candidate]] = None, manual_vol: Optional[float] = None, flavor: str = "", deep_pool: bool = False) -> bool:
    console_callback("─" * 37)
    console_callback(f"=== {item['filename']} ===")
    console_callback(f"Searching for {item['filename']}...")
    result = None
    used_query = None
    if item.get('manual_id'):
        console_callback(f"Query: manual ID {item['manual_id']}")
        result = get_sound_by_id(item['manual_id'], api_keys)
        if result:
            used_query = f"Manual ID {item['manual_id']}"
            console_callback(f"Found 1 result")
            console_callback(f"Picked ID {item['manual_id']} - {result['name']}")
            is_cc0 = True  # Assume IDs are CC0
        else:
            result = None
    elif item.get('id'):
        console_callback(f"Query: predefined ID {item['id']}")
        result = get_sound_by_id(item['id'], api_keys)
        if result:
            used_query = f"ID {item['id']}"
            console_callback(f"Found 1 result")
            console_callback(f"Picked ID {item['id']} - {result['name']}")
            is_cc0 = True  # Assume IDs are CC0
        else:
            result = None
    if not result:
        slot = item['slot']
        cands = simple_search_slot(slot, flavor, deep_pool, api_keys)
        console_callback(f"Found {len(cands)} candidates")
        if cands:
            if random_mode:
                cand = random.choice(cands[:5])
            else:
                cand = cands[0]
            result = get_sound_by_id(cand['id'], api_keys)
            used_query = f"Simple query for {slot['display_name']}"
            console_callback(f"Picked ID {cand['id']} - {cand['name']}")
            is_cc0 = True  # Assume CC0
        else:
            is_cc0 = True  # default
    if not result:
        console_callback("Skipped: No results")
        log_failed(output_dir, [item['slot']['display_name']])
        log_message(output_dir, f"Skipped {item['filename']}: no results")
        return False
    if not is_cc0:
        log_message(output_dir, f"NON-CC0: {item['filename']} ({used_query})")
    temp_path = item['path'] + '.temp'
    console_callback(f"Downloading preview...")
    if not download_sfx(result, temp_path):
        console_callback("Skipped: Download failed")
        log_message(output_dir, f"Skipped {item['filename']}: download failed")
        return False
    max_len = 2.0  # default
    vol_gain = volume_settings['global_volume'] if volume_settings else 1.0
    rms_t = volume_settings['loudness_target'] if volume_settings else -14.0
    strict_l = volume_settings['strict_length'] if volume_settings else False
    manual_vol = item.get('manual_vol')
    console_callback(f"Processing audio (normalize={normalize}, trim={trim}, vol={vol_gain:.1f}, rms={rms_t:.1f}, max_len={max_len})...")
    result_proc = process_audio(temp_path, item['path'], normalize, trim, vol_gain=vol_gain, max_len=max_len, rms_target=rms_t, strict_length=strict_l, vol_factor=manual_vol)
    if result_proc is not True:
        console_callback(f"Skipped: Process failed - {result_proc}")
        log_message(output_dir, f"Skipped {item['filename']}: process failed - {result_proc}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return False
    os.remove(temp_path)
    log_message(output_dir, f"Generated {item['filename']} (query: {used_query})")
    console_callback(f"Generated successfully")
    return True

def run_headless() -> None:
    parser = argparse.ArgumentParser(description='SFX Clanker Headless Mode')
    parser.add_argument('--output', help='Output directory')
    parser.add_argument('--normalize', action='store_true', help='Normalize audio')
    parser.add_argument('--random', action='store_true', help='Randomize sounds each batch')
    parser.add_argument('--trim', action='store_true', help='Trim silence')
    parser.add_argument('--categories', default='Combat,Movement,UI', help='Comma-separated categories')
    parser.add_argument('--volume', type=float, default=1.0, help='Global volume multiplier (0.0-2.0)')
    parser.add_argument('--loudness', type=float, default=-14.0, help='RMS loudness target (dB)')
    parser.add_argument('--strict-length', action='store_true', help='Strict length trimming with fade')
    parser.add_argument('--manual', action='store_true', help='Manual selection mode (stub: auto-pick)')
    parser.add_argument('--flavor', default='', help='Flavor text to append to queries')
    parser.add_argument('--deep-pool', action='store_true', help='Use deep pool mode for better results')
    args = parser.parse_args(sys.argv[2:])

    output_dir = args.output
    normalize = args.normalize
    random_mode = args.random
    trim = args.trim
    categories = [c.strip() for c in args.categories.split(',')]
    flavor = args.flavor
    deep_pool = args.deep_pool

    api_keys = load_keys()
    if not api_keys:
        print("Error: No API keys found. Run GUI first to set it.")
        sys.exit(1)

    if not output_dir:
        print("Error: --output required for generation")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    sfx = SFXLibrary()
    slots = sfx.get_slots()
    items = []
    for cat in categories:
        cat_slots = [slot for slot in slots if slot['category'] == cat]
        for slot in cat_slots:
            filename = sfx.filename_from_slot(slot)
            items.append({'slot': slot, 'filename': filename, 'path': os.path.join(output_dir, filename)})

    if not items:
        print("Error: No items for selected categories")
        sys.exit(1)

    volume_settings = {
        'global_volume': args.volume,
        'loudness_target': args.loudness,
        'strict_length': args.strict_length
    }
    length_config = {'Combat': 1.0, 'Movement': 1.5, 'UI': 0.5, 'Test': 2.0}  # hardcoded
    if args.manual:
        print("Manual mode stubbed in headless - using auto selection")
    print(f"Generating {len(items)} SFX to {output_dir}...")
    success_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures_to_items = {executor.submit(process_item, item, api_keys, normalize, random_mode, output_dir, lambda msg: print(f"[{item['filename']}] {msg}"), trim, volume_settings, length_config, flavor=flavor, deep_pool=deep_pool): item for item in items}  # type: ignore[arg-type,misc]
        for future in concurrent.futures.as_completed(futures_to_items):
            item = futures_to_items[future]
            print(f"Processing {item['filename']}")
            try:
                success = future.result()
                if success:
                    success_count += 1
                    print(f"[{item['filename']}] SUCCESS")
                else:
                    print(f"[{item['filename']}] SKIPPED")
            except Exception as e:
                print(f"[{item['filename']}] ERROR: {e}")

    print(f"Done: {success_count}/{len(items)} generated")
    sys.exit(0 if success_count > 0 else 1)

class SFXClankerGUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        try:
            self.title("SFX Clanker - HelloKnight Pack Generator")
            self.geometry("1480x920")
            self.minsize(1400, 750)
            self.configure(bg='#1a1a1a')
            self.sfx = SFXLibrary()
            self.slots = self.sfx.get_slots()
            self.output_dir = ""
            self.normalize = tk.BooleanVar(value=True)
            self.randomize = tk.BooleanVar(value=False)
            self.trim = tk.BooleanVar(value=False)
            self.volume_var = tk.DoubleVar(value=1.0)
            self.loudness_var = tk.DoubleVar(value=-14.0)
            self.manual_var = tk.BooleanVar(value=False)
            self.strict_var = tk.BooleanVar(value=False)
            self.flavor_var = tk.StringVar()
            self.deep_pool_var = tk.BooleanVar(value=False)
            self.length_config = {'Combat': 1.0, 'Movement': 1.5, 'UI': 0.5, 'Test': 2.0}
            self.allow_multiple_var = tk.BooleanVar(value=False)
            self.test_mode_var = tk.BooleanVar(value=False)
            self.selections = defaultdict(dict)
            self.console_queue = queue.Queue()
            self.progress = ttk.Progressbar(self, orient="horizontal", mode="determinate")
            self.status_label = tk.Label(self, text="Ready", bg='#1a1a1a', fg='white')
            self.stop_event = threading.Event()
            self.left_frame = None
            self.create_widgets()
        except Exception as e:
            messagebox.showerror("Initialization Error", f"Failed to start: {e}")
            self.destroy()

    def create_widgets(self) -> None:
        # Left frame: checklist
        self.left_frame = tk.Frame(self, bg='#1a1a1a', width=200)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=5)
        self.left_frame.pack_propagate(False)
        tk.Label(self.left_frame, text="Categories:", bg='#1a1a1a', fg='white', font=('Arial', 10, 'bold')).pack(anchor='w', pady=5)
        self.check_vars = {}
        cats = ['Combat', 'Movement', 'UI']
        for cat in cats:
            var = tk.BooleanVar(value=True)
            self.check_vars[cat] = var
            chk = tk.Checkbutton(self.left_frame, text=cat, variable=var, bg='#1a1a1a', fg='white', selectcolor='#3c3c3c')
            chk.pack(anchor='w', padx=10, pady=2)
        tk.Button(self.left_frame, text="Select All", command=self.select_all, bg='#4a4a4a', fg='white').pack(anchor='w', padx=10, pady=5)

        # Top toolbar
        top_frame = tk.Frame(self, bg='#1a1a1a')
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Button(top_frame, text="Set API Key", command=lambda: self.set_api_key(), bg='#4a4a4a', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(top_frame, text="Choose Output Folder", command=self.choose_output_dir, bg='#4a4a4a', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Scale(top_frame, from_=0.0, to=2.0, resolution=0.1, orient=tk.HORIZONTAL, variable=self.volume_var, label="Vol").pack(side=tk.LEFT, padx=10)
        tk.Scale(top_frame, from_=-20.0, to=0.0, resolution=1.0, orient=tk.HORIZONTAL, variable=self.loudness_var, label="RMS").pack(side=tk.LEFT, padx=10)
        tk.Label(top_frame, text="Flavor:", bg='#1a1a1a', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Entry(top_frame, textvariable=self.flavor_var, width=20).pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(top_frame, text="Deep Pool", variable=self.deep_pool_var, bg='#1a1a1a', fg='white', selectcolor='#3c3c3c').pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(top_frame, text="Normalize", variable=self.normalize, bg='#1a1a1a', fg='white', selectcolor='#3c3c3c').pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(top_frame, text="Trim", variable=self.trim, bg='#1a1a1a', fg='white', selectcolor='#3c3c3c').pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(top_frame, text="Random", variable=self.randomize, bg='#1a1a1a', fg='white', selectcolor='#3c3c3c').pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(top_frame, text="Strict", variable=self.strict_var, bg='#1a1a1a', fg='white', selectcolor='#3c3c3c').pack(side=tk.LEFT, padx=5)
        tk.Button(top_frame, text="STOP", command=self.stop_search, bg='#880808', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(top_frame, text="Test Mode (2 slots)", variable=self.test_mode_var, bg='#1a1a1a', fg='white', selectcolor='#3c3c3c').pack(side=tk.RIGHT, padx=5)

        # Middle notebook (70% vertical)
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background='#252525')
        style.configure('TNotebook.Tab', background='#4a4a4a', foreground='white')
        self.notebook = ttk.Notebook(self, style='TNotebook')
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Bottom frame: console and buttons
        bottom_frame = tk.Frame(self, bg='#1a1a1a')
        bottom_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        # Console
        self.console = tk.Text(bottom_frame, height=15, bg='#0f0f0f', fg='white', insertbackground='white')
        self.console.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.console.tag_config("success", foreground="#00ff00")
        self.console.tag_config("skipped", foreground="#ff6666")
        self.console.tag_config("query", foreground="#66ccff")
        self.console.tag_config("info", foreground="#aaaaaa")
        self.console.insert(tk.END, "Console output:\n")
        self.console.config(state='disabled')
        # Controls
        controls_frame = tk.Frame(bottom_frame, bg='#1a1a1a')
        controls_frame.pack(fill=tk.X, pady=5)
        tk.Checkbutton(controls_frame, text="Manual", variable=self.manual_var, bg='#1a1a1a', fg='white', selectcolor='#3c3c3c').pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(controls_frame, text="Multiple", variable=self.allow_multiple_var, bg='#1a1a1a', fg='white', selectcolor='#3c3c3c').pack(side=tk.LEFT, padx=5)
        self.gen_btn = tk.Button(controls_frame, text="GENERATE SOUND PACK", command=self.generate_pack, bg='#d4af37', fg='black', font=('Arial', 12, 'bold'))
        self.gen_btn.pack(side=tk.LEFT, padx=10)
        self.confirm_btn = tk.Button(controls_frame, text="Confirm Selections", command=self.read_selections_and_continue, bg='#d4af37', fg='black', font=('Arial', 12, 'bold'))
        self.confirm_btn.pack(side=tk.LEFT, padx=10)
        self.confirm_btn.pack_forget()  # Hide initially
        self.export_btn = tk.Button(controls_frame, text="EXPORT CONFIRMED", command=self.export_pack, bg='#d4af37', fg='black', font=('Arial', 12, 'bold'))
        self.export_btn.pack(side=tk.RIGHT, padx=10)
        self.export_btn.config(state='disabled')
        # Progress and status
        self.progress = ttk.Progressbar(bottom_frame, orient="horizontal", mode="determinate")
        self.progress.pack(fill=tk.X, pady=5)
        self.status_label = tk.Label(bottom_frame, text="Ready", bg='#1a1a1a', fg='white')
        self.status_label.pack(pady=5)
        self.poll_console()

    def select_all(self) -> None:
        all_selected = all(var.get() for var in self.check_vars.values())
        for var in self.check_vars.values():
            var.set(not all_selected)

    def choose_output_dir(self) -> None:
        dir = filedialog.askdirectory()
        if dir:
            self.output_dir = dir
            self.status_label.config(text=f"Output: {dir}")

    def set_api_key(self) -> None:
        key = simpledialog.askstring("API Key", "Enter FreeSound API key:")
        if key:
            save_api_key(key)
            self.update_console("API key saved.")

    def stop_search(self) -> None:
        self.stop_event.set()
        self.update_console("Stop signal sent.")

    def generate_pack(self) -> None:
        if not self.output_dir:
            messagebox.showerror("Error", "Choose output folder first")
            return
        api_keys = load_keys()
        self.update_console(f"API keys loaded: {len(api_keys)}")
        if not api_keys:
            key = simpledialog.askstring("API Key", "Enter FreeSound API key:")
            if not key:
                return
            save_api_key(key)
            api_keys = [key]
        self.gen_btn.config(state='disabled')
        self.update_console("Searching slots...")
        self.status_label.config(text="Searching...")
        self.volume_settings = {
            'global_volume': self.volume_var.get(),
            'loudness_target': self.loudness_var.get(),
            'strict_length': self.strict_var.get()
        }
        self.api_keys = api_keys
        threading.Thread(target=self.orchestrate_search, daemon=True).start()

    def orchestrate_search(self):
        self.stop_event.clear()
        selected_cats = [cat for cat, var in self.check_vars.items() if var.get()]
        slots_to_search = [slot for slot in self.slots if slot['category'] in selected_cats]
        if self.test_mode_var.get():
            slots_to_search = slots_to_search[:2]
        self.items = []
        for slot in slots_to_search:
            filename = self.sfx.filename_from_slot(slot)
            self.items.append({'slot': slot, 'filename': filename, 'path': os.path.join(self.output_dir, filename)})
        cands_by_slot = {}
        flavor = self.flavor_var.get()
        deep_pool = self.deep_pool_var.get()
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            logger_callback = lambda msg, tag="": self.after(0, lambda m=msg, t=tag: self.update_console(m, t))
            futures = {executor.submit(simple_search_slot, slot, flavor, deep_pool, self.api_keys, logger_callback, self.stop_event): slot for slot in slots_to_search}
            count = 0
            for future in concurrent.futures.as_completed(futures):
                slot = futures[future]
                try:
                    cands = future.result()
                    count += 1
                    msg = f"[Internal] Slot {count}/{len(slots_to_search)}: {slot['name']} search complete ({len(cands)} candidates found)"
                    self.after(0, lambda m=msg: self.update_console(m))
                    self.after(0, lambda: self.status_label.config(text=f"Searching slots: {count}/{len(slots_to_search)}"))
                    self.after(0, lambda: self.progress.config(value=(count / len(slots_to_search)) * 100))
                    cands_by_slot[slot['name']] = cands
                except Exception as e:
                    error_msg = f"[Error] Slot {slot['name']} search failed: {e}"
                    self.after(0, lambda m=error_msg: self.update_console(m))
        from collections import defaultdict
        slots_cands_by_cat = defaultdict(dict)
        for slot_name, cands in cands_by_slot.items():
            cat = slot_name.split('_')[0].title()
            slots_cands_by_cat[cat][slot_name] = cands
        self.after(0, lambda: self.create_tabbed_view(slots_cands_by_cat, self.manual_var.get()))

    def _run_generation(self, items: List[Dict[str, Any]], api_keys: List[str], volume_settings: VolumeSettings, normalize: bool, randomize: bool, trim: bool, length_config: LengthConfig) -> None:
        self.console_queue.put("Worker thread started")
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            self.console_queue.put("Executor created")
            futures_to_items = {executor.submit(process_item, item, api_keys, normalize, randomize, self.output_dir, lambda msg: self.console_queue.put(msg), trim, volume_settings, length_config, manual_vol=item.get('manual_vol')): item for item in items}  # type: ignore[misc]
            self.console_queue.put(f"Submitted {len(futures_to_items)} tasks")
            completed = 0
            self.console_queue.put("Entering as_completed")
            for future in concurrent.futures.as_completed(futures_to_items):
                item = futures_to_items[future]
                self.console_queue.put(f"Future done for {item['filename']}")
                try:
                    success = future.result()
                    item['status'] = 'success' if success else 'skipped'
                except:
                    item['status'] = 'skipped'
                completed += 1
                self.console_queue.put(("progress", completed, len(items), item))
        self.console_queue.put(("finish", items))

    def run_generation_threaded(self, items: List[Dict[str, Any]], api_keys: List[str], volume_settings: VolumeSettings, normalize: bool, randomize: bool, trim: bool, length_config: LengthConfig) -> None:
        def worker():
            self._run_generation(items, api_keys, volume_settings, normalize, randomize, trim, length_config)
        threading.Thread(target=worker, daemon=True).start()

    def poll_console(self) -> None:
        try:
            while True:
                item = self.console_queue.get_nowait()
                if isinstance(item, tuple):
                    if item[0] == "progress":
                        self.update_progress(item[1], item[2], item[3])
                    elif item[0] == "finish":
                        self.finish_generation(item[1])
                    else:
                        msg, tag = item
                        self.update_console(msg, tag)
                else:
                    self.update_console(item)
        except queue.Empty:
            pass
        self.after(100, self.poll_console)

    def update_console(self, msg: str, tag: str = "") -> None:
        if not tag:
            if "SUCCESS" in msg or "Generated successfully" in msg:
                tag = "success"
            elif "SKIPPED" in msg or "Skipped:" in msg:
                tag = "skipped"
            elif "Query:" in msg or "Searching for" in msg:
                tag = "query"
            else:
                tag = "info"
        self.console.config(state='normal')
        self.console.insert(tk.END, msg + "\n", tag)
        self.console.see(tk.END)
        self.console.config(state='disabled')
        self.console.update_idletasks()

    def update_progress(self, completed: int, total: int, item: Dict[str, Any]) -> None:
        self.progress['value'] = completed
        self.status_label.config(text=f"Processed {completed}/{total}")
        self.update_console(f"Processed {item['filename']}: {'success' if item['status'] == 'success' else 'skipped'}")

    def finish_generation(self, items: List[Dict[str, Any]]) -> None:
        self.gen_btn.config(state='normal')
        self.status_label.config(text="Done")
        # Summary
        success_count = sum(1 for i in items if i['status'] == 'success')
        messagebox.showinfo("Done", f"Generated {success_count}/{len(items)} SFX. Check {self.output_dir}")



# Removed unused methods

    def create_tabbed_view(self, slots_cands_by_cat: Dict[str, Dict[str, List[Candidate]]], is_manual: bool):
        # Clear notebook
        for tab_id in self.notebook.tabs():
            self.notebook.forget(tab_id)
        for cat, slots_cands in slots_cands_by_cat.items():
            build_category_scrollable(self.notebook, cat, slots_cands, self.selections, self.allow_multiple_var.get())
        if is_manual:
            self.confirm_btn.pack(side=tk.LEFT, padx=10)
        else:
            self.confirm_btn.pack_forget()
        self.gen_btn.config(state='normal')
        self.update_console("Tables ready. Adjust volumes and confirm.")
        self.notebook.update()
        self.update()



    def read_selections_and_continue(self):
        self.update_console("Starting generation...")
        for item in self.items:
            slot_name = item['slot_name']
            if slot_name in self.selections and self.selections[slot_name]:
                if self.allow_multiple_var.get():
                    selected_ids = list(self.selections[slot_name].keys())
                    if selected_ids:
                        sel_id = random.choice(selected_ids)
                        item['manual_id'] = sel_id
                        item['manual_vol'] = self.selections[slot_name][sel_id]
                else:
                    sel_id = next(iter(self.selections[slot_name]))
                    item['manual_id'] = sel_id
                    item['manual_vol'] = self.selections[slot_name][sel_id]
        self.confirm_btn.pack_forget()
        if self.selections:
            self.export_btn.config(state='normal')
        normalize = self.normalize.get()
        randomize = self.randomize.get()
        trim = self.trim.get()
        length_config = self.length_config
        self.after(0, lambda: self.run_generation_threaded(self.items, self.api_keys, self.volume_settings, normalize, randomize, trim, length_config))

    def export_pack(self):
        confirmed = []
        for slot_name, sel in self.selections.items():
            for id, vol in sel.items():
                confirmed.append({
                    'slot_name': slot_name,
                    'id': id,
                    'path': f"temp_{id}.wav",
                    'category': slot_name.split('_')[0].title()
                })
        from utils.exporter import package_assets
        package_assets(confirmed, self.output_dir, self.update_console)



if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--headless':
        run_headless()
    else:
        app = SFXClankerGUI()
        app.mainloop()
