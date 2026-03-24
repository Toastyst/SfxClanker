# SFX Clanker

## Overview

SFX Clanker is a simple Python GUI application that generates a complete 24-SFX sound pack for HelloKnight by automatically downloading and processing audio from FreeSound. It ensures uniform dark fantasy Souls-like flavor across all sounds, with one-click generation, category selection, and post-generation preview.

Built per sfxClanker.design.md and .clinerules, under 400 lines, dark retro theme, no extra complexity.

## Features

- **GUI Layout**: Left checklist for categories (Combat/Movement/UI), bottom controls (folder select, normalize checkbox, big green GENERATE button), right preview list post-gen.
- **Headless Mode**: CLI for automation: `python sfxClanker.py --headless --output DIR [--normalize] --categories Combat,Movement,UI`.
- **API Integration**: FreeSound v2 API with token auth, search appends "dark fantasy souls-like gritty armor medieval dark souls style", prefers CC0 license (logs NON-CC0 alerts for fallback results), returns first result (no strict filters), downloads HQ/LQ MP3 previews.
- **Fallbacks and IDs**: Each SFX has 5+ fallback queries; optional hardcoded IDs for pre-validated sounds tried first.
- **Audio Processing**: Converts to 44.1kHz mono WAV with ffmpeg, optional loudnorm normalization.
- **Filenames**: Exact convention from clinerules: category_lowercase_underscores.wav (e.g., combat_light_attack_hit.wav).
- **Preview**: Plays with winsound (Windows).
- **Error Handling**: Retries 3x, skips failures, logs to generation_log.txt (with NON-CC0 alerts) and failed_queries.txt for debugging.
- **Persistence**: API key saved in freesound_key.txt.

## Requirements

- Python 3.x (tested on 3.13)
- tkinter (built-in on Windows)
- requests, pytest, mypy libraries
- ffmpeg (bundled in repo, or install separately)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Toastyst/SfxClanker.git
   cd SfxClanker
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Obtain FreeSound API key:
   - Visit https://freesound.org/apiv2/apply/
   - Apply for a personal API key (free, instant approval for non-commercial use).

## Usage Instructions

### First-Time Setup

1. Download or clone the project.
2. Run the application:
   ```
   python sfxClanker.py
   ```
3. On first run, enter your FreeSound API key in the prompt. It will be saved to `freesound_key.txt` for future use.

### Generating a Sound Pack

1. **Launch GUI**: Run `python sfxClanker.py`. The window opens with dark theme.
2. **Select Categories**: Use the left checklist to choose Combat, Movement, UI (default all selected). Click "Select All" to toggle.
3. **Choose Output Folder**: Click "Choose Output Folder" button, select a directory for the generated WAV files.
4. **Options**: Check "Normalize to -3 dB" for consistent volume (recommended).
5. **Generate**: Click the big green "GENERATE SOUND PACK" button. The tool tries hardcoded IDs first if available, then searches with name + fallbacks + appended tags, filtering results.
6. **Monitor Progress**: Watch the progress bar and status text. Generation is threaded, GUI remains responsive.
7. **Completion**: Dialog shows success count. Preview buttons appear on the right for each generated SFX.
8. **Playback**: Click any "Play [filename]" button to preview at 50% volume.
9. **Output**: Check the selected folder for WAV files, plus `generation_log.txt` with details on generated/skipped files, and `failed_queries.txt` with failed query lists for debugging.

### Example Output

- combat_light_attack_hit.wav
- movement_wall_crumble_secret_reveal.wav
- ui_menu_select_click.wav
- ...
- generation_log.txt (e.g., "Generated combat_light_attack_hit.wav", "Skipped ui_low_stamina_warning.wav: no results")
- failed_queries.txt (e.g., "Failed queries: ui_low_stamina_warning.wav, low stamina, exhaust, ...")

### Troubleshooting

- **No API Key**: Enter it when prompted; ensure valid FreeSound key.
- **Network Issues**: Retries automatically; check log for skips.
- **Low Success Rate**: Check failed_queries.txt for failed query lists; may need to add hardcoded IDs or adjust fallbacks.
- **Audio Errors**: Ensure ffmpeg installed and in PATH; check command prompt with `ffmpeg -version`.
- **Preview Issues**: winsound is Windows-only; ensure speakers enabled.

## Development

### Git Workflow
- **Repo**: https://github.com/Toastyst/SfxClanker
- **Branch**: main (default)
- **Before changes**: `git status`, `git pull origin main`
- **After changes**: `git add .`, `git commit -m "Action: description"`, `git push origin main`
- **Testing before commit**: `pytest tests/ -v`, `mypy .`
- **Feature branches**: `git checkout -b feature/name` for new features

### Testing
Run tests with:
```
pytest tests/ -v
```
Check types with:
```
mypy .
```

### Architecture

- **SFXLibrary**: Class in utils/sfx_library.py with 24 prompts (9 Combat, 9 Movement, 6 UI).
- **Threading**: concurrent.futures for parallel downloads/processing.
- **Audio**: ffmpeg for processing/normalization, winsound for preview.

## Limitations

- Requires ffmpeg installation.
- Requires internet for downloads.
- No batch/custom tags beyond the fixed append.

## License

CC0 (matching FreeSound sources).