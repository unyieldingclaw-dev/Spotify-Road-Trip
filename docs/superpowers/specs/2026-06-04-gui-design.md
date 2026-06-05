# Spotify Playlist Generator — GUI Design Spec
**Date:** 2026-06-04

## Context

The existing CLI script (`main.py`) requires the user to open a terminal, type a command, and respond to text prompts. The goal is to replace that workflow with a double-clickable desktop app — no terminal, no typing commands. The user opens the app, picks a playlist, adjusts two sliders, and hits Generate.

## Goal

A customtkinter desktop GUI (`app.py`) that wraps the existing `spotify_client.py` functions. Launched via `run.bat` (double-click, no terminal window). The CLI `main.py` is kept but no longer the primary entry point.

## Layout

Single window (~420×540px, dark theme):

```
┌──────────────────────────────────┐
│  🎵 Road-trip Playlist Generator │
│  Connected as: [username]        │
│                                  │
│  Source playlist:                │
│  [ Road-trip Sing Alongs    ▼ ]  │
│                                  │
│  New playlist name:              │
│  [ Road-trip Sing Alongs Extended│
│                                  │
│  Artist tracks per artist:  3    │
│  ○────────●──────────────────    │
│                                  │
│  AI recommendations:       25    │
│  ○──────────────●────────────    │
│                                  │
│       [ Generate ▶ ]             │
│                                  │
│  ████████████░░░ 65%             │
│  ✓ Copied 47 tracks              │
│  ✓ Added 23 artist tracks        │
│  ⟳ Getting AI recommendations…  │
└──────────────────────────────────┘
```

## UI States

### 1. Startup / Connecting
- Window appears immediately
- Status shows "Connecting to Spotify…"
- All controls disabled
- If first run: "Opening Spotify in your browser for login…" — browser opens for OAuth
- On success: status shows "Connected as [display name]", controls enabled, playlist dropdown populated

### 2. Ready
- Source playlist dropdown populated with all user playlists
- "Road-trip Sing Alongs" pre-selected if found, otherwise first playlist
- New playlist name auto-filled: `[source name] Extended`
- Artist tracks slider: range 1–5, default 3, live label update
- AI recommendations slider: range 5–50, default 25, live label update
- Generate button enabled

### 3. Generating
- Generate button disabled, shows "Generating…"
- Progress bar appears (0–100%)
- Status log appends lines as each step completes:
  - `⟳ Reading '[source]'…`
  - `✓ Read 47 tracks`
  - `⟳ Creating '[new name]'…`
  - `✓ Copied 47 original tracks`
  - `⟳ Finding artist tracks…`
  - `✓ Added 23 artist tracks`
  - `⟳ Getting AI recommendations…`
  - `✓ Added 19 AI recommendations`

### 4. Done
- Progress bar fills to 100%
- Summary line: `Done! 89 total tracks in '[new name]'`
- Generate button re-enabled (user can run again with different settings)

### 5. Error
- If any step fails, status log shows `✗ [error message]` in red
- Generate button re-enabled so user can retry

## Architecture

### Files

| File | Purpose |
|------|---------|
| `app.py` | customtkinter GUI — all UI logic |
| `run.bat` | Double-click launcher using `pythonw.exe` |
| `spotify_client.py` | **Unchanged** — all API calls live here |
| `main.py` | **Unchanged** — CLI still works |

### Threading Model

All Spotify API calls run in a `threading.Thread` to prevent the GUI from freezing. Communication from worker → UI uses a `queue.Queue`:

```
Worker thread  →  queue.put({"type": "progress", "pct": 40, "msg": "✓ Copied tracks"})
Main thread    →  polls queue via root.after(100, poll_queue)
               →  updates progress bar + status log
```

### `run.bat`

```bat
@echo off
start "" pythonw "%~dp0app.py"
```

`pythonw.exe` is the no-console Python binary — zero terminal window appears.

## Dependencies

Add to `requirements.txt`:
```
customtkinter>=5.2.0
```

All other dependencies (`spotipy`, `python-dotenv`) already present.

## Progress Steps & Percentages

| Step | Progress |
|------|----------|
| Auth complete | 5% |
| Playlists loaded | 15% |
| Source tracks read | 30% |
| New playlist created | 40% |
| Original tracks copied | 55% |
| Artist tracks added | 75% |
| AI recommendations added | 95% |
| Done | 100% |

## Verification

1. Double-click `run.bat` — window opens, no terminal appears
2. First run: browser opens for Spotify auth; window shows "Opening Spotify in your browser…"
3. After auth: dropdown populates with user's playlists, "Road-trip Sing Alongs" pre-selected
4. Drag artist slider to 5 — label next to slider updates live
5. Click Generate — progress bar advances through all steps
6. Open Spotify — verify new playlist exists with correct tracks
7. Click Generate again — creates a second playlist (doesn't overwrite)
8. Close and re-open `run.bat` — no browser auth this time (cached token)
