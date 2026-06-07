# Spotify Road-Trip Playlist Generator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python CLI script that copies "Road-trip Sing Alongs" into a new Spotify playlist and expands it with songs from the same artists plus Spotify AI recommendations.

**Architecture:** Two Python files — `spotify_client.py` wraps all Spotify API calls and houses pure helper functions; `main.py` orchestrates the full flow. Auth uses spotipy's Authorization Code flow, caching the token in `.spotify_cache`. User is prompted for the new playlist name at runtime.

**Tech Stack:** Python 3.10+, spotipy>=2.23.0, python-dotenv>=1.0.0, pytest

---

## File Map

| File | Purpose |
|------|---------|
| `spotify_client.py` | All Spotify API wrappers + pure helper functions |
| `main.py` | CLI orchestration — calls functions, prints summary |
| `tests/test_helpers.py` | Unit tests for pure functions |
| `.env` | `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, `SPOTIFY_REDIRECT_URI` (gitignored) |
| `.env.example` | Credential template |
| `requirements.txt` | `spotipy>=2.23.0`, `python-dotenv>=1.0.0`, `pytest` |
| `.gitignore` | Excludes `.env`, `.spotify_cache`, `__pycache__/`, `*.pyc` |

---

## Task 1: GitHub Repo + Project Skeleton

**Files:**
- Create: `.gitignore`
- Create: `.env.example`
- Create: `requirements.txt`

- [ ] **Step 1: Create the GitHub repo**

```bash
gh repo create UnyieldingClaw/Spotify-Road-Trip --public --description "Generate expanded road trip playlists from an existing Spotify playlist" --clone
cd Spotify-Road-Trip
```

> If the repo already exists locally (you're working from `C:\Users\Mizzo\Claude\Spotify-Road-Trip`), skip `--clone` and just add the remote:
> ```bash
> gh repo create UnyieldingClaw/Spotify-Road-Trip --public --source=. --remote=origin --push
> ```

- [ ] **Step 2: Write `.gitignore`**

```
.env
.spotify_cache
__pycache__/
*.pyc
.pytest_cache/
```

- [ ] **Step 3: Write `.env.example`**

```
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
SPOTIFY_REDIRECT_URI=http://localhost:8080/callback
```

- [ ] **Step 4: Write `requirements.txt`**

```
spotipy>=2.23.0
python-dotenv>=1.0.0
pytest
```

- [ ] **Step 5: Install dependencies**

```bash
pip install -r requirements.txt
```

Expected: installs without errors.

- [ ] **Step 6: Commit**

```bash
git add .gitignore .env.example requirements.txt
git commit -m "chore: project skeleton with gitignore and requirements"
git push -u origin master
```

---

## Task 2: Pure Helper Functions + Tests

**Files:**
- Create: `spotify_client.py` (helpers only for now)
- Create: `tests/__init__.py`
- Create: `tests/test_helpers.py`

These functions take plain Python data (no Spotify API calls) so they're fully unit-testable.

- [ ] **Step 1: Write the failing tests**

Create `tests/__init__.py` (empty file), then create `tests/test_helpers.py`:

```python
from spotify_client import get_track_uris, get_unique_artist_ids

def _make_track_item(uri, artist_ids):
    """Build a minimal playlist track item dict."""
    return {
        "track": {
            "uri": uri,
            "artists": [{"id": aid} for aid in artist_ids]
        }
    }

def test_get_track_uris_returns_all_uris():
    items = [
        _make_track_item("spotify:track:aaa", ["artist1"]),
        _make_track_item("spotify:track:bbb", ["artist2"]),
    ]
    result = get_track_uris(items)
    assert result == {"spotify:track:aaa", "spotify:track:bbb"}

def test_get_track_uris_skips_none_tracks():
    items = [{"track": None}, _make_track_item("spotify:track:aaa", ["artist1"])]
    result = get_track_uris(items)
    assert result == {"spotify:track:aaa"}

def test_get_unique_artist_ids_deduplicates():
    items = [
        _make_track_item("spotify:track:aaa", ["artist1", "artist2"]),
        _make_track_item("spotify:track:bbb", ["artist1"]),  # artist1 seen again
    ]
    result = get_unique_artist_ids(items)
    assert result == ["artist1", "artist2"]

def test_get_unique_artist_ids_skips_none_tracks():
    items = [{"track": None}, _make_track_item("spotify:track:aaa", ["artist1"])]
    result = get_unique_artist_ids(items)
    assert result == ["artist1"]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_helpers.py -v
```

Expected: `ImportError` or `ModuleNotFoundError` — `spotify_client` doesn't exist yet.

- [ ] **Step 3: Write the helper functions in `spotify_client.py`**

```python
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

