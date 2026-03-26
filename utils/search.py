import time
import math
import random
from typing import List, Dict, Any, Tuple, TypedDict, Optional
import requests
from utils.slots import Slot
from utils.query_builder import build_slot_query, enhance_query, get_flavor_query

class Candidate(TypedDict):
    id: str
    name: str
    duration: float
    preview_url: str
    downloads: int
    quality_score: float
    analysis: Dict[str, Any]

def weighted_search_freesound(query: str, tokens: List[str], prefer_cc0: bool = False, filter: str = "duration:[0.1 TO 3.0]", logger_callback=None, stop_event=None) -> Tuple[List[Dict[str, Any]], bool]:
    if stop_event and stop_event.is_set():
        if logger_callback:
            logger_callback("[System] Thread Aborted")
        return [], True
    sleep_multiplier = [1.0]
    for token in tokens:
        base_url = 'https://freesound.org/apiv2/search/text/'
        params = {'token': token, 'query': query, 'sort': 'downloads_desc,rating_desc', 'fields': 'id,name,previews,duration,num_downloads,license,analysis', 'filter': filter}
        if prefer_cc0:
            params['filter'] += ';license:cc0'
        for attempt in range(3):
            try:
                jitter = (2.0 + random.uniform(0, 2.0)) * sleep_multiplier[0]
                time.sleep(jitter)
                if logger_callback:
                    logger_callback(f"[API] Searching Freesound for: '{query}' using Key {tokens.index(token)}...")
                resp = requests.get(base_url, params=params, timeout=60)
                if resp.status_code == 429:
                    if logger_callback:
                        logger_callback("[Warning] Rate limit hit. Increasing delay...")
                    sleep_multiplier[0] *= 2
                    time.sleep(5)
                    continue
                if resp.status_code == 504:
                    if logger_callback:
                        logger_callback("[RETRY] Freesound busy... waiting 5s")
                    time.sleep(5)
                    continue
                if resp.status_code == 200:
                    data = resp.json()
                    results = [r for r in data['results'] if r['duration'] < 4 and r['num_downloads'] > 5 and ('analysis' not in r or r['analysis'].get('ac_loudness_mean', 0) >= -30)][:30]
                    is_cc0 = prefer_cc0 or all(r.get('license') == 'cc0' for r in results)
                    return results, is_cc0
            except requests.Timeout:
                if logger_callback:
                    logger_callback("[RETRY] Freesound timeout... waiting 5s")
                time.sleep(5)
                continue
            except Exception as e:
                if logger_callback:
                    logger_callback(f"[ERROR] API request failed: {e}")
                break
    return [], True

def search_slot(slot: Slot, tokens: List[str], logger_callback=None, stop_event=None) -> List[Candidate]:
    if stop_event and stop_event.is_set():
        if logger_callback:
            logger_callback("[System] Thread Aborted")
        return []
    query = build_slot_query(slot)
    enhanced = enhance_query(query)
    if logger_callback:
        logger_callback(f"[API] Searching {slot['name']} ({slot['category']} - Gritty Medieval)...")
    results, _ = weighted_search_freesound(enhanced, tokens, logger_callback=logger_callback, stop_event=stop_event)
    if not results:
        return []
    max_downloads = max(r['num_downloads'] for r in results) or 1
    candidates = []
    for r in results:
        dur_score = 10 - abs(r['duration'] - 1.2) / 1.2 * 5
        dl_score = math.log(r['num_downloads'] + 1) / math.log(max_downloads + 1) * 5 if max_downloads > 1 else 0
        quality_score = dur_score + dl_score
        candidates.append({
            'id': str(r['id']),
            'name': r['name'],
            'duration': r['duration'],
            'preview_url': r['previews'].get('preview-lq-mp3', ''),
            'downloads': r['num_downloads'],
            'quality_score': quality_score,
            'analysis': r.get('analysis', {})
        })
    candidates.sort(key=lambda c: c['quality_score'], reverse=True)
    return candidates

def get_sound_by_id(sound_id: str, tokens: List[str]) -> Optional[Dict[str, Any]]:
    for token in tokens:
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
