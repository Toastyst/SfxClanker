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
from utils.query_builder import build_search_query, enhance_query
from utils.audio_processor import process_audio, preview_audio, AudioSegment
from utils.cache import load_cache, save_cache, CacheEntry, get_sound_by_id, populate_cache, clear_cache
from utils.search import weighted_search_freesound

class Candidate(TypedDict):
    id: str
    name: str
    duration: float
    preview_url: str
    rms_loudness: float
    quality_score: float
    tag: str

LengthConfig = Dict[str, float]  # e.g., {'Combat': 1.0, 'UI': 0.5}

class VolumeSettings(TypedDict):
    global_volume: float  # 0.0-2.0 for boost
    loudness_target: float  # dB, e.g., -14.0
    strict_length: bool

def load_api_key() -> str | None:
    try:
        with open('freesound_key.txt', 'r') as f:
            return f.read().strip()
    except:
        return None

def save_api_key(key: str) -> None:
    with open('freesound_key.txt', 'w') as f:
        f.write(key)



def download_sfx(result: Dict[str, Any], path: str) -> bool:
    urls = [result['previews'].get('preview-hq-mp3'), result['previews'].get('preview-lq-mp3')]
    for url in urls:
        if url:
            try:
                resp = requests.get(url, timeout=60)
                if resp.status_code == 200:
                    with open(path, 'wb') as f:
                        f.write(resp.content)
                    return True
            except:
                pass
    return False

def generate_filename(category: str, name: str) -> str:
    clean = re.sub(r'[^a-zA-Z0-9\s/]', '', name).lower().replace(' ', '_').replace('/', '_')
    return f"{category}_{clean}.wav"

def log_message(output_dir: str, msg: str) -> None:
    log_path = os.path.join(output_dir, 'generation_log.txt')
    with open(log_path, 'a') as f:
        f.write(msg + '\n')

def log_failed(output_dir: str, queries: List[str]) -> None:
    path = os.path.join(output_dir, 'failed_queries.txt')
    with open(path, 'a') as f:
        f.write(f"Failed queries: {', '.join(queries)}\n")



