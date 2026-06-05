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
