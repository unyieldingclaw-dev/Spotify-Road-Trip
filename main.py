from spotify_client import (
    get_spotify_client,
    get_playlist_by_name,
    get_all_tracks,
    get_track_uris,
    expand_by_artists,
    get_recommendations,
    create_playlist,
    add_tracks_in_batches,
    list_all_playlists,
)

SOURCE_PLAYLIST = "Road-trip Sing Alongs"
ARTIST_TRACKS_PER_ARTIST = 3
RECOMMENDATION_LIMIT = 25


def main():
    sp = get_spotify_client()
    user_id = sp.me()["id"]

    # Find source playlist
    source = get_playlist_by_name(sp, SOURCE_PLAYLIST)
    if not source:
        print(f"'{SOURCE_PLAYLIST}' not found. Your playlists:")
        playlists = list_all_playlists(sp)
        for i, (name, _) in enumerate(playlists):
            print(f"  {i + 1}. {name}")
        choice = int(input("Enter number to use as source: ")) - 1
        source = {"id": playlists[choice][1], "name": playlists[choice][0]}

    print(f"\nReading '{source['name']}'...")
    original_tracks = get_all_tracks(sp, source["id"])
    existing_uris = get_track_uris(original_tracks)
    print(f"  {len(original_tracks)} tracks found.")

    # Name the new playlist
    default_name = source["name"] + " Extended"
    new_name = input(f"\nNew playlist name [{default_name}]: ").strip() or default_name

    # Create and populate
    print(f"\nCreating '{new_name}'...")
    new_playlist_id = create_playlist(sp, user_id, new_name)

    print("Copying original tracks...")
    add_tracks_in_batches(sp, new_playlist_id, list(existing_uris))

    print("Finding more tracks from same artists...")
    artist_additions = expand_by_artists(
        sp, original_tracks, existing_uris, per_artist=ARTIST_TRACKS_PER_ARTIST
    )
    if artist_additions:
        all_uris = existing_uris | {t["uri"] for t in artist_additions}
        add_tracks_in_batches(sp, new_playlist_id, [t["uri"] for t in artist_additions])
    else:
        all_uris = set(existing_uris)

    print("Getting Spotify AI recommendations...")
    seed_uris = [item["track"]["uri"] for item in original_tracks[:5]]
    rec_additions = get_recommendations(sp, seed_uris, all_uris, limit=RECOMMENDATION_LIMIT)
    if rec_additions:
        add_tracks_in_batches(sp, new_playlist_id, [t["uri"] for t in rec_additions])

    total = len(existing_uris) + len(artist_additions) + len(rec_additions)
    print(f"\nDone! '{new_name}' created:")
    print(f"  {len(existing_uris)} original tracks")
    print(f"  {len(artist_additions)} added from existing artists")
    print(f"  {len(rec_additions)} AI-recommended tracks")
    print(f"  {total} total")


if __name__ == "__main__":
    main()
