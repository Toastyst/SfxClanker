# Implementation Plan

[Overview]
Simplify search and cache to broad simple queries, optional user flavor, client-side filtering, Deep Pool opt-in for larger pools, no auto-flavor complexity.

The current search uses FlavorManager auto-tags from flavor_profiles.json, enhance_query (empty), quality_score, client filter in weighted_search_freesound. process_item uses simple build_search_query + weighted_search_freesound. No cache.py, cache.json unused. GUI has no flavor input or Deep Pool chk.

New design: Core search broad (name + fallbacks[:2]), optional flavor text append, client filter dur<4 dl>10 CC0 prefer, simple score dl + dur closeness. Deep Pool: target 50, stricter filter. GUI: flavor text field, Deep Pool chk.

Preserve UI/generation flow, headless.

[Types]
No new types; reuse Candidate, add DeepPoolConfig(TypedDict): {'deep': bool, 'target': int = 50}.

[Files]
Modify sfxClanker.py (GUI flavor/Deep Pool input), utils/search.py (simplified weighted_search_freesound, search_slot), utils/query_builder.py (simple build_search_query, remove FlavorManager/build_slot_query), create utils/cache.py (Deep Pool logic, cache.json).

No deletions.

[Functions]
Modified:
- utils/search.py: weighted_search_freesound (broad query, client filter dl>10 dur<4 prefer CC0, simple score dl + dur closeness, deep param for target).
- utils/search.py: search_slot (use simple query, optional flavor, deep).
- utils/query_builder.py: build_search_query (keep simple, remove special rules if not needed).
- utils/query_builder.py: remove enhance_query, build_slot_query, FlavorManager, get_flavor_query.
- utils/cache.py: new populate_cache(slot, deep: bool, target: int) -> List[Candidate] (cache.json, larger for deep).
- sfxClanker.py: generate_pack (add self.deep_pool_var, self.flavor_var, pass to search_slot).
- sfxClanker.py: create_widgets (add Deep Pool chk, flavor text field in top toolbar).

[Classes]
No class changes.

[Dependencies]
No changes.

[Testing]
- Normal: fast, broad results.
- Deep Pool ON: 50 candidates per slot.
- Flavor input: appends to query.
- Headless unchanged.
- pytest tests/, mypy .

[Implementation Order]
1. Create utils/cache.py with populate_cache (read/write cache.json, deep target 50).
2. Simplify utils/query_builder.py: keep build_search_query simple, remove FlavorManager/build_slot_query/enhance_query.
3. Update utils/search.py: weighted_search_freesound broad + client filter dl>10 dur<4 prefer CC0, simple score, deep param.
4. Update search_slot: simple query + optional flavor, deep.
5. sfxClanker.py: add self.deep_pool_var, self.flavor_var in create_widgets, pass to search_slot.
6. Update process_item if needed (already simple).
7. Test normal/Deep Pool/flavor/headless, pytest/mypy.
8. Git pull/commit/push.