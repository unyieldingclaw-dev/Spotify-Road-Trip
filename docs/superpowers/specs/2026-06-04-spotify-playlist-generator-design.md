# Spotify Road-Trip Playlist Generator — Design Spec
**Date:** 2026-06-04

## Context

The user has an existing Spotify playlist called "Road-trip Sing Alongs" and wants to generate a new, expanded playlist based on it. The new playlist should be a copy of the original, augmented with:
1. Additional songs from the same artists already in the playlist
2. AI-curated similar tracks via Spotify's recommendations endpoint

The project starts from an empty directory and needs a GitHub repo.

## Goal

A Python CLI script that reads the existing playlist, creates a new named playlist, and populates it with the original tracks plus curated expansions — no duplicates.

## Approach: Python + Spotify Web API (spotipy)

A single `main.py` script using the `spotipy` library. One-time OAuth browser login; subsequent runs use a cached token.

**Why not Zapier:** Zapier's Spotify integration doesn't expose the `/recommendations` endpoint, which is required for AI-based song suggestions.

## Architecture

### Auth
- Spotify OAuth 2.0 Authorization Code flow
- `spotipy` manages the token cache (`.spotify_cache` file, gitignored)
- Scopes needed: `playlist-read-private`, `playlist-modify-public`, `playlist-modify-private`
- Credentials stored in `.env` (gitignored)

### Script Flow (`main.py`)

1. Authenticate with Spotify (browser popup on first run, silent after)
2. Search user's playlists for "Road-trip Sing Alongs" — if not found, list all playlists and prompt user to pick
3. Fetch all tracks from the source playlist
4. Prompt user for new playlist name (default: "Road-trip Extended")
5. Create the new playlist (private by default)
6. Copy all original tracks into the new playlist
7. Collect unique artists from original tracks
8. For each artist, fetch their top tracks; add up to **3 per artist** not already in the playlist
9. Pick up to 5 seed tracks from the original and call `/recommendations`; add up to **25 AI-recommended tracks** not already in the playlist
10. Print a summary: original count, artist expansions added, AI recommendations added

### Deduplication
Track URIs (Spotify's unique track identifier) are used for all duplicate checks. Before any add step, filter against the running set of already-included URIs.

### Error Handling
- Playlist not found → list all playlists, let user pick by number
- Spotify API rate limits → `spotipy` retries automatically
- Token expiry → `spotipy` refreshes automatically via cached refresh token

## File Structure

```
Spotify-Road-Trip/
├── main.py              # CLI entry point
├── spotify_client.py    # All Spotify API wrappers + pure helpers
├── app.py               # GUI (customtkinter) + generate_playlist()
├── run.bat              # Double-click launcher (no terminal)
├── .env                 # CLIENT_ID, CLIENT_SECRET, REDIRECT_URI (gitignored)
├── .env.example         # template
├── requirements.txt     # spotipy, python-dotenv, pytest, customtkinter
├── .gitignore
├── tests/
│   ├── __init__.py
│   ├── test_helpers.py
│   └── test_app.py
└── docs/
    └── superpowers/
        └── specs/
            └── 2026-06-04-spotify-playlist-generator-design.md
```

## GitHub Repo

- New repo: `UnyieldingClaw/Spotify-Road-Trip`
- `.gitignore` excludes: `.env`, `.spotify_cache`, `__pycache__/`, `*.pyc`
- Initial commit includes all project files except credentials

## Dependencies

```
spotipy>=2.23.0
python-dotenv>=1.0.0
pytest
customtkinter>=5.2.0
```

## Setup Instructions (for spec)

1. Go to https://developer.spotify.com/dashboard → Create App
2. Set Redirect URI to `http://localhost:8080/callback`
3. Copy Client ID and Client Secret into `.env`
4. Run `pip install -r requirements.txt`
5. Run `python main.py` — browser opens for Spotify login on first run

## Verification

- Run `python main.py` with a real Spotify account
- Confirm the new playlist appears in Spotify with the original tracks
- Confirm artist expansions are present (spot-check 2-3 artists)
- Confirm no duplicate tracks in the new playlist
- Confirm AI recommendation tracks appear and are thematically similar
