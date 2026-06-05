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
        for artist in item["track"]["artists"]:
            if artist["id"] not in seen:
                seen.add(artist["id"])
                artist_ids.append(artist["id"])
    return artist_ids