SCOPES = "playlist-read-private playlist-modify-public playlist-modify-private"


def get_spotify_client():
    load_dotenv()
    return spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=os.environ["SPOTIFY_CLIENT_ID"],
        client_secret=os.environ["SPOTIFY_CLIENT_SECRET"],
        redirect_uri=os.environ["SPOTIFY_REDIRECT_URI"],
        scope=SCOPES,
        cache_path=".spotify_cache",
    ))


def get_track_uris(track_items):
    """Return set of track URIs from playlist item dicts."""
    return {
        item["track"]["uri"]
        for item in track_items
        if item.get("track")
    }


def get_unique_artist_ids(track_items):
    """Return list of unique artist IDs, preserving first-seen order."""
    seen = set()
    artist_ids = []
    for item in track_items:
        if not item.get("track"):
            continue
        for artist in item["track"].get("artists", []):
            if artist["id"] not in seen:
                seen.add(artist["id"])
                artist_ids.append(artist["id"])
    return artist_ids
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_helpers.py -v
```

Expected: 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add spotify_client.py tests/
git commit -m "feat: pure helper functions with tests"
```

---

## Task 3: Spotify API — Read Playlist and Tracks

**Files:**
- Modify: `spotify_client.py` (add 3 functions)

These functions call the Spotify API; verify them manually in Task 8.

- [ ] **Step 1: Add playlist and track fetching functions to `spotify_client.py`**

Append these functions after the existing ones:

```python
def get_playlist_by_name(sp, name):
    """Search user's playlists by exact name. Returns playlist dict or None."""
    results = sp.current_user_playlists()
    while results:
        for playlist in results["items"]:
            if playlist["name"] == name:
                return playlist
        results = sp.next(results) if results["next"] else None
    return None


def get_all_tracks(sp, playlist_id):
    """Fetch all tracks from a playlist, handling pagination. Returns list of playlist item dicts."""
    tracks = []
    results = sp.playlist_items(playlist_id)
    while results:
        tracks.extend(results["items"])
        results = sp.next(results) if results["next"] else None
    return [item for item in tracks if item.get("track")]


def list_all_playlists(sp):
    """Return list of (name, id) tuples for all user playlists."""
    playlists = []
    results = sp.current_user_playlists()
    while results:
        for p in results["items"]:
            playlists.append((p["name"], p["id"]))
        results = sp.next(results) if results["next"] else None
    return playlists
```

- [ ] **Step 2: Verify existing tests still pass**

```bash
pytest tests/test_helpers.py -v
```

Expected: 4 tests PASS (new functions have no unit tests — verified end-to-end in Task 8).

- [ ] **Step 3: Commit**

```bash
git add spotify_client.py
git commit -m "feat: playlist and track fetching functions"
```

---

## Task 4: Artist Expansion Function + Test

**Files:**
- Modify: `spotify_client.py` (add `expand_by_artists`)
- Modify: `tests/test_helpers.py` (add test)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_helpers.py`:

```python
from unittest.mock import MagicMock
from spotify_client import expand_by_artists

def test_expand_by_artists_limits_per_artist_and_deduplicates():
    # Artist "a1" has 5 top tracks; we should only take 2 (per_artist=2)
    # Track "uri-orig" is already in existing_uris — must be skipped
    mock_sp = MagicMock()
    mock_sp.artist_top_tracks.return_value = {
        "tracks": [
            {"uri": "uri-orig",  "artists": [{"id": "a1"}]},  # already exists, skip
            {"uri": "uri-new-1", "artists": [{"id": "a1"}]},
            {"uri": "uri-new-2", "artists": [{"id": "a1"}]},
            {"uri": "uri-new-3", "artists": [{"id": "a1"}]},  # over limit, skip
        ]
    }

    original_items = [_make_track_item("uri-orig", ["a1"])]
    existing_uris = get_track_uris(original_items)

    result = expand_by_artists(mock_sp, original_items, existing_uris, per_artist=2)

    assert [t["uri"] for t in result] == ["uri-new-1", "uri-new-2"]
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_helpers.py::test_expand_by_artists_limits_per_artist_and_deduplicates -v
```

Expected: FAIL with `ImportError` — `expand_by_artists` not defined yet.

- [ ] **Step 3: Add `expand_by_artists` to `spotify_client.py`**

```python
def expand_by_artists(sp, original_track_items, existing_uris, per_artist=3, country="US"):
    """
    For each unique artist in the original tracks, fetch their top tracks and
    return up to `per_artist` tracks not already in `existing_uris`.
    """
    artist_ids = get_unique_artist_ids(original_track_items)
    additions = []
    seen_uris = set(existing_uris)

    for artist_id in artist_ids:
        result = sp.artist_top_tracks(artist_id, country=country)
        count = 0
        for track in result["tracks"]:
            if track["uri"] not in seen_uris and count < per_artist:
                additions.append(track)
                seen_uris.add(track["uri"])
                count += 1

    return additions
