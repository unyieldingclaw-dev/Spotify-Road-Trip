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
