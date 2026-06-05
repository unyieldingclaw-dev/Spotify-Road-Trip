from unittest.mock import MagicMock, patch
from app import generate_playlist


def _make_track(uri, artist_id):
    return {"track": {"uri": uri, "artists": [{"id": artist_id}]}}


def test_generate_playlist_returns_correct_counts():
    mock_sp = MagicMock()
    mock_sp.me.return_value = {"id": "user123"}

    progress_log = []

    with (
        patch("app.get_all_tracks") as mock_tracks,
        patch("app.get_track_uris") as mock_uris,
        patch("app.create_playlist") as mock_create,
        patch("app.add_tracks_in_batches"),
        patch("app.expand_by_artists") as mock_expand,
        patch("app.get_recommendations") as mock_recs,
    ):
        mock_tracks.return_value = [
            _make_track("uri-1", "a1"),
            _make_track("uri-2", "a2"),
        ]
        mock_uris.return_value = {"uri-1", "uri-2"}
        mock_create.return_value = "new-playlist-id"
        mock_expand.return_value = [{"uri": "uri-3"}]
        mock_recs.return_value = [{"uri": "uri-4"}, {"uri": "uri-5"}]

        result = generate_playlist(
            mock_sp, "source-id", "My Playlist", "My Playlist Extended",
            per_artist=3, rec_limit=25,
            on_progress=lambda pct, msg: progress_log.append((pct, msg)),
        )

    assert result == {"original": 2, "artist": 1, "recommended": 2, "total": 5}
    assert any(pct == 1.0 for pct, _ in progress_log), "must reach 100%"
    assert any("Done" in msg for _, msg in progress_log), "must report Done"


def test_generate_playlist_handles_empty_artist_and_rec_additions():
    mock_sp = MagicMock()
    mock_sp.me.return_value = {"id": "user123"}

    with (
        patch("app.get_all_tracks") as mock_tracks,
        patch("app.get_track_uris") as mock_uris,
        patch("app.create_playlist") as mock_create,
        patch("app.add_tracks_in_batches"),
        patch("app.expand_by_artists") as mock_expand,
        patch("app.get_recommendations") as mock_recs,
    ):
        mock_tracks.return_value = [_make_track("uri-1", "a1")]
        mock_uris.return_value = {"uri-1"}
        mock_create.return_value = "playlist-id"
        mock_expand.return_value = []
        mock_recs.return_value = []

        result = generate_playlist(
            mock_sp, "source-id", "Source", "New",
            per_artist=3, rec_limit=25,
            on_progress=lambda pct, msg: None,
        )

    assert result == {"original": 1, "artist": 0, "recommended": 0, "total": 1}
