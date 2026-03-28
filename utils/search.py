import time
import math
import random
import json
from typing import List, Dict, Any, Tuple, TypedDict, Optional
import requests
from utils.slots import Slot
from utils.query_builder import simple_query

class Candidate(TypedDict):
    id: str
    name: str
    duration: float
    preview_url: str
    downloads: int
    quality_score: float
    analysis: Dict[str, Any]

request_counter = 0

def simple_score(result: Dict[str, Any]) -> float:
    target_dur = 1.2
    dur_score = max(0, 10 - abs(result['duration'] - target_dur) * 5)
    dl_score = math.log(result['num_downloads'] + 1) * 2
    return dl_score + dur_score

def load_cache() -> Dict[str, List[Candidate]]:
    try:
        with open('cache.json', 'r') as f:
            return json.load(f)
    except:
        return {}

def save_cache(cache: Dict[str, List[Candidate]]):
    with open('cache.json', 'w') as f:
        json.dump(cache, f, indent=2)

def to_candidate(r: Dict[str, Any]) -> Candidate:
    return {
        'id': str(r['id']),
        'name': r['name'],
        'duration': r['duration'],
        'preview_url': r['previews'].get('preview-lq-mp3', ''),
        'downloads': r['num_downloads'],
        'quality_score': simple_score(r),
        'analysis': r.get('analysis', {})
    }

def weighted_search_freesound(query: str, tokens: List[str], target: int = 30, prefer_cc0: bool = True, api_filter: str = "", logger_callback=None, stop_event=None) -> Tuple[List[Dict[str, Any]], bool]:
    global request_counter
    if stop_event and stop_event.is_set():
        if logger_callback:
            logger_callback("[System] Thread Aborted")
        return [], True
    sleep_multiplier = [1.0]
    for token in tokens:
        base_url = 'https://freesound.org/apiv2/search/text/'
        params = {'token': token, 'query': query, 'sort': 'downloads_desc,rating_desc', 'fields': 'id,name,previews,duration,num_downloads,license,analysis', 'filter': api_filter or "duration:[0.1 TO 4.0]"}
        if prefer_cc0:
            params['filter'] += ';license:cc0'
        for attempt in range(3):
            try:
                jitter = (2.0 + random.uniform(0, 2.0)) * sleep_multiplier[0]
                time.sleep(jitter)
                if logger_callback:
                    logger_callback(f"[API] Searching Freesound for: '{query}' using Key {tokens.index(token)}...")
                resp = requests.get(base_url, params=params, timeout=60)
                request_counter += 1
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
                    results = [r for r in data['results'] if r['duration'] < 4 and r['num_downloads'] > 10][:target]
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

def simple_search_slot(slot: Slot, flavor: str = "", deep_pool: bool = False, tokens: List[str] = [], logger_callback=None, stop_event=None) -> List[Candidate]:
    if stop_event and stop_event.is_set():
        if logger_callback:
            logger_callback("[System] Thread Aborted")
        return []
    if logger_callback:
        logger_callback(f"[API] Searching {slot['name']} ({slot['category']})...")
    # Build query chain: main, each fallback, broad
    main_query = simple_query(slot, flavor)
    queries = [main_query] + slot['fallbacks'] + [slot['display_name']]
    all_results = []
    successful_query = None
    for i, query in enumerate(queries):
        if stop_event and stop_event.is_set():
            break
        if i == 0:
            if logger_callback:
                logger_callback(f"[API] Trying main query: {query}")
        elif i <= len(slot['fallbacks']):
            if logger_callback:
                logger_callback(f"[API] Main query failed → trying fallback {i}/{len(slot['fallbacks'])}: {query}")
        else:
            if logger_callback:
                logger_callback(f"[API] Fallbacks failed → trying broad query: {query}")
        if deep_pool:
            cache = load_cache()
            cached = cache.get(slot['name'], [])
            good_cached = [c for c in cached if c['downloads'] > 10 and c['duration'] < 4]
            if len(good_cached) >= 50 or request_counter > 60:
                return sorted(good_cached, key=lambda c: c['quality_score'], reverse=True)[:50]
            results, _ = weighted_search_freesound(query, tokens, target=50, prefer_cc0=True, api_filter="duration:[0.5 TO 2.5];num_downloads:>20", logger_callback=logger_callback, stop_event=stop_event)
        else:
            results, _ = weighted_search_freesound(query, tokens, target=30, prefer_cc0=True, logger_callback=logger_callback, stop_event=stop_event)
        if results:
            all_results.extend(results)
            successful_query = query
            if logger_callback:
                logger_callback(f"[API] Success with query: {successful_query} ({len(results)} results)")
            break
    # Sort by downloads desc
    all_results = sorted(all_results, key=lambda r: r['num_downloads'], reverse=True)
    if not all_results:
        if logger_callback:
            logger_callback(f"[API] No results found for {slot['name']} after all queries")
        return []
    # For deep pool, cache the results
    if deep_pool and successful_query:
        new_cands = [to_candidate(r) for r in all_results]
        cache = load_cache()
        cached = cache.get(slot['name'], [])
        good_cached = [c for c in cached if c['downloads'] > 10 and c['duration'] < 4]
        all_cands = good_cached + new_cands
        unique_cands = list({c['id']: c for c in all_cands}.values())
        sorted_cands = sorted(unique_cands, key=lambda c: c['quality_score'], reverse=True)[:50]
        cache[slot['name']] = sorted_cands
        save_cache(cache)
        return sorted_cands
    else:
        return [to_candidate(r) for r in all_results]

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
