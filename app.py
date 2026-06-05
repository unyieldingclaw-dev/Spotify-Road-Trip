import threading
import queue

import customtkinter as ctk

from spotify_client import (
    get_spotify_client,
    list_all_playlists,
    get_all_tracks,
    get_track_uris,
    expand_by_artists,
    get_recommendations,
    create_playlist,
    add_tracks_in_batches,
)

SOURCE_PLAYLIST_DEFAULT = "Road-trip Sing Alongs"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


def generate_playlist(sp, source_id, source_name, new_name, per_artist, rec_limit, on_progress):
    """
    Run full playlist generation. Thread-safe: communicates only via on_progress callback.

    Args:
        sp: authenticated spotipy.Spotify client
        source_id: Spotify playlist ID to copy from
        source_name: display name of the source playlist (for status messages)
        new_name: name for the new playlist
        per_artist: max tracks to add per artist
        rec_limit: max AI-recommended tracks to add
        on_progress: callable(pct: float, msg: str) called at each step

    Returns:
        dict with keys: original, artist, recommended, total
    """
    user_id = sp.me()["id"]

    on_progress(0.30, f"⟳ Reading '{source_name}'…")
    original_tracks = get_all_tracks(sp, source_id)
    existing_uris = get_track_uris(original_tracks)
    on_progress(0.40, f"✓ Read {len(original_tracks)} tracks")

    on_progress(0.45, f"⟳ Creating '{new_name}'…")
    new_playlist_id = create_playlist(sp, user_id, new_name)

    on_progress(0.50, "⟳ Copying original tracks…")
    add_tracks_in_batches(sp, new_playlist_id, list(existing_uris))
    on_progress(0.60, f"✓ Copied {len(existing_uris)} original tracks")

    on_progress(0.65, "⟳ Finding artist tracks…")
    artist_additions = expand_by_artists(
        sp, original_tracks, existing_uris, per_artist=per_artist
    )
    if artist_additions:
        all_uris = existing_uris | {t["uri"] for t in artist_additions}
        add_tracks_in_batches(sp, new_playlist_id, [t["uri"] for t in artist_additions])
    else:
        all_uris = set(existing_uris)
    on_progress(0.80, f"✓ Added {len(artist_additions)} artist tracks")

    on_progress(0.85, "⟳ Getting AI recommendations…")
    seed_uris = [item["track"]["uri"] for item in original_tracks[:5]]
    rec_additions = get_recommendations(sp, seed_uris, all_uris, limit=rec_limit)
    if rec_additions:
        add_tracks_in_batches(sp, new_playlist_id, [t["uri"] for t in rec_additions])
    on_progress(0.95, f"✓ Added {len(rec_additions)} AI recommendations")

    total = len(existing_uris) + len(artist_additions) + len(rec_additions)
    on_progress(1.0, f"\U0001f389 Done! {total} total tracks in '{new_name}'")

    return {
        "original": len(existing_uris),
        "artist": len(artist_additions),
        "recommended": len(rec_additions),
        "total": total,
    }
