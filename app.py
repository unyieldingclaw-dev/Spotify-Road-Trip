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


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Road-trip Playlist Generator")
        self.geometry("440x540")
        self.resizable(False, False)

        self._queue = queue.Queue()
        self._playlists = []   # list of (name, id) tuples
        self._sp = None
        self._generating = False

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_ui()
        self._start_auth()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Status line (connection info)
        self._status_label = ctk.CTkLabel(
            self, text="Connecting to Spotify…", font=ctk.CTkFont(size=13)
        )
        self._status_label.pack(pady=(20, 4))

        # Source playlist
        ctk.CTkLabel(self, text="Source playlist:", anchor="w").pack(
            fill="x", padx=24, pady=(16, 2)
        )
        self._playlist_var = ctk.StringVar(value="Loading…")
        self._playlist_menu = ctk.CTkOptionMenu(
            self,
            variable=self._playlist_var,
            values=["Loading…"],
            command=self._on_playlist_select,
            state="disabled",
            width=392,
        )
        self._playlist_menu.pack(padx=24)

        # New playlist name
        ctk.CTkLabel(self, text="New playlist name:", anchor="w").pack(
            fill="x", padx=24, pady=(14, 2)
        )
        self._name_entry = ctk.CTkEntry(self, width=392, state="disabled")
        self._name_entry.pack(padx=24)

        # Artist tracks slider
        artist_row = ctk.CTkFrame(self, fg_color="transparent")
        artist_row.pack(fill="x", padx=24, pady=(14, 0))
        ctk.CTkLabel(artist_row, text="Artist tracks per artist:").pack(side="left")
        self._artist_val_label = ctk.CTkLabel(artist_row, text="3", width=24)
        self._artist_val_label.pack(side="right")
        self._artist_slider = ctk.CTkSlider(
            self, from_=1, to=5, number_of_steps=4,
            command=lambda v: self._artist_val_label.configure(text=str(int(v))),
            state="disabled", width=392,
        )
        self._artist_slider.set(3)
        self._artist_slider.pack(padx=24)

        # AI recommendations slider
        rec_row = ctk.CTkFrame(self, fg_color="transparent")
        rec_row.pack(fill="x", padx=24, pady=(14, 0))
        ctk.CTkLabel(rec_row, text="AI recommendations:").pack(side="left")
        self._rec_val_label = ctk.CTkLabel(rec_row, text="25", width=32)
        self._rec_val_label.pack(side="right")
        self._rec_slider = ctk.CTkSlider(
            self, from_=5, to=50, number_of_steps=45,
            command=lambda v: self._rec_val_label.configure(text=str(int(v))),
            state="disabled", width=392,
        )
        self._rec_slider.set(25)
        self._rec_slider.pack(padx=24)

        # Generate button
        self._generate_btn = ctk.CTkButton(
            self, text="Generate ▶", command=self._on_generate,
            state="disabled", width=392, height=44,
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        self._generate_btn.pack(padx=24, pady=(20, 0))

        # Progress bar — hidden until Generate is clicked
        self._progress_bar = ctk.CTkProgressBar(self, width=392)
        self._progress_bar.set(0)

        # Status log — hidden until Generate is clicked
        self._log = ctk.CTkTextbox(self, width=392, height=130, state="disabled")

    # ── Auth ──────────────────────────────────────────────────────────────────

    def _start_auth(self):
        threading.Thread(target=self._auth_worker, daemon=True).start()
        self.after(100, self._poll_queue)

    def _auth_worker(self):
        try:
            self._queue.put({"type": "status", "msg": "Opening Spotify in your browser for login…"})
            sp = get_spotify_client()
            user = sp.me()
            playlists = list_all_playlists(sp)
            self._sp = sp
            self._queue.put({
                "type": "auth_done",
                "user": user.get("display_name") or user["id"],
                "playlists": playlists,
            })
        except Exception as e:
            self._queue.put({"type": "auth_error", "msg": f"Auth failed: {e}"})

    # ── Queue polling ─────────────────────────────────────────────────────────

    def _poll_queue(self):
        while not self._queue.empty():
            self._handle_message(self._queue.get_nowait())
        self.after(100, self._poll_queue)

    def _handle_message(self, msg):
        t = msg["type"]
        if t == "status":
            self._status_label.configure(text=msg["msg"])
        elif t == "auth_done":
            self._status_label.configure(text=f"Connected as: {msg['user']}")
            self._playlists = msg["playlists"]
            names = [name for name, _ in self._playlists]
            self._playlist_menu.configure(values=names, state="normal")
            default = next(
                (n for n in names if n == SOURCE_PLAYLIST_DEFAULT),
                names[0] if names else "",
            )
            self._playlist_var.set(default)
            self._on_playlist_select(default)
            for widget in (self._name_entry, self._artist_slider,
                           self._rec_slider, self._generate_btn):
                widget.configure(state="normal")
        elif t == "progress":
            self._progress_bar.set(msg["pct"])
            self._append_log(msg["msg"])
        elif t == "auth_error":
            self._status_label.configure(text=f"✗ {msg['msg']}")
            # Keep Generate disabled — sp is None, generation cannot proceed
        elif t == "done":
            self._generating = False
            self._progress_bar.set(1.0)
            self._append_log(msg["msg"])
            self._generate_btn.configure(state="normal", text="Generate ▶")
        elif t == "error":
            self._generating = False
            self._append_log(f"✗ {msg['msg']}")
            self._generate_btn.configure(state="normal", text="Generate ▶")
            self._status_label.configure(text="Error — see log below")

    # ── UI helpers ────────────────────────────────────────────────────────────

    def _on_playlist_select(self, selected_name):
        self._name_entry.configure(state="normal")
        self._name_entry.delete(0, "end")
        self._name_entry.insert(0, f"{selected_name} Extended")

    def _append_log(self, msg):
        self._log.configure(state="normal")
        self._log.insert("end", msg + "\n")
        self._log.see("end")
        self._log.configure(state="disabled")

    # ── Generate ──────────────────────────────────────────────────────────────

    def _on_generate(self):
        selected_name = self._playlist_var.get()
        playlist_id = next(
            (pid for name, pid in self._playlists if name == selected_name), None
        )
        if not playlist_id:
            return

        new_name = self._name_entry.get().strip() or f"{selected_name} Extended"
        per_artist = int(self._artist_slider.get())
        rec_limit = int(self._rec_slider.get())

        # Expand window and reveal progress widgets
        self.geometry("440x740")
        self._progress_bar.pack(padx=24, pady=(14, 0))
        self._log.pack(padx=24, pady=(10, 20))

        self._generating = True
        self._generate_btn.configure(state="disabled", text="Generating…")
        self._progress_bar.set(0)

        threading.Thread(
            target=self._generate_worker,
            args=(playlist_id, selected_name, new_name, per_artist, rec_limit),
            daemon=True,
        ).start()

    def _generate_worker(self, source_id, source_name, new_name, per_artist, rec_limit):
        def on_progress(pct, msg):
            self._queue.put({"type": "progress", "pct": pct, "msg": msg})

        try:
            on_progress(0.05, "⟳ Starting generation…")
            result = generate_playlist(
                self._sp, source_id, source_name, new_name,
                per_artist, rec_limit, on_progress,
            )
            self._queue.put({
                "type": "done",
                "msg": (
                    f"🎉 {result['total']} total  ·  "
                    f"{result['original']} original  ·  "
                    f"{result['artist']} artist  ·  "
                    f"{result['recommended']} AI"
                ),
            })
        except Exception as e:
            self._queue.put({"type": "error", "msg": str(e)})

    # ── Close guard ───────────────────────────────────────────────────────────

    def _on_close(self):
        if self._generating:
            import tkinter.messagebox as mb
            if not mb.askyesno(
                "Generation in progress",
                "A playlist is still being generated. Close anyway?\n\n"
                "Closing now may leave a partial playlist in your Spotify account.",
            ):
                return
        self.destroy()


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
