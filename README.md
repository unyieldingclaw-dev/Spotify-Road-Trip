# Spotify Road Trip

A Python desktop app that takes your existing Spotify playlist and generates an expanded copy — preserving all original tracks, adding music from the same artists, and appending AI-recommended songs — with zero duplicate URIs.

Perfect for road trips, study sessions, or discovering new music from your favorite artists.

**Tech**: Python 3.10+ • Spotify Web API • customtkinter GUI

---

## Features

- ✅ **Expand any playlist** — select from your Spotify library
- ✅ **Artist deep-dive** — add up to 3 top tracks per original artist
- ✅ **AI recommendations** — up to 25 Spotify-curated songs based on your selection
- ✅ **Zero duplicates** — URI-based deduplication at every step
- ✅ **Desktop GUI** — no terminal required (Windows double-click launcher)
- ✅ **Real-time progress** — watch the generation happen
- ✅ **Secure credentials** — OAuth token cached locally, never committed to git

---

## Quick Start

### Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.10+ |
| Spotify Account | Free or Premium |

### Installation

```bash
pip install spotify-road-trip
# or clone and: pip install -r requirements.txt
```

### Usage

#### GUI (Recommended)
```bash
python app.py
# or just: run.bat (Windows)
```

1. **Authorize** — browser opens, sign in with Spotify
2. **Pick a playlist** — select from dropdown
3. **Adjust sliders**:
   - Artist tracks: 1–3 per artist
   - Recommendations: 0–25 suggestions
4. **Generate** — watch progress, then done!

#### CLI (Advanced)
```bash
python main.py --playlist "My Playlist" --artist-tracks 3 --recommendations 25
```

---

## How It Works

### 1. Read Source Playlist
```
Your Playlist (paginated API fetch)
↓
Extract all track URIs
```

### 2. Expand by Artist
```
For each original artist:
  → Fetch top tracks
  → Take up to N (user-selected)
  → Deduplicate against already-added
```

### 3. AI Recommendations
```
Send seed tracks to /recommendations endpoint
↓
Receive Spotify-curated songs
↓
Deduplicate, add to playlist
```

### 4. Create New Playlist
```
New private playlist on your account
↓
Add all tracks (original + artist + recommended)
```

---

## Project Structure

```
.
├── app.py                 # GUI entry point (customtkinter)
├── main.py                # CLI entry point
├── run.bat                # Windows launcher (no terminal)
│
├── src/
│   ├── spotify_client.py   # Wrapper around spotipy, OAuth caching
│   ├── playlist_expander.py# Core generation logic
│   ├── deduplicator.py     # URI-based dedup
│   └── config.py           # Environment, credentials
│
└── tests/
    ├── test_spotify_client.py
    ├── test_playlist_expander.py
    └── test_deduplicator.py
```

---

## Configuration

### Environment Variables

Create `.env` in the project root:

```bash
# Spotify Developer App (create at https://developer.spotify.com/dashboard)
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback

# Optional
DEBUG=false
```

**Important**: `.env` and `.spotify_cache` are `.gitignore`-d and never committed.

---

## Development

### Run Tests

```bash
pytest tests/ -v
# All 10 tests pass ✅
# Mocks Spotify API — no real calls during testing
```

### Add a Feature

1. Write test(s) first — mock the Spotify client
2. Implement in `src/`
3. Add GUI element to `app.py` if user-facing
4. Update README

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Local Python app, not web** | No server overhead, work offline (after initial playlist fetch) |
| **URI deduplication, not track ID** | URIs are Spotify's canonical identifier; handles regional variants |
| **Mock Spotify in tests** | Respects API quota, fast iteration, reliable test runs |
| **customtkinter GUI** | Dark theme, modern look, cross-platform (Windows/Mac/Linux) |
| **Token cached locally** | Faster auth flows, user can revoke anytime via Spotify settings |

---

## Constraints & Non-Goals

**🚫 Out of Scope**:
- Multi-account support
- Cloud storage or sync
- Playlist editing / merge
- Duplicate detection across your entire library
- Web version

---

## Troubleshooting

### "Authorization failed"
- Check `.env` has correct `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET`
- Verify redirect URI matches Spotify app settings exactly

### "No playlists found"
- Ensure you're signed in with the correct Spotify account
- Only shows playlists you own or collaborate on

### "GUI won't launch"
- Try `python app.py` from terminal to see error output
- Verify customtkinter is installed: `pip install customtkinter`

---

## Status

| Phase | Status | Description |
|-------|--------|-------------|
| **CLI** | ✅ Complete | OAuth + playlist expansion + recommendations |
| **GUI** | ✅ Complete | customtkinter UI, progress bars, sliders |
| **Testing** | ✅ Complete | 10 unit tests, 100% mocked |

---

## Documentation

- **Project Brief**: `memory-bank/projectbrief.md`
- **Development**: `CLAUDE.md`
- **Tech Stack**: `memory-bank/techContext.md`

---

**Contributors**: UnyieldingClaw (you), Claude  
**License**: Private
