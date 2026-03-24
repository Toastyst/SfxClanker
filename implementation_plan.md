# Implementation Plan

[Overview]
Fix the search logic and cache system to achieve 24/24 sound packs with variety on randomize and consistency within packs.

The current issue is 0 sounds due to strict CC0 filter, long queries, no rate limit delay, and empty cache. This plan updates FreeSound API calls for better results (fix filter syntax, shorter queries, delay), adds cache population (store 3-5 good IDs per sound for variety), enforces short sounds (<4s), and tests headless randomize for variety/consistency. Fits existing modular utils structure, maintains one-button flow.

[Types]
No new types needed; use existing Prompt TypedDict, add CacheEntry TypedDict for cache.json.

CacheEntry TypedDict:
- filename: str
- good_ids: List[str]  # 3-5 validated IDs
- last_updated: str  # ISO date

Validation: IDs exist, duration <4s, downloads >10.

[Files]
Update sfxClanker.py for cache save/load, search fixes; update utils/query_builder.py for shorter queries; update README for cache info; no deletions.

- Modified: sfxClanker.py (cache save, search delay, filter fix)
- Modified: utils/query_builder.py (shorter build_search_query)
- Modified: README.md (cache explanation)
- Modified: tests/test_query_builder.py (new test cases)

[Functions]
Update search and cache functions.

Modified functions:
- weighted_search_freesound (sfxClanker.py): Fix 'license:"cc0"', add time.sleep(0.5), relax fallback downloads >5
- process_item (sfxClanker.py): After success, append result['id'] to cache[filename]['good_ids'][:5], save cache.json
- build_search_query (utils/query_builder.py): Limit to 4 words, optional + only for key terms
- load_cache (new in sfxClanker.py): Load cache.json, validate IDs

No removals.

[Classes]
No class changes.

[Dependencies]
Add types-requests for mypy requests stubs.

pip install types-requests

[Testing]
Add tests for cache save/load, new query logic, headless randomize.

- New: tests/test_cache.py (load/save, variety)
- Modified: tests/test_query_builder.py (shorter queries)
- Run pytest/mypy after.

[Implementation Order]
Implement search fixes first, then cache, then test.

1. Update utils/query_builder.py for shorter queries, test.
2. Update weighted_search_freesound in sfxClanker.py (filter, delay), test search.
3. Add cache save/load in process_item, populate good_ids.
4. Update tests, run pytest/mypy.
5. Test headless randomize, verify 24/24, variety.