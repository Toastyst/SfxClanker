# Implementation Plan

## [Overview]
Organize the SFXClanker project logically by improving modularity, fixing type inconsistencies, and aligning with .clinerules for refactor goals: modularity, testability, type safety. This addresses documentation overlap, unclear Slot TypedDict, and ensures consistent structure.

The project is already well-structured with utils/, tests/, but has type errors in Slot TypedDict (missing fallbacks, extra pos_tags/neg_tags), mypy issues, and some duplication. README and sfxClanker.design.md overlap on features; consolidate into README. prompts.json is raw data; load from SFXLibrary class.

This plan fixes types, organizes prompts into code, cleans docs, ensures 100% test pass/mypy clean.

## [Types]
Update Slot TypedDict in utils/slots.py to include all fields used:

class Slot(TypedDict):
    name: str
    display_name: str
    category: str
    fallbacks: List[str]
    id: Optional[str]
    pos_tags: List[str]
    neg_tags: List[str]

Add TypedDict for Candidate in utils/search.py.

## [Files]
- **utils/slots.py**: Update Slot TypedDict to include fallbacks, pos_tags, neg_tags. Remove hardcoded slots; load from SFXLibrary.
- **utils/sfx_library.py**: Load prompts.json into SFXLibrary.get_slots() -> List[Slot]
- **README.md**: Consolidate design info from sfxClanker.design.md, remove duplication.
- **sfxClanker.design.md**: Archive or delete after consolidation.
- **.clinerules/**: Keep as is.
- **prompts.json**: Keep as source data.

No new files.

## [Functions]
- **utils/slots.py**: get_slots() -> List[Slot] (load from SFXLibrary)
- **utils/sfx_library.py**: New get_slots() -> List[Slot] (parse prompts.json)
- **utils/query_builder.py**: No change.
- **utils/search.py**: No change.

## [Classes]
- **SFXLibrary**: Add get_slots() method to return typed slots from prompts.json.

## [Dependencies]
No changes.

## [Testing]
- Update tests/test_slots.py to use new Slot with all fields.
- Ensure pytest passes 100%.
- mypy . passes 100%.

## [Implementation Order]
1. Update Slot TypedDict in utils/slots.py
2. Add get_slots() in utils/sfx_library.py
3. Update tests/test_slots.py
4. Run pytest tests/ -v and mypy .
5. Consolidate README.md
6. Commit "Refactor: improve types and modularity"