```

- [ ] **Step 4: Run all tests**

```bash
pytest tests/ -v
```

Expected: 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add spotify_client.py tests/test_helpers.py
git commit -m "feat: artist expansion with per-artist deduplication"
```

---

## Task 5: AI Recommendations Function + Test

**Files:**
- Modify: `spotify_client.py` (add `get_recommendations`)
- Modify: `tests/test_helpers.py` (add test)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_helpers.py`:

```python
from spotify_client import get_recommendations

def test_get_recommendations_filters_existing_and_respects_limit():
    mock_sp = MagicMock()
    mock_sp.recommendations.return_value = {
        "tracks": [
            {"uri": "uri-existing"},   # already in playlist, skip
            {"uri": "uri-rec-1"},
            {"uri": "uri-rec-2"},
        ]
    }

    existing_uris = {"uri-existing"}
    seed_uris = ["uri-seed-1", "uri-seed-2"]

    result = get_recommendations(mock_sp, seed_uris, existing_uris, limit=25)

    assert [t["uri"] for t in result] == ["uri-rec-1", "uri-rec-2"]
    mock_sp.recommendations.assert_called_once_with(seed_tracks=["uri-seed-1", "uri-seed-2"], limit=25)


def test_get_recommendations_uses_at_most_5_seeds():
    mock_sp = MagicMock()
    mock_sp.recommendations.return_value = {"tracks": []}

    seeds = ["s1", "s2", "s3", "s4", "s5", "s6", "s7"]  # 7 seeds, must truncate to 5
    get_recommendations(mock_sp, seeds, set(), limit=10)

    call_args = mock_sp.recommendations.call_args
    assert len(call_args.kwargs["seed_tracks"]) == 5
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_helpers.py -k "recommendations" -v
```

Expected: FAIL with `ImportError`.

- [ ] **Step 3: Add `get_recommendations` to `spotify_client.py`**

```python
def get_recommendations(sp, seed_uris, existing_uris, limit=25):
    """
    Call Spotify's recommendations endpoint with up to 5 seed track URIs.
    Returns tracks not already in `existing_uris`.
    """
    if not seed_uris:
        return []
    seeds = seed_uris[:5]
    result = sp.recommendations(seed_tracks=seeds, limit=limit)
    return [t for t in result["tracks"] if t["uri"] not in existing_uris]
```

- [ ] **Step 4: Run all tests**

```bash
pytest tests/ -v
```

Expected: 8 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add spotify_client.py tests/test_helpers.py
git commit -m "feat: Spotify recommendations with seed deduplication"
```

---

## Task 6: Playlist Creation and Track-Adding Functions

**Files:**
- Modify: `spotify_client.py` (add 2 functions)

- [ ] **Step 1: Add functions to `spotify_client.py`**

```python
def create_playlist(sp, user_id, name):
    """Create a new private playlist. Returns playlist ID."""
    playlist = sp.user_playlist_create(user_id, name, public=False)
    return playlist["id"]


def add_tracks_in_batches(sp, playlist_id, uris):
    """Add track URIs to a playlist in batches of 100 (Spotify API limit)."""
    for i in range(0, len(uris), 100):
        sp.playlist_add_items(playlist_id, uris[i:i + 100])
```

- [ ] **Step 2: Run all tests to confirm nothing broke**

```bash
pytest tests/ -v
```

Expected: 7 tests PASS.

- [ ] **Step 3: Commit**

```bash
git add spotify_client.py
git commit -m "feat: playlist creation and batched track-adding"
```

---

## Task 7: Main Orchestration Script

**Files:**
- Create: `main.py`

- [ ] **Step 1: Write `main.py`**

