---
authority: immutable
review-cycle: never
retention: permanent
staleness-threshold: 365d
tags:
  - requirements/core
  - constraints/non-negotiable
last-reviewed: 2026-06-06
compaction_generation: 1
source_type: canonical
confidence: high
lineage: []
---

# Project Brief

**Last Updated**: 2026-06-06

## Core Purpose

A Python desktop application that takes a user's existing Spotify playlist and generates an expanded copy — preserving all original tracks, adding more songs from the same artists, and appending Spotify AI-recommended tracks — with zero duplicate URIs. Available as a CLI (`main.py`) and a double-clickable GUI (`app.py` + `run.bat`).

## Non-Negotiable Constraints

### Business Requirements
- No duplicate tracks in the generated playlist (URI-based deduplication is mandatory at every step)
- Must use Spotify's `/recommendations` endpoint for AI-curated suggestions (Zapier cannot expose this)
- Credentials never committed to git (`.env` and `.spotify_cache` are gitignored)

### Technical Constraints
- Windows 11 development environment
- Python 3.10+ only — no backend server, no Docker, no database
- All Spotify API calls via `spotipy` (Authorization Code flow, token cached in `.spotify_cache`)
- No real Spotify API calls in tests — mock all Spotify client methods

### User Experience
- GUI launches without a terminal window (via `pythonw.exe` + `run.bat`)
- Progress visible in real time during generation
- Closing during generation shows a confirmation dialog (warns about partial playlists)

## Key Goals

### Phase 1 — CLI (Complete)
- [x] OAuth login + token caching
- [x] Read source playlist (paginated)
- [x] Create new private playlist
- [x] Copy original tracks
- [x] Add artist top-tracks (up to 3/artist, no duplicates)
- [x] Add AI recommendations (up to 25, no duplicates)
- [x] Print summary

### Phase 2 — GUI (Complete)
- [x] customtkinter dark-theme desktop window (440×540px)
- [x] Playlist picker dropdown
- [x] Sliders for artist-tracks and recommendation limits
- [x] Background threading with queue-based progress updates
- [x] Double-click launcher (`run.bat`)
- [x] Close-while-generating confirmation guard

### Future
- [ ] Duplicate detection across the user's full Spotify library
- [ ] Export playlist to text/CSV

## Success Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Unit tests passing | 10 | 10 |
| Duplicate tracks in output | 0 | 0 |
| GUI launch (no terminal) | Yes | Yes |

## Stakeholders

| Role | Person/Team | Responsibility |
|------|-------------|----------------|
| Primary User | UnyieldingClaw | Uses the app to generate road-trip playlists |
| Development | UnyieldingClaw + Claude | Builds and maintains the codebase |

## Out of Scope

- Web server or REST API
- Database or persistent storage beyond the token cache
- Mobile app
- Multi-user / multi-account support
