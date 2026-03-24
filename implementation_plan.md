# Implementation Plan

[Overview]
Create a highly optimized Cline workspace for SFXClanker by refactoring code for modularity and testability, aligning implementation with design rules (e.g., switch to pydub/simpleaudio, exact query append), enhancing .clinerules for precise guidance, and adding comprehensive testing and automation setups.

The current codebase is functional but monolithic (~350 lines in main.py), with duplicated query logic, hardcoded tokens in helpers, deps mismatch (ffmpeg vs pydub), and basic error handling. Optimization will split into utils modules, add type hints/pytest, update rules to reflect/enforce best practices, remove security risks, and introduce Cline-specific rules for common tasks like adding SFX or refactoring. This makes the project easier for Cline to maintain/extend while preserving the one-button simplicity.

High-level approach: Extract utilities first, refactor main app to import them, align audio/query to specs, add tests/verification, enhance rules/docs. No feature bloat – keep under 500 total lines.

[Types]  
Introduce type hints and TypedDict/dataclasses for better maintainability and IDE/Cline support.

- from typing import TypedDict
- class Prompt(TypedDict):
    category: str
    name: str
    fallbacks: list[str]
    id: str | None
- class SFXItem(TypedDict):
    category: str
    name: str
    fallbacks: list[str]
    id: str | None
    filename: str
    path: str
    status: str  # 'pending' | 'success' | 'skipped'
- Add mypy type checking in tests/CI.

No new enums/interfaces needed; use str literals for categories ('Combat', 'Movement', 'UI').

[Files]
Create new modular files, refactor main, delete obsolete helpers, update configs/docs.

New files:
- requirements.txt: List deps (requests==2.32.*, pydub==0.25.*, simpleaudio==0.1.*, pytest==8.*, mypy==1.*)
- utils/query_builder.py: Centralized query functions.
- utils/audio_processor.py: pydub-based process/normalize/preview.
- utils/sfx_library.py: Extracted SFXLibrary class.
- tests/test_query_builder.py: Unit tests for queries.
- tests/test_audio_processor.py: Mock audio tests.
- tests/test_sfxclanker.py: Integration tests.
- .gitignore: Ignore __pycache__, .venv, SFX PACKS/, *.txt keys/logs.
- .clinerules/refactor.mdc: Rules for code changes.
- .clinerules/testing.mdc: Rules for running tests/verification.
- .mypy.ini: Basic mypy config.

Modified files:
- sfxClanker.py: Refactor to import utils, use pydub/simpleaudio, exact query append, type hints, under 250 lines.
- .clinerules/sfxClanker.mdc: Update deps to pydub/simpleaudio, add modularity/testing rules, exact query string.
- README.md: Add sections for testing, development workflow, requirements install.
- prompts.json: No change (immutable per rules).

Deleted files:
- query_prompts.py: Obsolete debug script with hardcoded token.
- cache_builder.py: Obsolete with hardcoded token; integrate cache logic optionally later.

No config updates needed beyond requirements.txt.

[Functions]
Centralize duplicated logic into utils, add type hints, improve error handling.

New functions:
- utils/query_builder.py: build_search_query(raw: str) -> str, enhance_query(base: str) -> str  (exact append: "dark fantasy souls-like low reverb gritty armor medieval dark souls style")
- utils/audio_processor.py: process_audio(input_path: str, output_path: str, normalize: bool, trim: bool) -> bool | str, preview_audio(path: str, volume: float = 0.5) -> None  (pydub + simpleaudio)
- utils/sfx_library.py: load_prompts() -> dict[str, dict[str, Prompt]], get_prompt(cat: str, name: str) -> Prompt | None, etc.
- tests/: test_build_search_query(), test_enhance_query(), test_process_audio(mock), etc.

Modified functions:
- sfxClanker.py: generate_pack() -> use utils, concurrent.futures unchanged; process_item() -> delegate to utils; remove duplicated query/audio code.
- Remove weighted_search_freesound, download_sfx, etc. -> move to utils/api.py if expanded.

No functions removed; obsolete helpers deleted entirely.

[Classes]
Extract inline class to module, minor GUI tweaks.

New classes:
- utils/sfx_library.py: SFXLibrary (unchanged, but typed, load from json).

Modified classes:
- sfxClanker.py: SFXClankerGUI – import SFXLibrary from utils, use utils funcs, add type hints to methods (e.g., def generate_pack(self) -> None).

No classes removed.

[Dependencies]
Switch to design-spec deps, add dev tools.

New packages:
- pydub==0.25.* (audio normalize/convert, replaces ffmpeg subprocess)
- simpleaudio==0.1.* (cross-platform preview at 50% vol, replaces ffplay/winsound)
- pytest==8.* (testing)
- mypy==1.* (type checking)

requests==2.32.* unchanged (pip only).

No version changes; pin for reproducibility.
Remove ffmpeg bundle dep (no pip/subprocess).
Update requirements.txt install: pip install -r requirements.txt

Integration: pydub needs ffmpeg backend? No, for mp3 pydub uses ffmpeg if avail, but bundle optional or doc install.

[Testing]
Add pytest suite for 80%+ coverage on utils, mock external (requests, audio).

New test files:
- tests/test_query_builder.py: Test query strings exact match spec.
- tests/test_audio_processor.py: Mock pydub/simpleaudio, test normalize -3dB peak (use pydub.effects.normalize + peak check), trim silence.
- tests/test_sfxclanker.py: Mock API responses, end-to-end headless mode.

Validation: pytest -v, mypy ., coverage via pytest-cov.
Run tests post-changes to verify no regressions.
CI: Add .github/workflows/test.yml (pytest on push).

[Implementation Order]
Execute changes in dependency order to avoid breakage.

1. Create requirements.txt and pip install new deps (pydub simpleaudio pytest mypy).
2. Create utils/ modules: query_builder.py, audio_processor.py, sfx_library.py with extracted/refactored code.
3. Refactor sfxClanker.py: Replace inline SFXLibrary, duplicated funcs with utils imports; switch audio to pydub/simpleaudio; update query append exact.
4. Create tests/ suite and verify pytest passes.
5. Update .clinerules/sfxClanker.mdc (deps, utils usage rules), add .clinerules/refactor.mdc and testing.mdc.
6. Update README.md (dev section, pip install, pytest run).
7. Add .gitignore, .mypy.ini.
8. Delete obsolete query_prompts.py, cache_builder.py.
9. Run full e2e test: generate pack, verify audio/WAVs/logs.