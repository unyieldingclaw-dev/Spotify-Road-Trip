---
authority: stable
review-cycle: 30d
retention: permanent
staleness-threshold: 90d
tags:
  - stack/backend
  - stack/frontend
  - env/tools
last-reviewed: 2026-06-06
compaction_generation: 1
source_type: canonical
confidence: high
lineage: []
---

# Technical Context & Stack

**Last Updated**: 2026-06-06

## Development Environment

| Component | Value |
|-----------|-------|
| OS | Windows 11 Home 10.0.26200 |
| Shell | PowerShell (primary); bash available via Bash tool |
| Package Manager | pip |
| Git Remote | github.com/UnyieldingClaw/Spotify-Road-Trip (branch: master) |

## Stack

### Language & Runtime
- **Language**: Python 3.10+
- **No backend server** — pure desktop/CLI application; no Flask, FastAPI, or database

### GUI
- **Framework**: customtkinter>=5.2.0
- **Theme**: dark appearance, blue color (`ctk.set_appearance_mode("dark")`, `ctk.set_default_color_theme("blue")`)
- **Threading**: `threading.Thread` + `queue.Queue` (progress events polled via `root.after(100, ...)`)

### Spotify Integration
- **Library**: spotipy>=2.23.0
- **Auth flow**: OAuth 2.0 Authorization Code (browser popup on first run)
- **Token cache**: `.spotify_cache` (gitignored, auto-managed by spotipy)
- **Scopes**: `playlist-read-private playlist-modify-public playlist-modify-private`

### Testing
- **Framework**: pytest
- **Mocking**: `unittest.mock.MagicMock`, `unittest.mock.patch`

## Dependencies

```
spotipy>=2.23.0
python-dotenv>=1.0.0
pytest
customtkinter>=5.2.0
```

## Configuration

### Environment Variables

```bash
# Required — stored in .env (gitignored)
SPOTIFY_CLIENT_ID=<from Spotify Developer Dashboard>
SPOTIFY_CLIENT_SECRET=<from Spotify Developer Dashboard>
SPOTIFY_REDIRECT_URI=http://localhost:8080/callback
```

### Configuration Files

| File | Purpose |
|------|---------|
| `.env` | Spotify API credentials (gitignored) |
| `.env.example` | Credential template (committed) |
| `.spotify_cache` | OAuth token cache (gitignored) |
| `run.bat` | Double-click launcher: `pythonw app.py` (no terminal window) |

## File Structure

```
Spotify-Road-Trip/
├── main.py              # CLI entry point
├── spotify_client.py    # All Spotify API wrappers + pure helpers
├── app.py               # GUI (customtkinter) + generate_playlist()
├── run.bat              # Double-click launcher (pythonw, no terminal)
├── requirements.txt
├── .env                 # gitignored
├── .env.example
├── .gitignore
└── tests/
    ├── __init__.py
    ├── test_helpers.py  # 8 unit tests for spotify_client functions
    └── test_app.py      # 2 unit tests for generate_playlist()
```

## Key Constants

| Constant | File | Value |
|----------|------|-------|
| `SOURCE_PLAYLIST` | main.py | `"Road-trip Sing Alongs"` |
| `SOURCE_PLAYLIST_DEFAULT` | app.py | `"Road-trip Sing Alongs"` |
| `ARTIST_TRACKS_PER_ARTIST` | main.py | `3` |
| `RECOMMENDATION_LIMIT` | main.py | `25` |

## External Service Constraints

### Spotify Web API
- **Auth**: Authorization Code flow (browser popup first run, silent after via cached refresh token)
- **Rate limiting**: spotipy retries 429s automatically
- **Batch limit**: `playlist_add_items` accepts max 100 URIs per call — use `add_tracks_in_batches`
- **Recommendations**: `/recommendations` requires 1–5 seed tracks; calling with 0 seeds raises an API error
- **Artist top tracks**: returns at most 10 tracks per artist (country-filtered, default `"US"`)

## GUI Window Sizes

| State | Geometry |
|-------|---------|
| Initial / connecting | 440×540 |
| After Generate clicked | 440×740 (expands to show progress bar + log) |

## Development Workflow

### Running the GUI

```bat
run.bat             # double-click — no terminal window
```
```bash
python app.py       # from terminal
```

### Running the CLI

```bash
python main.py
```

### Running Tests

```bash
pytest tests/ -v
```

Expected: **10 tests PASS** (8 in `test_helpers.py`, 2 in `test_app.py`)

## Deployment

### Current State
- **Environment**: local desktop, Windows 11
- **Distribution**: git clone + `pip install -r requirements.txt` + populate `.env`
