# Implementation Plan

[Overview]
Fix GitHub CI failures by addressing OS-specific imports (winsound), completing dependencies, cross-platform paths, and updating workflow actions.

The CI fails on Linux due to winsound (Windows-only). Additional issues: incomplete requirements.txt, hardcoded Windows paths, deprecated actions. This plan makes the code cross-platform, completes deps, fixes paths, updates workflow for reliable CI.

[Types]
No new types needed.

[Files]
Modified: utils/audio_processor.py (conditional winsound).
Modified: tests/test_audio_processor.py (skipif for preview test).
Modified: requirements.txt (add all deps: requests, pydub? but no pydub, wait, code uses pydub? No, ffmpeg).
Wait, code uses no pydub, only ffmpeg subprocess.
Add pydub if needed? No.
Modified: .github/workflows/ci.yml (update actions/checkout@v4, setup-python@v5).
Modified: utils/audio_processor.py (fix hardcoded ffmpeg path to os.path.join).
Modified: sfxClanker.py (check for hardcoded paths).

No new files.

[Functions]
Modified functions:
- preview_audio (utils/audio_processor.py): Conditional winsound, no-op on Linux.
- get_ffmpeg_path (utils/audio_processor.py): Fix hardcoded Windows path to os.path.join(os.path.dirname(__file__), 'ffmpeg', 'bin', 'ffmpeg.exe') or use shutil.which only.
- test_preview_audio (tests/test_audio_processor.py): Add @pytest.mark.skipif(sys.platform != 'win32', reason="Windows only").

No new.

[Classes]
No changes.

[Dependencies]
Add to requirements.txt:
types-requests==2.32.*
pytest-mock==3.*
(Already has requests, pytest, mypy).

No new runtime deps.

[Testing]
Local pytest tests/ -v passes on Windows.
CI will pass on Linux with skip.

[Implementation Order]
1. Update utils/audio_processor.py (conditional winsound, fix hardcoded path).
2. Update tests/test_audio_processor.py (skipif).
3. Update requirements.txt if needed.
4. Update .github/workflows/ci.yml (actions versions).
5. pytest tests/ -v
6. git add ., commit -m "Fix CI: winsound conditional, paths, workflow", git push origin main.