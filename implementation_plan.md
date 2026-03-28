# Implementation Plan for Color-Coded Console

## Overview
Add color-coded console output to the GUI console in sfxClanker.py to improve readability by replacing harsh white text with categorized colors: green for success, red for skipped, cyan for queries, gray for info.

## Files
- Modify sfxClanker.py (SFXClankerGUI.create_widgets, update_console, poll_console, get_tag)

## Functions
- update_console(msg: str, tag: str = ""): accept optional tag, insert with tag
- get_tag(msg: str) -> str: detect tag from keywords
- poll_console(): handle tuple (msg, tag) or plain msg

## Classes
- SFXClankerGUI: add tag_config in create_widgets, update poll_console and update_console

## Dependencies
No new.

## Testing
- Run python sfxClanker.py
- Generate pack with Combat category
- Confirm colors: green success, red skipped, cyan queries, gray info

## Implementation Order
1. Add tag_config in create_widgets
2. Update update_console and add get_tag
3. Update poll_console for tuples
4. Add explicit tuples in process_item and orchestrate_search
5. Test GUI, confirm colors