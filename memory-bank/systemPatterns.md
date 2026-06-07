---
authority: stable
review-cycle: 90d
retention: permanent
staleness-threshold: 180d
tags:
  - architecture/decisions
  - patterns/code
  - anti-patterns
last-reviewed: 2026-06-06
compaction_generation: 1
source_type: canonical
confidence: high
lineage: []
---

# System Patterns & Architecture Decisions

**Last Updated**: 2026-06-06

## Architecture Patterns

### Module Separation

**Decision**: All Spotify API calls and pure helper functions live in `spotify_client.py`. GUI and generation orchestration live in `app.py`. CLI orchestration lives in `main.py`.

**Rationale**:
- `spotify_client.py` functions are testable without importing tkinter
- `generate_playlist()` in `app.py` is a standalone function — tested without a real Spotify client or GUI
- `main.py` is untouched by GUI work

**Implementation**:
```
spotify_client.py  ← API wrappers + pure helpers (fully unit-tested)
app.py             ← generate_playlist() + App(CTk) GUI class
main.py            ← CLI entry point (imports spotify_client directly)
```

### Threading Model

**Decision**: All Spotify API calls run in background `threading.Thread`; a `queue.Queue` carries messages to the main thread via `root.after(100, _poll_queue)`.

**Rationale**:
- tkinter freezes if blocking I/O runs on the main thread
- `queue.Queue` is the only safe cross-thread communication mechanism in tkinter

**Implementation**:
```
Worker thread  →  queue.put({"type": "progress", "pct": 0.60, "msg": "✓ Copied tracks"})
Main thread    →  polls queue every 100ms via after()
               →  updates progress bar + appends to status log
```

### Message Types

| type | Sender | Meaning |
|------|--------|---------|
| `status` | auth worker | Status label update (pre-auth) |
| `auth_done` | auth worker | Auth succeeded; populate dropdown, enable controls |
| `auth_error` | auth worker | Auth failed; keep Generate disabled (sp is None) |
| `progress` | generate worker | Progress bar + log line update |
| `done` | generate worker | Generation complete; re-enable Generate |
| `error` | generate worker | Generation failed; re-enable Generate |

`auth_error` must remain separate from `error`: auth failure leaves `self._sp = None` so Generate must stay disabled.

## Code Patterns

### Deduplication

Always use a `set` of track URIs. Thread it through every expansion step:

```python
existing_uris = get_track_uris(original_tracks)          # set
all_uris = existing_uris | {t["uri"] for t in artist_additions}
# pass all_uris as existing_uris to get_recommendations
```

### Batch API Writes

Spotify limits `playlist_add_items` to 100 URIs per call. Always use `add_tracks_in_batches`:

```python
for i in range(0, len(uris), 100):
    sp.playlist_add_items(playlist_id, uris[i:i + 100])
```

### Defensive Access on Track Items

Playlist item dicts may have `"track": None` (local files, deleted tracks). Always guard:

```python
if not item.get("track"):
    continue
for artist in item["track"].get("artists", []):
    ...
```

### Empty-Seed Guard in get_recommendations

Calling `/recommendations` with zero seeds raises a Spotify API error. Guard before calling:

```python
if not seed_uris:
    return []
seeds = seed_uris[:5]
```

### Close-While-Generating Guard

`App` tracks `self._generating: bool`. `WM_DELETE_WINDOW` is bound to `_on_close`, which shows a `tkinter.messagebox.askyesno` dialog if `_generating` is `True`.

## Data Flow Patterns

### Playlist Generation Flow

1. `_start_auth` → spawns `_auth_worker` thread
2. `_auth_worker` → `auth_done` message → `_handle_message` populates dropdown, enables controls
3. User clicks Generate → `_on_generate` → sets `_generating = True`, spawns `_generate_worker`
4. `_generate_worker` calls `generate_playlist()` → emits `progress` messages at each step
5. On success → `done` message → `_handle_message` sets `_generating = False`, re-enables button
6. On exception → `error` message → `_handle_message` sets `_generating = False`, re-enables button

## Testing Patterns

### Mock Everything External

All Spotify API calls are mocked. Never call real endpoints in tests.

```python
mock_sp = MagicMock()
mock_sp.artist_top_tracks.return_value = {"tracks": [...]}
```

### Test the Pure Function, Not the GUI

`generate_playlist()` accepts `on_progress` as a callback — test it directly with `patch` on all Spotify calls and a simple lambda for `on_progress`.

### Minimal Track Item Fixture

```python
def _make_track_item(uri, artist_ids):
    return {"track": {"uri": uri, "artists": [{"id": aid} for aid in artist_ids]}}
```

## Git & Version Control

### Commit Message Format

```
<type>: <short description>

Types: feat, fix, chore, docs, refactor, test, style
```

### Branch Strategy

- `master` — only branch; all work committed directly (solo project)

## Never Do This

- ❌ Call real Spotify API in tests
- ❌ Run blocking I/O on the tkinter main thread
- ❌ Call `sp.recommendations()` with zero seeds (raises API error — guard first)
- ❌ Access `item["track"]["artists"]` without `.get("artists", [])` (may KeyError on local files)
- ❌ Commit `.env` or `.spotify_cache`
- ❌ Force push to master
- ❌ Put `{"type": "auth_error"}` through the `error` handler (keeps Generate disabled intentionally)
