import time
from typing import List, Dict, Any, Tuple
import requests

def weighted_search_freesound(query: str, token: str, prefer_cc0: bool = False) -> List[Dict[str, Any]]:
    base_url = 'https://freesound.org/apiv2/search/text/'
    params = {'token': token, 'query': query, 'sort': 'downloads_desc,rating_desc', 'fields': 'id,name,previews,duration,num_downloads,license'}
    if prefer_cc0:
        params['filter'] = 'license:cc0'
    for _ in range(1):
        try:
            resp = requests.get(base_url, params=params, timeout=60)
            time.sleep(1.5)
            if resp.status_code == 200:
                data = resp.json()
                results = [r for r in data['results'] if r['duration'] < 4 and r['num_downloads'] > 5][:30]
                return results
        except:
            pass
    return []
