import requests
import os
import re
from typing import Dict, Any

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