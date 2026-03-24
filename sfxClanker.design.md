# sfxClanker Design Document
**Version:** 1.1 (March 2026)
**Status:** Modular one-button FreeSound batch downloader for HelloKnight with testing and automation
**Goal:** Single “Generate Sound Pack” button that downloads all 24 SFX with perfect dark-fantasy Souls-like consistency, names them correctly, normalizes them, and drops them in a folder. Includes headless mode, randomization, and comprehensive testing.
**Repository:** https://github.com/Toastyst/SfxClanker

## 1. Project Overview
- Modular Python GUI (tkinter) using utils/ modules for maintainability.
- One-click: downloads, renames, normalizes, and saves the entire 24-SFX pack.
- Maintains **uniform flavor** across the whole batch (dark fantasy, low reverb, gritty, Souls-like).
- Works for anyone with a FreeSound API key (shareable).
- Includes headless CLI mode for automation.
- Comprehensive testing with pytest and type checking with mypy.

## 2. Core Features (MUST-HAVE)
- Left side: Categorized checklist (Combat / Movement / UI) with “Select All” toggle.
- Bottom bar:
  - “Choose Output Folder” button
  - Checkbox: “Normalize to -3 dB peak (recommended)”
  - Checkbox: “Auto-trim silence”
  - Checkbox: “Randomize sounds each batch (for funny packs)”
  - Big green **“GENERATE SOUND PACK”** button
- Right side / After generation: Preview list with “Play [filename]” buttons for every sound.
- Headless mode: `python sfxClanker.py --headless --output DIR [--normalize] [--random] [--trim] --categories Combat,Movement,UI`
- API key: Asked once, saved to `freesound_key.txt` next to the script.
- Search logic (chosen for 80% success rate):
  - Takes original prompt from prompts.json
  - Builds query: build_search_query(name) + fallbacks
  - Enhances: enhance_query(query) appends "dark fantasy souls-like low reverb gritty armor medieval dark souls style"
  - Filters: CC0 license prefer, fallback to all; min 44.1 kHz implied
  - Sorts by: most downloaded + highest rating
  - Uses cache.json for pre-validated IDs if available
  - Auto-retries with fallbacks, then skips + logs.
- Post-processing:
  - Always convert to 44.1 kHz mono WAV
  - Normalize to -3 dB peak (ffmpeg loudnorm) when checkbox enabled
  - Trim silence (ffmpeg silenceremove) when checkbox enabled
- Filenames: `category_lowercase_with_underscores_name.wav` (exact match to helloknight_sfx_library.mdc)
- Preview: Plays with winsound (Windows)

## 3. Dependencies
- tkinter (built-in)
- requests (API calls)
- pytest (testing)
- mypy (type checking)
- ffmpeg (audio processing, bundled or installed)

## 4. Error Handling & UX
- Clear progress bar + status text during batch.
- Console output for headless.
- At end: summary dialog/stdout + list of any missing sounds.
- generation_log.txt and failed_queries.txt created in output folder.
- Threaded downloads/processing for responsiveness.

## 5. Architecture
- utils/query_builder.py: Query building and enhancement.
- utils/audio_processor.py: Audio processing with ffmpeg.
- utils/sfx_library.py: SFXLibrary class for prompts.
- sfxClanker.py: Main GUI and headless logic.
- tests/: Unit tests for utils.
- .clinerules/: Rules for Cline guidance.

## 6. Non-Goals
- No manual search UI
- No 8-bit/N64 tags (keeps consistent dark fantasy flavor)
- No complex custom tags per sound (global suffix only)

Success = User clicks one button → perfect ready-to-use HelloKnight sound pack in <2 minutes.
