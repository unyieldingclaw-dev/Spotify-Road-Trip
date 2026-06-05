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
