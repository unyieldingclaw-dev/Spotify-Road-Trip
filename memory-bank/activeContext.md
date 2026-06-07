---
authority: volatile
review-cycle: 7d
retention: archive-after-6m
staleness-threshold: 14d
tags:
  - session/focus
  - session/blockers
  - session/next-steps
last-reviewed: 2026-06-06
compaction_generation: 1
source_type: canonical
confidence: high
lineage: []
---

# Active Context - Current State

**Last Updated**: 2026-06-06

## Current Focus

Documentation update: populating the 5 memory-bank template files from actual source code, and fixing 12 inaccuracies across 4 spec/plan docs files. The app itself is feature-complete.

## What's Working

- `spotify_client.py`: 9 functions — all API wrappers + pure helpers, fully unit-tested
- `app.py`: customtkinter GUI with auth flow, playlist picker, sliders, progress log, close-while-generating guard
- `main.py`: CLI script (untouched by GUI work)
- `run.bat`: double-click launcher (`pythonw app.py`, no terminal)
- `tests/test_helpers.py`: 8 unit tests — all passing
- `tests/test_app.py`: 2 unit tests for `generate_playlist()` — all passing
- Auth worker correctly uses `auth_error` type (keeps Generate disabled when `sp` is None)
- Close guard: `_on_close` method, `_generating` flag, `WM_DELETE_WINDOW` protocol bound

## Immediate Next Steps

1. ~~Populate memory bank~~ — done in this session
2. ~~Fix spec inaccuracies~~ — done in this session
3. **Commit and push** — `"docs: populate memory bank and fix 12 spec inaccuracies"`

## Known Issues

None.

## Git Status

**Branch**: master

**Recent commits:**
- `7cae63a` fix: separate auth_error type, add close-while-generating guard
- `abe4c3e` fix: pre-push hook falsely blocking on CRLF advisory warnings
- `ea4d062` feat: customtkinter GUI app with auth, playlist picker, sliders, and progress log
- `75b593d` feat: generate_playlist function with tests

## Key Commands

```bash
pytest tests/ -v          # run all 10 tests
python app.py             # run GUI (terminal visible)
run.bat                   # run GUI (no terminal)
python main.py            # run CLI
```

## Key Files

- [`spotify_client.py`](../spotify_client.py): API wrappers (`get_track_uris`, `get_unique_artist_ids`, `expand_by_artists`, `get_recommendations`, etc.)
- [`app.py`](../app.py): `generate_playlist()` function + `App(CTk)` class
- [`tests/test_helpers.py`](../tests/test_helpers.py): 8 unit tests for spotify_client functions
- [`tests/test_app.py`](../tests/test_app.py): 2 unit tests for generate_playlist()

## Recent Decisions

- `auth_error` is a separate message type from `error`: auth failure must not re-enable Generate (sp is None)
- `_generating` flag + `WM_DELETE_WINDOW` guard: warns user before closing mid-generation to avoid partial playlists
- `get_recommendations` has an `if not seed_uris: return []` guard (calling the Spotify endpoint with 0 seeds raises an API error)
- `get_unique_artist_ids` uses `.get("artists", [])` to handle local/deleted tracks that lack an artists key
