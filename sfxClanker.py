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
from datetime import datetime
from typing import List, Dict, Tuple, TypedDict, Any, Callable
from utils.sfx_library import SFXLibrary
from utils.query_builder import build_search_query, enhance_query
from utils.audio_processor import process_audio, preview_audio
from utils.cache import load_cache, save_cache, CacheEntry, get_sound_by_id, populate_cache
from utils.search import weighted_search_freesound

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

# RANDOM MODE: pick from top 5 for funny packs
def process_item(item: Dict[str, Any], api_key: str, normalize: bool, random_mode: bool, output_dir: str, console_callback: Callable[[str], None], trim: bool = False) -> bool:
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
    console_callback(f"Processing audio (normalize={normalize}, trim={trim})...")
    result_proc = process_audio(temp_path, item['path'], normalize, trim)
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

    print(f"Generating {len(items)} SFX to {output_dir}...")
    success_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures_to_items = {executor.submit(process_item, item, api_key, normalize, random_mode, output_dir, lambda msg: print(f"[{item['filename']}] {msg}"), trim): item for item in items}  # type: ignore[arg-type,misc]
        for future in concurrent.futures.as_completed(futures_to_items):
            item = futures_to_items[future]
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
            self.geometry("1000x600")
            self.configure(bg='#2b2b2b')
            self.sfx = SFXLibrary()
            self.output_dir = ""
            self.normalize = tk.BooleanVar(value=True)
            self.randomize = tk.BooleanVar(value=False)
            self.trim = tk.BooleanVar(value=False)
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

        # Bottom frame
        bottom_frame = tk.Frame(self, bg='#2b2b2b')
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        tk.Button(bottom_frame, text="Choose Output Folder", command=self.choose_output_dir, bg='#4a4a4a', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(bottom_frame, text="Normalize to -3 dB", variable=self.normalize, bg='#2b2b2b', fg='white', selectcolor='#3c3c3c').pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(bottom_frame, text="Auto-trim silence", variable=self.trim, bg='#2b2b2b', fg='white', selectcolor='#3c3c3c').pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(bottom_frame, text="Randomize sounds each batch (for funny packs)", variable=self.randomize, bg='#2b2b2b', fg='white', selectcolor='#3c3c3c').pack(side=tk.LEFT, padx=5)
        self.gen_btn = tk.Button(bottom_frame, text="GENERATE SOUND PACK", command=self.generate_pack, bg='#00ff00', fg='black', font=('Arial', 14, 'bold'))
        self.gen_btn.pack(side=tk.RIGHT, padx=5)

        # Right frame: preview
        self.preview_frame = tk.Frame(self, bg='#2b2b2b')
        self.preview_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)
        tk.Label(self.preview_frame, text="Previews (after generation)", bg='#2b2b2b', fg='white').pack()
        self.preview_list = tk.Frame(self.preview_frame, bg='#2b2b2b')
        self.preview_list.pack(fill=tk.BOTH, expand=True)

        # Progress and status
        self.progress.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        self.status_label.pack(side=tk.BOTTOM, padx=10, pady=5)
        # Console
        self.console = tk.Text(self, height=25, bg='#1e1e1e', fg='white', insertbackground='white')
        self.console.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.console.insert(tk.END, "Console output:\n")

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
        # Thread
        def worker() -> None:
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                futures_to_items = {executor.submit(process_item, item, api_key, self.normalize.get(), self.randomize.get(), self.output_dir, lambda msg: self.after(0, lambda: self.update_console(msg)), self.trim.get()): item for item in items}  # type: ignore[misc]
                completed = 0
                for future in concurrent.futures.as_completed(futures_to_items):
                    item = futures_to_items[future]
                    try:
                        success = future.result()
                        item['status'] = 'success' if success else 'skipped'
                    except:
                        item['status'] = 'skipped'
                    self.after(0, lambda: self.update_console(f"Processed {item['filename']}: {'success' if item['status'] == 'success' else 'skipped'}"))  # type: ignore[misc]
                    completed += 1
                    self.progress['value'] = completed
                    self.status_label.config(text=f"Processed {completed}/{len(items)}")
                    self.update()
            # Post
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
        threading.Thread(target=worker, daemon=True).start()

    def update_console(self, msg: str) -> None:
        self.console.insert(tk.END, msg + "\n")
        self.console.see(tk.END)

    def on_preview(self, path: str) -> None:
        preview_audio(path)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--headless':
        run_headless()
    else:
        app = SFXClankerGUI()
        app.mainloop()
