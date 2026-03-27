# Implementation Plan

[Overview]
This plan fixes the SFX Clanker GUI generation flow by cleaning up layout, ensuring tables always show in both normal/manual modes, fixing console output, live preview, scroll, and removing dead code while preserving headless mode.

The current GUI has broken flow: normal mode doesn't show tables reliably, console blank, leftover manual_frame/popup code. Cleanup creates clean layout (left checklist, top toolbar, center tabs, bottom controls), ensures tables populate with top candidate pre-checked in normal mode, multiple in manual, live volume preview, detailed console, scroll wheel. No new features/files/deps.

[Types]
No new types needed; reuse existing Candidate(TypedDict), VolumeSettings(TypedDict), Slot(TypedDict).

[Files]
Modify sfxClanker.py (main layout/flow cleanup) and utils/audio_processor.py (live preview volume).

No new files, no deletions.

[Functions]
Modified functions in sfxClanker.py:
- create_widgets: Final clean layout (left checklist, top toolbar with folder/vol/RMS/checkboxes, center notebook, bottom controls).
- generate_pack: Always collect candidates, build tabbed tables, start generation after confirm (no early return).
- build_candidate_table: Add live preview bind on scale, fix MouseWheel, auto-check top in normal mode.
- create_tabbed_view, create_category_tab: Ensure tables appear, confirm button always added.
- process_item: Ensure detailed console messages.

utils/audio_processor.py:
- preview_audio: Support vol_factor for live preview.

Remove: show_manual_selection, old manual_frame references, duplicate generation paths.

[Classes]
SFXClankerGUI:
- Remove leftover manual_frame, old popup logic.
- Ensure self.notebook center, self.selections, console_queue preserved.

[Dependencies]
No changes.

[Testing]
- Normal mode: Test → Generate → tables with top pre-checked, live vol preview, detailed console, generated.
- Manual mode: tables multiple cands, select/vol live, Confirm → generate.
- Scroll wheel on tables.
- Headless unchanged.

[Implementation Order]
1. Read current create_widgets, generate_pack, build_candidate_table, create_tabbed_view, create_category_tab in sfxClanker.py.
2. Update utils/audio_processor.py preview_audio(path, vol_factor=1.0).
3. In sfxClanker.py: Finalize create_widgets clean layout.
4. Update generate_pack always collect cands, call create_tabbed_view.
5. Update build_candidate_table live preview/MouseWheel/auto-check.
6. Ensure create_tabbed_view/create_category_tab both modes.
7. Remove dead code (manual_frame, popup, duplicates).
8. Restore detailed console in process_item/generation.
9. Test normal/manual + headless.