def collect_candidates_for_category(category: str, api_key: str, console_callback: Callable, target_cand: int = 12) -> List[Candidate]:
    candidates: List[Candidate] = []
    sfx = SFXLibrary()
    cat_defaults = {'Combat': 'hit', 'Movement': 'step', 'UI': 'click'}
    for name in sfx.get_names(category):
        queries = [name]  # simplified
        for query in queries:
            results, _ = weighted_search_freesound(build_search_query(query), api_key)
            for r in results[:target_cand // len(sfx.get_names(category)) + 1]:
                sound = get_sound_by_id(str(r['id']), api_key)
                if sound and sound.get('duration', 0) < 4:
                    temp_mp3 = f"temp_preview_{r['id']}.mp3"
                    if download_sfx(sound, temp_mp3):
                        temp_audio = AudioSegment.from_file(temp_mp3).set_frame_rate(44100).set_channels(1)
                        rms_db = 20 * math.log10(temp_audio.rms / 32768) if temp_audio.rms > 0 else -60
                        dur = sound['duration']
                        quality_score = (10 - abs(rms_db + 14)) * (1 - abs(dur - 1.2) / 1.2)
                        tag = sound.get('analysis', {}).get('tagstrings', [cat_defaults.get(category, 'sound')])[0]
                        candidates.append({
                            'id': str(sound['id']),
                            'name': sound['name'],
                            'duration': dur,
                            'preview_url': sound['previews'].get('preview-lq-mp3', ''),
                            'rms_loudness': float(rms_db),
                            'quality_score': float(quality_score),
                            'tag': tag
                        })
                        os.remove(temp_mp3)
                    if len(candidates) >= target_cand:
                        break
            if len(candidates) >= target_cand:
                break
    console_callback(f"Category {category}: found {len(candidates)}/{target_cand}")
    return candidates

# RANDOM MODE: pick from top 5 for funny packs
def process_item(item: Dict[str, Any], api_key: str, normalize: bool, random_mode: bool, output_dir: str, console_callback: Callable[[str], None], trim: bool = False,
                 volume_settings: Optional[VolumeSettings] = None, length_config: Optional[LengthConfig] = None,
                 manual_candidates: Optional[List[Candidate]] = None, manual_vol: Optional[float] = None) -> bool:
    console_callback("─" * 37)
    console_callback(f"=== {item['filename']} ===")
    console_callback(f"Searching for {item['filename']}...")
    cache = load_cache(api_key, skip_validate=True)
    queries = [item['name']] + item['fallbacks']
    result = None
    used_query = None
    if item.get('id'):
        console_callback(f"Query: predefined ID {item['id']}")
        result = get_sound_by_id(item['id'], api_key)
        if result:
            used_query = f"ID {item['id']}"
            console_callback(f"Found 1 result")
            console_callback(f"Picked ID {item['id']} - {result['name']}")
            is_cc0 = True  # Assume IDs are CC0
        else:
            result = None
    if not result:
        if item['filename'] in cache and cache[item['filename']].get('good_ids'):
            ids = cache[item['filename']]['good_ids'][:]
            console_callback(f"Query: cache hit")
            console_callback(f"Found {len(ids)} cached results")
            if random_mode and ids:
                random_id = random.choice(ids)
                result = get_sound_by_id(random_id, api_key)
                if result:
                    used_query = f"Cache ID {random_id}"
                    console_callback(f"Picked ID {random_id} - {result['name']}")
                    is_cc0 = True
            else:
                # for non-random, try top 3
                random.shuffle(ids)
                for id in ids[:3]:
                    result = get_sound_by_id(id, api_key)
                    if result:
                        used_query = f"Cache ID {id}"
                        console_callback(f"Picked ID {id} - {result['name']}")
                        is_cc0 = True
                        break
    if not result:
        for query in queries:
            boosted = build_search_query(query)
            log_message(output_dir, f"Query for {item['filename']}: {boosted}")
            console_callback(f"Query: {boosted}")
            results, is_cc0 = weighted_search_freesound(boosted, api_key)
            console_callback(f"Found {len(results)} results")
            if results:
                if random_mode:
                    result = random.choice(results)
                else:
                    result = results[0]
                used_query = boosted
                console_callback(f"Picked ID {result['id']} - {result['name']}")
                break
            else:
                is_cc0 = True  # default
    if result and used_query and not used_query.startswith("ID ") and not used_query.startswith("Cache ID "):
        # Populate cache with new good ID
        filename = item['filename']
        if filename not in cache:
            cache[filename] = CacheEntry(good_ids=[], last_updated=datetime.now().isoformat())
        good_ids = cache[filename]['good_ids']
        id_str = str(result['id'])
        if id_str not in good_ids:
            good_ids.append(id_str)
            cache[filename]['good_ids'] = good_ids[-5:]
            cache[filename]['last_updated'] = datetime.now().isoformat()
            save_cache(cache)
    if not result:
        console_callback("Skipped: No results")
        log_failed(output_dir, queries)
        log_message(output_dir, f"Skipped {item['filename']}: no results for any query")
        return False
    if not is_cc0:
        log_message(output_dir, f"NON-CC0: {item['filename']} ({used_query})")
    temp_path = item['path'] + '.temp'
    console_callback(f"Downloading preview...")
    if not download_sfx(result, temp_path):
        console_callback("Skipped: Download failed")
        log_message(output_dir, f"Skipped {item['filename']}: download failed")
        return False
    cat = item['category'].title()  # e.g. 'combat' -> 'Combat'
    max_len = length_config.get(cat, 2.0) if length_config else None
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
    parser.add_argument('--populate-cache', action='store_true', help='Populate cache with good IDs')
    parser.add_argument('--volume', type=float, default=1.0, help='Global volume multiplier (0.0-2.0)')
    parser.add_argument('--loudness', type=float, default=-14.0, help='RMS loudness target (dB)')
    parser.add_argument('--strict-length', action='store_true', help='Strict length trimming with fade')
    parser.add_argument('--manual', action='store_true', help='Manual selection mode (stub: auto-pick)')
    parser.add_argument('--deep-pool', action='store_true', help='Populate deep cache')
    args = parser.parse_args(sys.argv[2:])

    output_dir = args.output
    normalize = args.normalize
    random_mode = args.random
    trim = args.trim
    categories = [c.strip() for c in args.categories.split(',')]

    api_key = load_api_key()
    if not api_key:
        print("Error: No API key found. Run GUI first to set it.")
        sys.exit(1)

    if args.populate_cache:
        print("Populating cache...")
        populate_cache(api_key, categories)
        print("Cache populated.")
        sys.exit(0)

    if args.deep_pool:
        print("Populating deep cache...")
        populate_cache(api_key, categories, deep=True, target=40)
        print("Deep cache populated.")
        sys.exit(0)

    if not output_dir:
        print("Error: --output required for generation")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    sfx = SFXLibrary()
    items = []
    for cat in categories:
        if cat in sfx.prompts:
            for name in sfx.get_names(cat):
                prompt = sfx.get_prompt(cat, name)
                filename = generate_filename(cat, name)
                items.append({'category': cat.lower(), 'name': name, 'fallbacks': prompt['fallbacks'] if prompt else [], 'id': prompt.get('id') if prompt else None, 'filename': filename, 'status': 'pending', 'path': os.path.join(output_dir, filename)})

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
        futures_to_items = {executor.submit(process_item, item, api_key, normalize, random_mode, output_dir, lambda msg: print(f"[{item['filename']}] {msg}"), trim, volume_settings, length_config): item for item in items}  # type: ignore[arg-type,misc]
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
            self.geometry("1450x900")
            self.minsize(1350, 750)
            self.configure(bg='#2b2b2b')
            self.sfx = SFXLibrary()
            self.output_dir = ""
            self.normalize = tk.BooleanVar(value=True)
            self.randomize = tk.BooleanVar(value=False)
            self.trim = tk.BooleanVar(value=False)
            self.volume_var = tk.DoubleVar(value=1.0)
            self.loudness_var = tk.DoubleVar(value=-14.0)
            self.manual_var = tk.BooleanVar(value=False)
            self.strict_var = tk.BooleanVar(value=False)
            self.length_config = {'Combat': 1.0, 'Movement': 1.5, 'UI': 0.5, 'Test': 2.0}
            self.deep_pool_var = tk.BooleanVar(value=False)
            self.allow_multiple_var = tk.BooleanVar(value=False)
            self.hide_preview_var = tk.BooleanVar(value=False)
            self.selections = defaultdict(lambda: defaultdict(float))
            self.manual_frame = tk.Frame(self, bg='#2b2b2b')
            self.console_queue = queue.Queue()
            self.progress = ttk.Progressbar(self, orient="horizontal", mode="determinate")
            self.status_label = tk.Label(self, text="Ready", bg='#2b2b2b', fg='white')
            self.create_widgets()
        except Exception as e:
            messagebox.showerror("Initialization Error", f"Failed to start: {e}")
            self.destroy()

    def create_widgets(self) -> None:
        # Left frame: checklist
        left_frame = tk.Frame(self, bg='#2b2b2b')
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        tk.Label(left_frame, text="Select Categories:", bg='#2b2b2b', fg='white').pack()
        self.check_vars = {}
        for cat in self.sfx.prompts:
            var = tk.BooleanVar(value=True)
            self.check_vars[cat] = var
            chk = tk.Checkbutton(left_frame, text=cat, variable=var, bg='#2b2b2b', fg='white', selectcolor='#3c3c3c')
            chk.pack(anchor='w')
        tk.Button(left_frame, text="Select All", command=self.select_all, bg='#4a4a4a', fg='white').pack(pady=5)

        # Toolbar frame
        toolbar_frame = tk.Frame(self, bg='#2b2b2b')
        toolbar_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Scale(toolbar_frame, from_=0.0, to=2.0, resolution=0.1, orient=tk.HORIZONTAL, variable=self.volume_var, label="Global Volume").pack(side=tk.LEFT, padx=5)
        tk.Scale(toolbar_frame, from_=-20.0, to=0.0, resolution=1.0, orient=tk.HORIZONTAL, variable=self.loudness_var, label="RMS Target (dB)").pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(toolbar_frame, text="Strict Length Trim", variable=self.strict_var, bg='#2b2b2b', fg='white', selectcolor='#3c3c3c').pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(toolbar_frame, text="Manual Selection Mode", variable=self.manual_var, bg='#2b2b2b', fg='white', selectcolor='#3c3c3c').pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(toolbar_frame, text="Deep Pool (40 high-quality IDs)", variable=self.deep_pool_var, bg='#2b2b2b', fg='white', selectcolor='#3c3c3c').pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(toolbar_frame, text="Allow Multiple (random pick from selected)", variable=self.allow_multiple_var, bg='#2b2b2b', fg='white', selectcolor='#3c3c3c').pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar_frame, text="Clear Cache", command=lambda: [clear_cache(), self.update_console("Cache cleared")]).pack(side=tk.LEFT, padx=5)

        # Bottom frame
        bottom_frame = tk.Frame(self, bg='#2b2b2b')
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        tk.Button(bottom_frame, text="Choose Output Folder", command=self.choose_output_dir, bg='#4a4a4a', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(bottom_frame, text="Normalize to -3 dB", variable=self.normalize, bg='#2b2b2b', fg='white', selectcolor='#3c3c3c').pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(bottom_frame, text="Auto-trim silence", variable=self.trim, bg='#2b2b2b', fg='white', selectcolor='#3c3c3c').pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(bottom_frame, text="Randomize sounds each batch (for funny packs)", variable=self.randomize, bg='#2b2b2b', fg='white', selectcolor='#3c3c3c').pack(side=tk.LEFT, padx=5)
        self.gen_btn = tk.Button(bottom_frame, text="GENERATE SOUND PACK", command=self.generate_pack, bg='#00ff00', fg='black', font=('Arial', 14, 'bold'))
        self.gen_btn.pack(side=tk.RIGHT, padx=10)

        # Right frame: preview
        self.preview_frame = tk.Frame(self, bg='#2b2b2b', width=200)
        self.preview_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=10)
        tk.Label(self.preview_frame, text="Previews (after generation)", bg='#2b2b2b', fg='white').pack()
        tk.Checkbutton(self.preview_frame, text="Hide Previews", variable=self.hide_preview_var, bg='#2b2b2b', fg='white', selectcolor='#3c3c3c', command=self.toggle_preview).pack()
        self.preview_list = tk.Frame(self.preview_frame, bg='#2b2b2b')
        self.preview_list.pack(fill=tk.BOTH, expand=True)

        # Progress and status
        self.progress.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        self.status_label.pack(side=tk.BOTTOM, padx=10, pady=5)
        # Console
        self.console = tk.Text(self, height=25, bg='#1e1e1e', fg='white', insertbackground='white')
        self.console.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.console.insert(tk.END, "Console output:\n")
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

    def generate_pack(self) -> None:
        if not self.output_dir:
            messagebox.showerror("Error", "Choose output folder first")
            return
        api_key = load_api_key()
        if not api_key:
            api_key = simpledialog.askstring("API Key", "Enter FreeSound API key:")
            if not api_key:
                return
            save_api_key(api_key)
        # Get selected items
        items = []
        for cat, var in self.check_vars.items():
            if var.get():
                for name in self.sfx.get_names(cat):
                    prompt = self.sfx.get_prompt(cat, name)
                    filename = generate_filename(cat, name)
                    items.append({'category': cat.lower(), 'name': name, 'fallbacks': prompt['fallbacks'] if prompt else [], 'id': prompt.get('id') if prompt else None, 'filename': filename, 'status': 'pending', 'path': os.path.join(self.output_dir, filename)})
        if not items:
            messagebox.showerror("Error", "Select at least one category")
            return
        self.gen_btn.config(state='disabled')
        self.progress['maximum'] = len(items)
        self.progress['value'] = 0
        self.status_label.config(text="Generating...")
        # Clear preview
        for widget in self.preview_list.winfo_children():
            widget.destroy()
        # Volume settings
        volume_settings = {
            'global_volume': self.volume_var.get(),
            'loudness_target': self.loudness_var.get(),
            'strict_length': self.strict_var.get()
        }
        if self.deep_pool_var.get():
            populate_cache(api_key, [cat for cat, var in self.check_vars.items() if var.get()], deep=True, target=40)
            self.update_console("Deep cache populated")
        if self.manual_var.get():
            self.items = items
            self.api_key = api_key
            self.volume_settings = volume_settings
            self.manual_frame.pack(fill=tk.BOTH, expand=True, before=self.console)
            def collect_cands():
                cands_by_cat = {}
                selected_cats = [cat for cat, var in self.check_vars.items() if var.get()]
                for cat in selected_cats:
                    cands = collect_candidates_for_category(cat, api_key, self.update_console)
                    cands_by_cat[cat] = cands
                self.after(0, lambda: self.create_tabbed_manual_view(cands_by_cat))
            threading.Thread(target=collect_cands, daemon=True).start()
            return
        # Normal mode
        self.update_console(f"Found {len(items)} items for generation")
        self.update_console("Starting generation...")
        normalize = self.normalize.get()
        randomize = self.randomize.get()
        trim = self.trim.get()
        length_config = self.length_config
        self.run_generation_threaded(items, api_key, volume_settings, normalize, randomize, trim, length_config)

    def _run_generation(self, items: List[Dict[str, Any]], api_key: str, volume_settings: VolumeSettings, normalize: bool, randomize: bool, trim: bool, length_config: LengthConfig) -> None:
        self.console_queue.put("Worker thread started")
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            self.console_queue.put("Executor created")
            futures_to_items = {executor.submit(process_item, item, api_key, normalize, randomize, self.output_dir, lambda msg: self.console_queue.put(msg), trim, volume_settings, length_config, manual_vol=item.get('manual_vol')): item for item in items}  # type: ignore[misc]
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

    def run_generation_threaded(self, items: List[Dict[str, Any]], api_key: str, volume_settings: VolumeSettings, normalize: bool, randomize: bool, trim: bool, length_config: LengthConfig) -> None:
        def worker():
            self._run_generation(items, api_key, volume_settings, normalize, randomize, trim, length_config)
        threading.Thread(target=worker, daemon=True).start()

    def poll_console(self) -> None:
        try:
            while True:
                msg = self.console_queue.get_nowait()
                if isinstance(msg, tuple):
                    if msg[0] == "progress":
                        self.update_progress(msg[1], msg[2], msg[3])
                    elif msg[0] == "finish":
                        self.finish_generation(msg[1])
                else:
                    self.update_console(msg)
        except queue.Empty:
            pass
        self.after(100, self.poll_console)

    def update_console(self, msg: str) -> None:
        self.console.insert(tk.END, msg + "\n")
        self.console.see(tk.END)
        self.console.update()

    def update_progress(self, completed: int, total: int, item: Dict[str, Any]) -> None:
        self.progress['value'] = completed
        self.status_label.config(text=f"Processed {completed}/{total}")
        self.update_console(f"Processed {item['filename']}: {'success' if item['status'] == 'success' else 'skipped'}")

    def finish_generation(self, items: List[Dict[str, Any]]) -> None:
        self.gen_btn.config(state='normal')
        self.status_label.config(text="Done")
        # Populate preview
        for item in items:
            if item['status'] == 'success':
                btn = tk.Button(self.preview_list, text=f"Play {item['filename']}", command=lambda p=item['path']: self.on_preview(p), bg='#4a4a4a', fg='white')
                btn.pack(fill=tk.X, pady=2)
        # Summary
        success_count = sum(1 for i in items if i['status'] == 'success')
        messagebox.showinfo("Done", f"Generated {success_count}/{len(items)} SFX. Check {self.output_dir}")

    def on_preview(self, path: str) -> None:
        preview_audio(path)

    def toggle_preview(self) -> None:
        if self.hide_preview_var.get():
            self.preview_list.pack_forget()
        else:
            self.preview_list.pack(fill=tk.BOTH, expand=True)

    def build_candidate_table(self, parent_frame: tk.Frame, category: str, candidates: List[Candidate], selections: Dict[str, Dict[str, float]], allow_multiple: bool) -> None:
        # ScrolledFrame
        canvas = tk.Canvas(parent_frame, bg='#2b2b2b', highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg='#2b2b2b')
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        # Headers
        tk.Label(scroll_frame, text="Select", bg='#2b2b2b', fg='white', font=('Arial', 10, 'bold')).grid(row=0, column=0, padx=10, pady=10)
        tk.Label(scroll_frame, text="Sound • Tag • Dur", bg='#2b2b2b', fg='white', font=('Arial', 10, 'bold')).grid(row=0, column=1, padx=10, pady=10)
        tk.Label(scroll_frame, text="Vol", bg='#2b2b2b', fg='white', font=('Arial', 10, 'bold')).grid(row=0, column=2, padx=10, pady=10)
        tk.Label(scroll_frame, text="Preview", bg='#2b2b2b', fg='white', font=('Arial', 10, 'bold')).grid(row=0, column=3, padx=10, pady=10)
        row = 1
        for cand in candidates:
            id_str = cand['id']
            # Checkbox
            var = tk.BooleanVar(value=False)
            chk = tk.Checkbutton(scroll_frame, variable=var, bg='#2b2b2b', fg='white', selectcolor='#3c3c3c')
            chk.grid(row=row, column=0, padx=10, pady=10)
            # Label
            label_text = f"{cand['name']} • {cand['tag']} • {cand['duration']:.1f}s"
            tk.Label(scroll_frame, text=label_text, bg='#2b2b2b', fg='white').grid(row=row, column=1, padx=10, pady=10, sticky='w')
            # Scale
            scale = tk.Scale(scroll_frame, from_=0.5, to=2.0, resolution=0.1, orient=tk.HORIZONTAL, bg='#2b2b2b', fg='white')
            scale.set(1.0)
            scale.grid(row=row, column=2, padx=10, pady=10)
            # Preview btn
            def preview(url=cand['preview_url'], id=id_str):
                if url:
                    temp = f"temp_{id}.mp3"
                    try:
                        resp = requests.get(url, timeout=10)
                        if resp.status_code == 200:
                            with open(temp, 'wb') as f:
                                f.write(resp.content)
                            preview_audio(temp)
                            os.remove(temp)
                    except:
                        pass
            btn = tk.Button(scroll_frame, text="Play", command=preview, bg='#4a4a4a', fg='white')
            btn.grid(row=row, column=3, padx=10, pady=10)
            # Store selections
            def on_check(var=var, scale=scale, id=id_str):
                if var.get():
                    selections[category][id] = scale.get()
                else:
                    selections[category].pop(id, None)
            var.trace_add('write', lambda *args, var=var, scale=scale, id=id_str: on_check(var, scale, id))
            scale.config(command=lambda v, id=id_str: selections[category].__setitem__(id, float(v)) if id in selections[category] else None)
            row += 1
        scroll_frame.grid_columnconfigure(1, weight=1)

    def create_tabbed_manual_view(self, cands_by_cat: Dict[str, List[Candidate]]):
        tk.Label(self.manual_frame, text="Select sounds below (check + adjust volume)", bg='#2b2b2b', fg='white', font=('Arial', 12, 'bold')).pack(pady=10)
        notebook = ttk.Notebook(self.manual_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        for cat, cands in cands_by_cat.items():
            tab = tk.Frame(notebook, bg='#2b2b2b')
            notebook.add(tab, text=cat)
            self.build_candidate_table(tab, cat, cands, self.selections, self.allow_multiple_var.get())
        # Confirm btn
        confirm_btn = tk.Button(self.manual_frame, text="Confirm Selections", command=self.read_selections_and_continue, bg='#00ff00', fg='black', font=('Arial', 14, 'bold'), height=2, width=20)
        confirm_btn.pack(side=tk.BOTTOM, pady=10)

    def read_selections_and_continue(self):
        for item in self.items:
            cat = item['category'].title()
            if cat in self.selections and self.selections[cat]:
                if self.allow_multiple_var.get():
                    selected_ids = list(self.selections[cat].keys())
                    if selected_ids:
                        sel_id = random.choice(selected_ids)
                        item['manual_id'] = sel_id
                        item['manual_vol'] = self.selections[cat][sel_id]
                else:
                    sel_id = next(iter(self.selections[cat]))
                    item['manual_id'] = sel_id
                    item['manual_vol'] = self.selections[cat][sel_id]
        self.manual_frame.pack_forget()
        normalize = self.normalize.get()
        randomize = self.randomize.get()
        trim = self.trim.get()
        length_config = self.length_config
        self.after(0, lambda: self.run_generation_threaded(self.items, self.api_key, self.volume_settings, normalize, randomize, trim, length_config))



if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--headless':
        run_headless()
    else:
        app = SFXClankerGUI()
        app.mainloop()
