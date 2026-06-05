from unittest.mock import MagicMock
from spotify_client import get_track_uris, get_unique_artist_ids, expand_by_artists


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


def test_expand_by_artists_limits_per_artist_and_deduplicates():
    # Artist "a1" has 5 top tracks; we should only take 2 (per_artist=2)
    # Track "uri-orig" is already in existing_uris — must be skipped
    mock_sp = MagicMock()
    mock_sp.artist_top_tracks.return_value = {
        "tracks": [
            {"uri": "uri-orig",  "artists": [{"id": "a1"}]},  # already exists, skip
            {"uri": "uri-new-1", "artists": [{"id": "a1"}]},
            {"uri": "uri-new-2", "artists": [{"id": "a1"}]},
            {"uri": "uri-new-3", "artists": [{"id": "a1"}]},  # over limit, skip
        ]
    }

    original_items = [_make_track_item("uri-orig", ["a1"])]
    existing_uris = get_track_uris(original_items)

    result = expand_by_artists(mock_sp, original_items, existing_uris, per_artist=2)

    assert [t["uri"] for t in result] == ["uri-new-1", "uri-new-2"]


def test_expand_by_artists_multiple_artists_respected_independently():
    # Two artists; per_artist=2 limit applies to each independently
    mock_sp = MagicMock()
    mock_sp.artist_top_tracks.side_effect = [
        {"tracks": [
            {"uri": "uri-a1-1", "artists": [{"id": "a1"}]},
            {"uri": "uri-a1-2", "artists": [{"id": "a1"}]},
            {"uri": "uri-a1-3", "artists": [{"id": "a1"}]},  # over limit
        ]},
        {"tracks": [
            {"uri": "uri-a2-1", "artists": [{"id": "a2"}]},
            {"uri": "uri-a2-2", "artists": [{"id": "a2"}]},
            {"uri": "uri-a2-3", "artists": [{"id": "a2"}]},  # over limit
        ]},
    ]

    original_items = [
        _make_track_item("uri-orig-1", ["a1"]),
        _make_track_item("uri-orig-2", ["a2"]),
    ]
    existing_uris = get_track_uris(original_items)

    result = expand_by_artists(mock_sp, original_items, existing_uris, per_artist=2)

    assert [t["uri"] for t in result] == ["uri-a1-1", "uri-a1-2", "uri-a2-1", "uri-a2-2"]
