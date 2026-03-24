# Implementation Plan

[Overview]
Fix CI failure by making winsound import conditional and preview_audio platform-agnostic, since winsound is Windows-only and CI runs on Linux.

The codebase uses winsound for audio preview on Windows. To make tests pass on Linux CI, conditionalize the import and make preview_audio a no-op on non-Windows platforms. Add pytest skip for preview test on non-Windows. This maintains Windows functionality while enabling CI.

[Types]
No new types needed.

[Files]
Modified: utils/audio_processor.py (conditional winsound import, platform check in preview_audio).
Modified: tests/test_audio_processor.py (add pytest.mark.skipif for test_preview_audio).
Modified: sfxClanker.py (remove direct winsound import if present, rely on conditional).

No new files.

[Functions]
Modified functions:
- preview_audio (utils/audio_processor.py): Add try/except or platform check; if not Windows or no winsound, print "Preview not available" and return.
- test_preview_audio (tests/test_audio_processor.py): Add @pytest.mark.skipif(sys.platform != 'win32', reason="winsound Windows only").

No new or removed functions.

[Classes]
No class changes.

[Dependencies]
No changes.

[Testing]
Add skip marker to test_preview_audio for Linux CI.

Update test_process_audio if needed, but already mocked.

Run pytest locally to verify.

[Implementation Order]
1. Update utils/audio_processor.py for conditional winsound.
2. Update tests/test_audio_processor.py with skip marker.
3. Update sfxClanker.py if needed.
4. Run pytest tests/ -v to verify.
5. git add ., commit "Fix: make winsound conditional for Linux CI", push origin main.