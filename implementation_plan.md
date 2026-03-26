# Implementation Plan

[Overview]
Refactor SFX Clanker to V2 with slot-based system replacing categories, slot-centric GUI, metadata-only candidate scoring, lazy audio loading, and removal of ID caching for fresh live discovery.

The current system uses category-based prompts from prompts.json, caches good IDs, pre-downloads previews for RMS scoring during candidate collection, and displays tabbed tables per category. V2 shifts to 24 specific functional slots (e.g., light_attack_hit) each with custom positive/negative tags, a single scrollable UI with slot headers and multi-select candidates underneath, Freesound API filters for duration/loudness to avoid downloads until play/confirm, and ephemeral searches without cache reliance. Hardcoded IDs bypass search. This improves performance, UI usability, and freshness while maintaining one-button flow and modularity. Fits .clinerules by using utils, adding types, running tests/mypy, git workflow. Main GUI shortened by extracting search/display logic.

[Types]  
Introduce Slot and Candidate types for slot-centric data flow.

```
from typing import TypedDict, List, Optional

class Slot(TypedDict):
    name: str  # e.g., "light_attack_hit" for filename base
    display_name: str  # e.g., "Light Attack Hit"
    pos_tags: List[str]  # e.g., ["sword", "hit", "light"]
    neg_tags: List[str]  # e.g., ["synth", "beep"]
    id: Optional[str]  # hardcoded bypass

class Candidate(TypedDict):
    id: str
    name: str
    duration: float
    preview_url: str
    downloads: int
    quality_score: float  # based on duration closeness to 1.2s, downloads
    analysis: Dict[str, Any]  # loudness etc. if avail
```

Validation: pos_tags/neg_tags non-empty lists of 3-8 lowercase words; name lowercase_ no specials; quality_score 0-10.

Relationships: SFXLibrary returns List[Slot]; search returns List[Candidate]; selections Dict[slot_name, List[str id]].

[Files]
Create new files for slot data and UI helpers; modify core utils and main; delete cache files/module.

New files:
- utils/slots.py: hardcoded 24 slots with pos/neg tags derived from current prompts (e.g., light_attack_hit: pos_tags=["light", "sword", "slash", "hit", "melee"], neg_tags=["synth","electronic","beep","buzz","sine"], display="Light Attack Hit")
- utils/gui_helpers.py: functions for building slot candidate rows/headers, handling selections.

Existing files modified:
- utils/sfx_library.py: load slots from utils/slots.py instead of prompts.json; add get_slots() -> List[Slot]; get_slot(name) -> Slot; filename_from_slot(slot: Slot) -> str
- prompts.json: unchanged (per .clinerules)
- utils/search.py: weighted_search_freesound add filter="duration:[0.1 TO 3.0];loudness:ge:-30" (exact Freesound syntax: loudness is ac_loudness_mean or similar; test); return with analysis fields.
- utils/query_builder.py: new build_slot_query(slot: Slot) -> str = " +".join(slot.pos_tags) + " -" + ",".join(slot.neg_tags)
- sfxClanker.py: refactor GUI to single scrollable frame with slot headers + 3-5 cand rows (parallel search on generate); remove cat checkboxes, cache imports/calls; extract candidate table build to gui_helpers; shorten to <250 lines; update process_item calls with selected IDs; add logging to files.
- utils/audio_processor.py: no change (lazy preview already good)
- tests/test_cache.py: delete or stub empty
- tests/: add test_slots.py for slot data; update test_query_builder for slot queries; test_search for filters.

Files deleted: utils/cache.py; cache.json (gitignore already?)

Config: .mypy.ini unchanged; requirements.txt add if needed (none).

[Functions]
Introduce slot query/search/display functions; modify search/process; remove cache funcs.

New functions:
- utils/slots.get_slots() -> List[Slot]: return hardcoded 24 slots
- utils/query_builder.build_slot_query(slot: Slot) -> str: pos + neg
- utils/search.search_slot(slot: Slot, keys: List[str]) -> List[Candidate]: weighted_search_freesound(build_slot_query(slot), keys, filter=slot_filter)
- utils/gui_helpers.build_slot_section(parent: tk.Frame, slot: Slot, cands: List[Candidate], on_select: Callable) -> None: bold header, 3-5 rows chk/play/vol
- sfxClankerGUI.collect_candidates_parallel(slots: List[Slot]) -> Dict[str, List[Candidate]]: threadpool search per slot

Modified functions:
- sfxClanker.py:collect_candidates_for_category -> gone; generate_pack: get all slots, parallel collect, build single scroll frame; process_item: always fresh get_sound_by_id(selected_id), no cache/search fallback
- utils/search.weighted_search_freesound: add filter param default "duration:[0.1 TO 3.0];ac_loudness:ge:-30", fields+=analysis; score candidates by downloads/duration
- utils/sfx_library.__init__: self.slots = get_slots()

Removed functions:
- All cache.py: load_cache/save_cache/populate_cache/clear_cache (delete module)
- sfxClanker.py:build_candidate_table -> refactored to gui_helpers per slot
Migration: replace cache calls with fresh search or selected IDs.

[Classes]
Minor mods to SFXClankerGUI; no new classes.

New classes: none

Modified classes:
- sfxClankerGUI (sfxClanker.py): remove cat_vars/check_vars/select_all; add self.slots; generate_pack: parallel search slots -> build_scrollable_slots_view(cands_by_slot); create_scrollable_slots_view: canvas+scrollframe, for each slot header + build_slot_section; read_selections: Dict[slot_name, List[id]] from chks; pass manual_candidates=[{'id':id, 'manual_vol':vol} for id,vol in selections[slot]]
- SFXLibrary (utils/sfx_library.py): add self.slots:List[Slot]; get_slots()->self.slots; get_slot(name:str)-> matching

Removed classes: none

[Dependencies]
No new packages; pygame/pydub ok for preview/process.

Version pins unchanged. MCP freesound? No need.

[Testing]
Unit test utils changes; integration GUI stubbed; run pytest/mypy before/after.

New tests:
- tests/test_slots.py: validate 24 slots, queries
- tests/test_query_builder.py: add test_build_slot_query
- tests/test_search.py: mock requests, verify filter in params
- tests/test_sfx_library.py: get_slots len==24, tags valid

Modify:
- test_audio_processor.py: unchanged
- test_cache.py: delete

Validation: pytest tests/ -v --cov=utils --cov-report=term-missing (aim 80%); mypy .; manual GUI test generate/preview/generate.

[Implementation Order]
Implement in phases to avoid breakage: data -> search -> utils -> GUI -> tests -> cleanup.

1. Hardcode slots in new utils/slots.py; update sfx_library.py to use slots; test get_slots.
2. Update query_builder.build_slot_query; test.
3. Update search.py weighted_search_freesound with filter, metadata score; test mock API.
4. Remove cache.py imports/uses from sfxClanker.py/process_item (stub fresh search if no manual).
5. Refactor sfxClankerGUI: extract gui_helpers.py; change generate_pack to parallel slot search, single scrollview with slot sections; update selections multi per slot.
6. Update process_item for manual_candidates List[Candidate] or IDs/vols.
7. Add logging to files in process_item/generate.
8. Update tests: new slot/query/search tests; delete test_cache.
9. Run pytest tests/, mypy .; git pull, commit "Refactor V2: slot system phase1", push.
10. Manual test full flow; final git commit/push.