```python
from spotify_client import (
    get_spotify_client,
    get_playlist_by_name,
    get_all_tracks,
    get_track_uris,
    get_unique_artist_ids,
    expand_by_artists,
    get_recommendations,
    create_playlist,
    add_tracks_in_batches,
    list_all_playlists,
)

SOURCE_PLAYLIST = "Road-trip Sing Alongs"
ARTIST_TRACKS_PER_ARTIST = 3
RECOMMENDATION_LIMIT = 25


def main():
    sp = get_spotify_client()
    user_id = sp.me()["id"]

    # Find source playlist
    source = get_playlist_by_name(sp, SOURCE_PLAYLIST)
    if not source:
        print(f"'{SOURCE_PLAYLIST}' not found. Your playlists:")
        playlists = list_all_playlists(sp)
        for i, (name, _) in enumerate(playlists):
            print(f"  {i + 1}. {name}")
        choice = int(input("Enter number to use as source: ")) - 1
        source = {"id": playlists[choice][1], "name": playlists[choice][0]}

    print(f"\nReading '{source['name']}'...")
    original_tracks = get_all_tracks(sp, source["id"])
    existing_uris = get_track_uris(original_tracks)
    print(f"  {len(original_tracks)} tracks found.")

    # Name the new playlist
    default_name = source["name"] + " Extended"
    new_name = input(f"\nNew playlist name [{default_name}]: ").strip() or default_name

    # Create and populate
    print(f"\nCreating '{new_name}'...")
    new_playlist_id = create_playlist(sp, user_id, new_name)

    print("Copying original tracks...")
    add_tracks_in_batches(sp, new_playlist_id, list(existing_uris))

    print("Finding more tracks from same artists...")
    artist_additions = expand_by_artists(sp, original_tracks, existing_uris, per_artist=ARTIST_TRACKS_PER_ARTIST)
    if artist_additions:
        all_uris = existing_uris | {t["uri"] for t in artist_additions}
        add_tracks_in_batches(sp, new_playlist_id, [t["uri"] for t in artist_additions])
    else:
        all_uris = set(existing_uris)

    print("Getting Spotify AI recommendations...")
    seed_uris = [item["track"]["uri"] for item in original_tracks[:5]]
    rec_additions = get_recommendations(sp, seed_uris, all_uris, limit=RECOMMENDATION_LIMIT)
    if rec_additions:
        add_tracks_in_batches(sp, new_playlist_id, [t["uri"] for t in rec_additions])

    total = len(existing_uris) + len(artist_additions) + len(rec_additions)
    print(f"\nDone! '{new_name}' created:")
    print(f"  {len(existing_uris)} original tracks")
    print(f"  {len(artist_additions)} added from existing artists")
    print(f"  {len(rec_additions)} AI-recommended tracks")
    print(f"  {total} total")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run all tests**

```bash
pytest tests/ -v
```

Expected: 7 tests PASS (main.py has no unit tests — verified end-to-end next).

- [ ] **Step 3: Commit**

```bash
git add main.py
git commit -m "feat: main orchestration script"
```

---

## Task 8: Spotify Developer App Setup + End-to-End Verification

**This task requires a real Spotify account.**

- [ ] **Step 1: Register a Spotify Developer App (one-time)**

1. Go to https://developer.spotify.com/dashboard
2. Log in with your Spotify account
3. Click **Create App**
4. Fill in any name/description, set Redirect URI to `http://localhost:8080/callback`
5. Copy **Client ID** and **Client Secret**

- [ ] **Step 2: Create your `.env` file**

```
SPOTIFY_CLIENT_ID=<paste your Client ID>
SPOTIFY_CLIENT_SECRET=<paste your Client Secret>
SPOTIFY_REDIRECT_URI=http://localhost:8080/callback
```

- [ ] **Step 3: Run the script**

```bash
python main.py
```

Expected flow:
- Browser opens → log in to Spotify → authorize the app → browser shows a blank page (that's normal)
- Terminal prints: `Reading 'Road-trip Sing Alongs'...` with track count
- Prompts for new playlist name (press Enter for default)
- Prints progress for each step
- Prints final summary with track counts

- [ ] **Step 4: Verify in Spotify**

Open Spotify → Your Library → find the new playlist. Confirm:
- Original tracks are present (spot-check 3-4)
- Additional tracks from the same artists appear (spot-check 1-2 artists)
- AI-recommended tracks appear and feel thematically similar
- No obvious duplicates

- [ ] **Step 5: Final push**

```bash
git push
```

---

## Spec Coverage Check

| Spec requirement | Covered by |
|-----------------|-----------|
| Copy original playlist | Task 7: `add_tracks_in_batches` with `existing_uris` |
| More songs from same artists (up to 3/artist) | Task 4: `expand_by_artists` |
| Spotify AI recommendations (25 tracks) | Task 5: `get_recommendations` |
| No duplicate tracks | Tasks 4 & 5: filter against `existing_uris` / `all_uris` |
| Playlist not found → fallback to list | Task 7: `list_all_playlists` fallback |
| New playlist is private | Task 6: `create_playlist` with `public=False` |
| GitHub repo | Task 1 |
| `.env` for credentials (gitignored) | Task 1 |
| Prompt for playlist name | Task 7: `input()` with default |
