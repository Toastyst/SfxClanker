import json
import os
import time
from datetime import datetime
from typing import Dict, List, TypedDict, Any, Optional
import requests
from utils.sfx_library import SFXLibrary
from utils.search import weighted_search_freesound
from utils.query_builder import build_search_query, enhance_query

class CacheEntry(TypedDict):
    good_ids: List[str]
    last_updated: str

def get_sound_by_id(sound_id: str, token: str) -> Dict[str, Any] | None:
    url = f'https://freesound.org/apiv2/sounds/{sound_id}/'
    params = {'token': token, 'fields': 'id,name,previews,duration,num_downloads'}
    for _ in range(3):
        try:
            resp = requests.get(url, params=params, timeout=60)
            time.sleep(1.5)
            if resp.status_code == 200:
                result = resp.json()
                return result  # type: ignore
        except:
            pass
    return None

def load_cache(token: str, skip_validate: bool = False) -> Dict[str, CacheEntry]:
    if not os.path.exists('cache.json'):
        return {}
    try:
        with open('cache.json') as f:
            cache: Dict[str, CacheEntry] = json.load(f)
        if skip_validate:
            return cache
        print(f"Validating cache ({len(cache)} files)...")
        # Validate IDs
        for filename, entry in list(cache.items()):
            good_ids = []
            for id_str in entry['good_ids']:
                result = get_sound_by_id(id_str, token)
                if result and result.get('duration', 0) < 4 and result.get('num_downloads', 0) > 5 and (result.get('previews', {}).get('preview-hq-mp3') or result.get('previews', {}).get('preview-lq-mp3')):
                    good_ids.append(id_str)
            if good_ids:
                entry['good_ids'] = good_ids
            else:
                del cache[filename]
        return cache
    except:
        return {}

def save_cache(cache: Dict[str, CacheEntry]) -> None:
    try:
        with open('cache.json', 'w') as f:
            json.dump(cache, f, indent=2)
    except:
        pass

def populate_cache(token: str, categories: List[str] = ['Combat', 'Movement', 'UI']) -> None:
    sfx = SFXLibrary()
    cache = load_cache(token)
    count = 0
    for cat in categories:
        if cat not in sfx.prompts:
            continue
        for name in sfx.get_names(cat):
            filename = f"{cat.lower()}_{name.lower().replace(' ', '_').replace('/', '_')}.wav"
            if filename in cache and len(cache[filename]['good_ids']) >= 12:
                continue
            prompt = sfx.get_prompt(cat, name)
            if not prompt:
                continue
            fallbacks = prompt['fallbacks']
            queries = [name] + [f"{name} {fb}" for fb in fallbacks[:4]]
            good_ids = set()
            for query in queries:
                if len(good_ids) >= 12:
                    break
                # First try CC0
                results = weighted_search_freesound(query, token, prefer_cc0=True)
                for r in results:
                    id_str = str(r['id'])
                    if id_str not in good_ids:
                        good_ids.add(id_str)
                        if len(good_ids) >= 12:
                            break
                if len(good_ids) < 12:
                    # Then try without CC0 filter
                    results = weighted_search_freesound(query, token, prefer_cc0=False)
                    for r in results:
                        id_str = str(r['id'])
                        if id_str not in good_ids:
                            good_ids.add(id_str)
                            if len(good_ids) >= 12:
                                break
            # If still 0, try very light flavor as last resort
            if len(good_ids) == 0:
                flavored = name + " +dark +fantasy"
                results = weighted_search_freesound(flavored, token, prefer_cc0=True)
                for r in results:
                    id_str = str(r['id'])
                    if id_str not in good_ids:
                        good_ids.add(id_str)
                        if len(good_ids) >= 12:
                            break
                if len(good_ids) < 12:
                    results = weighted_search_freesound(flavored, token, prefer_cc0=False)
                    for r in results:
                        id_str = str(r['id'])
                        if id_str not in good_ids:
                            good_ids.add(id_str)
                            if len(good_ids) >= 12:
                                break
            good_ids_list = list(good_ids)
            if good_ids_list:
                cache[filename] = {'good_ids': good_ids_list, 'last_updated': datetime.now().isoformat()}
                print(f"{filename}: {len(good_ids_list)} good_ids (e.g. {good_ids_list[:3]})")
            else:
                print(f"{filename}: 0 good_ids")
    save_cache(cache)
