import json
import os
from datetime import datetime
from typing import Dict, List, TypedDict
import requests

class CacheEntry(TypedDict):
    good_ids: List[str]
    last_updated: str

def get_sound_by_id(sound_id: str, token: str) -> Dict:
    url = f'https://freesound.org/apiv2/sounds/{sound_id}/'
    params = {'token': token, 'fields': 'id,name,previews,duration,num_downloads'}
    for _ in range(3):
        try:
            resp = requests.get(url, params=params, timeout=60)
            if resp.status_code == 200:
                result = resp.json()
                return result
        except:
            pass
    return None

def load_cache(token: str) -> Dict[str, CacheEntry]:
    if not os.path.exists('cache.json'):
        return {}
    try:
        with open('cache.json') as f:
            cache: Dict[str, CacheEntry] = json.load(f)
        # Validate IDs
        for filename, entry in list(cache.items()):
            good_ids = []
            for id_str in entry['good_ids']:
                result = get_sound_by_id(id_str, token)
                if result and result.get('duration', 0) < 4 and result.get('num_downloads', 0) > 10 and (result.get('previews', {}).get('preview-hq-mp3') or result.get('previews', {}).get('preview-lq-mp3')):
                    good_ids.append(id_str)
            if good_ids:
                entry['good_ids'] = good_ids
            else:
                del cache[filename]
        return cache
    except:
        return {}

def save_cache(cache: Dict[str, CacheEntry]):
    try:
        with open('cache.json', 'w') as f:
            json.dump(cache, f, indent=2)
    except:
        pass