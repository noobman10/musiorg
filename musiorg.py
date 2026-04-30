#!/usr/bin/env python3
"""
musiorg — Music Organizer TUI
Scans a music directory, reads genre tags, and moves files into genre subfolders.
Detects duplicate tracks by title tag (falls back to filename stem).
"""

import os
import shutil
from pathlib import Path
from collections import defaultdict

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.reactive import reactive
from textual.widgets import (
    Header, Footer, Static, Label, Button,
    ProgressBar, DataTable, Input, Log, Checkbox,
)
from textual.screen import Screen, ModalScreen
from textual import work

try:
    from mutagen import File as MutagenFile
except ImportError:
    MutagenFile = None

# ── constants ────────────────────────────────────────────────────────────────

AUDIO_EXTENSIONS = {
    ".mp3", ".flac", ".ogg", ".opus", ".m4a", ".aac",
    ".wav", ".wma", ".aiff", ".ape", ".wv", ".mp4",
}

UNKNOWN_GENRE = "Unknown"
TRASH_FOLDER  = ".musiorg_trash"

APP_CSS = """
/* ── Root ── */
Screen {
    background: #0e0e12;
}

/* ── Header / Footer ── */
Header {
    background: #0e0e12;
    color: #c084fc;
    text-style: bold;
    border-bottom: solid #2d1f4e;
}
Footer {
    background: #0e0e12;
    color: #6b6b8a;
    border-top: solid #2d1f4e;
}

/* ── Panels ── */
.panel {
    border: solid #2d1f4e;
    background: #13131a;
    padding: 1 2;
    margin: 0 1;
}
.panel-title {
    color: #c084fc;
    text-style: bold;
    margin-bottom: 1;
}

/* ── Path input row ── */
#path-row {
    height: 5;
    padding: 0 1;
    align: center middle;
}
#path-label {
    color: #a78bfa;
    width: auto;
    margin-right: 1;
}
#path-input {
    background: #1a1a26;
    border: solid #3b2f6b;
    color: #e2d9f3;
    width: 1fr;
}
#path-input:focus {
    border: solid #c084fc;
}

/* ── Buttons ── */
.btn-row {
    height: 3;
    align: center middle;
    padding: 0 1;
    margin-top: 1;
}
Button {
    margin: 0 1;
    background: #2d1f4e;
    color: #c084fc;
    border: solid #3b2f6b;
    min-width: 16;
}
Button:hover {
    background: #3b2f6b;
    color: #e9d5ff;
    border: solid #c084fc;
}
Button:focus {
    border: solid #a855f7;
}
Button.-primary {
    background: #7c3aed;
    color: #f3e8ff;
    border: solid #a855f7;
}
Button.-primary:hover {
    background: #9333ea;
}
Button.-danger {
    background: #4a1942;
    color: #f9a8d4;
    border: solid #be185d;
}
Button.-danger:hover {
    background: #6d1f52;
}
Button.-warning {
    background: #3d2a00;
    color: #fcd34d;
    border: solid #b45309;
}
Button.-warning:hover {
    background: #5c3e00;
}

/* ── Stats bar ── */
#stats-row {
    height: 3;
    padding: 0 2;
    align: center middle;
}
.stat-chip {
    background: #1e1a2e;
    border: solid #2d1f4e;
    color: #a78bfa;
    padding: 0 2;
    margin: 0 1;
    width: auto;
}
.stat-value {
    color: #e9d5ff;
    text-style: bold;
}

/* ── Genre table ── */
#table-panel {
    height: 1fr;
    overflow: auto;
}
DataTable {
    background: #13131a;
    color: #d1c4f0;
    height: 1fr;
}
DataTable > .datatable--header {
    background: #1e1a2e;
    color: #c084fc;
    text-style: bold;
}
DataTable > .datatable--cursor {
    background: #3b2f6b;
    color: #f3e8ff;
}
DataTable > .datatable--hover {
    background: #201a35;
}

/* ── Log panel ── */
#log-panel {
    height: 14;
    overflow: auto;
}
Log {
    background: #0c0c14;
    color: #8b7cb8;
    height: 1fr;
    scrollbar-color: #3b2f6b;
}

/* ── Progress ── */
#progress-row {
    height: 3;
    padding: 0 2;
    align: center middle;
}
ProgressBar {
    width: 1fr;
}
ProgressBar > .bar--bar {
    color: #a855f7;
}
ProgressBar > .bar--complete {
    color: #22c55e;
}
#progress-label {
    color: #6b6b8a;
    width: auto;
    margin-left: 2;
}

/* ── Confirm modal ── */
ConfirmScreen {
    align: center middle;
}
#confirm-box {
    background: #1a1a26;
    border: solid #7c3aed;
    padding: 2 4;
    width: 60;
    height: auto;
}
#confirm-title {
    color: #c084fc;
    text-style: bold;
    text-align: center;
    margin-bottom: 1;
}
#confirm-msg {
    color: #d1c4f0;
    text-align: center;
    margin-bottom: 2;
}

/* ── Duplicate modal ── */
DuplicateScreen {
    align: center middle;
}
#dup-box {
    background: #1a1a26;
    border: solid #b45309;
    padding: 2 3;
    width: 80;
    height: auto;
    max-height: 40;
}
#dup-title {
    color: #fcd34d;
    text-style: bold;
    text-align: center;
    margin-bottom: 1;
}
#dup-subtitle {
    color: #a78bfa;
    text-align: center;
    margin-bottom: 1;
}
#dup-scroll {
    height: 20;
    border: solid #2d1f4e;
    background: #0e0e12;
    margin-bottom: 1;
}
.dup-group-header {
    color: #fcd34d;
    text-style: bold;
    padding: 0 1;
    margin-top: 1;
    background: #1e1a2e;
}
.dup-file-row {
    padding: 0 2;
    color: #d1c4f0;
}
.dup-keep {
    color: #22c55e;
    text-style: bold;
}
.dup-delete {
    color: #f87171;
}
#dup-btn-row {
    height: 3;
    align: center middle;
    margin-top: 1;
}
"""


# ── helpers ──────────────────────────────────────────────────────────────────

def get_genre(filepath: Path) -> str:
    if MutagenFile is None:
        return UNKNOWN_GENRE
    try:
        audio = MutagenFile(filepath, easy=True)
        if audio is None:
            return UNKNOWN_GENRE
        for key in ("genre", "GENRE", "TCON"):
            val = audio.get(key)
            if val:
                v = val[0] if isinstance(val, list) else str(val)
                v = v.strip()
                if v:
                    return v
    except Exception:
        pass
    return UNKNOWN_GENRE


def sanitize(name: str) -> str:
    for ch in r'\/:*?"<>|':
        name = name.replace(ch, "_")
    return name.strip() or UNKNOWN_GENRE


def collect_files(music_dir: Path):
    return [
        p for p in music_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in AUDIO_EXTENSIONS
        and TRASH_FOLDER not in p.parts
    ]


def scan_genres(files: list[Path]) -> dict[str, list[Path]]:
    result: dict[str, list[Path]] = defaultdict(list)
    for f in files:
        genre = sanitize(get_genre(f))
        result[genre].append(f)
    return dict(result)


def file_size_fmt(path: Path) -> str:
    try:
        b = path.stat().st_size
        for unit in ("B", "KB", "MB", "GB"):
            if b < 1024:
                return f"{b:.1f} {unit}"
            b /= 1024
        return f"{b:.1f} TB"
    except Exception:
        return "?"


def get_track_name(filepath: Path) -> str:
    """
    Read the 'title' tag from audio metadata.
    Falls back to the filename stem (lowercased, stripped) if no tag is found.
    """
    if MutagenFile is not None:
        try:
            audio = MutagenFile(filepath, easy=True)
            if audio is not None:
                for key in ("title", "TITLE", "TIT2"):
                    val = audio.get(key)
                    if val:
                        v = val[0] if isinstance(val, list) else str(val)
                        v = v.strip()
                        if v:
                            return v.lower()
        except Exception:
            pass
    # fallback: filename without extension
    return filepath.stem.strip().lower()


def find_duplicates_by_track_name(
    files: list[Path],
    progress_cb=None,
) -> list[list[Path]]:
    """
    Group files that share the same track name (from metadata tags,
    falling back to filename stem).  Only groups with 2+ files are returned.
    progress_cb(current, total) is called after each file is processed.
    """
    name_map: dict[str, list[Path]] = defaultdict(list)
    total = len(files)
    for i, f in enumerate(files, 1):
        key = get_track_name(f)
        name_map[key].append(f)
        if progress_cb:
            progress_cb(i, total)
    return [group for group in name_map.values() if len(group) > 1]


def pick_keeper(group: list[Path]) -> Path:
    """
    Heuristic: prefer lossless formats, then highest file size.
    """
    LOSSLESS = {".flac", ".wav", ".aiff", ".ape", ".wv"}
    lossless = [f for f in group if f.suffix.lower() in LOSSLESS]
    candidates = lossless if lossless else group
    return max(candidates, key=lambda f: f.stat().st_size if f.exists() else 0)


# ── Confirm modal ─────────────────────────────────────────────────────────────

class ConfirmScreen(ModalScreen[bool]):
    BINDINGS = [
        Binding("y", "yes", "Yes"),
        Binding("n", "no", "No"),
        Binding("escape", "no", "Cancel"),
    ]

    def __init__(self, title: str, message: str):
        super().__init__()
        self._title = title
        self._message = message

    def compose(self) -> ComposeResult:
        with Container(id="confirm-box"):
            yield Label(self._title, id="confirm-title")
            yield Label(self._message, id="confirm-msg")
            with Horizontal(classes="btn-row"):
                yield Button("Yes  [Y]", id="btn-yes", variant="success")
                yield Button("No  [N]", id="btn-no", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "btn-yes")

    def action_yes(self) -> None:
        self.dismiss(True)

    def action_no(self) -> None:
        self.dismiss(False)


# ── Duplicate review modal ────────────────────────────────────────────────────

class DuplicateScreen(ModalScreen[list[Path]]):
    """
    Shows all duplicate groups.  For each group the suggested keeper is
    highlighted in green; everything else is marked for deletion.
    The user can press [A] to accept all suggestions, or [C] to cancel.
    Returns a list of paths the user approved for deletion.
    """
    BINDINGS = [
        Binding("a", "accept", "Accept all"),
        Binding("c", "cancel_dup", "Cancel"),
        Binding("escape", "cancel_dup", "Cancel"),
    ]

    def __init__(self, groups: list[list[Path]]):
        super().__init__()
        self._groups = groups
        # pre-compute keepers
        self._keepers: list[Path] = [pick_keeper(g) for g in groups]

    def compose(self) -> ComposeResult:
        to_delete = sum(len(g) - 1 for g in self._groups)
        with Container(id="dup-box"):
            yield Label("🗑  Duplicate Files Found", id="dup-title")
            yield Label(
                f"{len(self._groups)} group(s) · {to_delete} file(s) suggested for deletion",
                id="dup-subtitle",
            )
            with ScrollableContainer(id="dup-scroll"):
                for g_idx, (group, keeper) in enumerate(
                    zip(self._groups, self._keepers), 1
                ):
                    yield Label(
                        f"  Group {g_idx}", classes="dup-group-header"
                    )
                    for f in group:
                        size = file_size_fmt(f)
                        fmt  = f.suffix.upper().lstrip(".")
                        if f == keeper:
                            yield Label(
                                f"  ✔ KEEP   [{fmt}] {size:>8}  {f.name}",
                                classes="dup-file-row dup-keep",
                            )
                        else:
                            yield Label(
                                f"  ✖ DELETE [{fmt}] {size:>8}  {f.name}",
                                classes="dup-file-row dup-delete",
                            )

            with Horizontal(id="dup-btn-row"):
                yield Button("✔  Accept all  [A]", id="btn-dup-accept", classes="-warning")
                yield Button("✕  Cancel  [C]",     id="btn-dup-cancel", classes="-danger")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-dup-accept":
            self.action_accept()
        else:
            self.action_cancel_dup()

    def action_accept(self) -> None:
        to_delete: list[Path] = []
        for group, keeper in zip(self._groups, self._keepers):
            for f in group:
                if f != keeper:
                    to_delete.append(f)
        self.dismiss(to_delete)

    def action_cancel_dup(self) -> None:
        self.dismiss([])


# ── Main App ──────────────────────────────────────────────────────────────────

class MusiOrg(App):
    TITLE = "musiorg"
    CSS = APP_CSS
    BINDINGS = [
        Binding("s", "scan",     "Scan",       show=True),
        Binding("o", "organize", "Organize",   show=True),
        Binding("d", "dupes",    "Duplicates", show=True),
        Binding("r", "reset",    "Reset",      show=True),
        Binding("q", "quit",     "Quit",       show=True),
    ]

    # reactive state
    scanned:        reactive[list[Path]] = reactive([], recompose=False)
    genre_map:      reactive[dict]       = reactive({}, recompose=False)
    scanning:       reactive[bool]       = reactive(False)
    organizing:     reactive[bool]       = reactive(False)
    finding_dupes:  reactive[bool]       = reactive(False)
    progress:       reactive[float]      = reactive(0.0)
    progress_label: reactive[str]        = reactive("")

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        # ── path row ──
        with Horizontal(id="path-row"):
            yield Label("Directory:", id="path-label")
            yield Input(
                value=str(Path.home() / "Music"),
                placeholder="/path/to/music",
                id="path-input",
            )

        # ── action buttons ──
        with Horizontal(classes="btn-row"):
            yield Button("⟳  Scan",       id="btn-scan",     classes="-primary")
            yield Button("⏎  Organize",   id="btn-organize")
            yield Button("⊕  Duplicates", id="btn-dupes",    classes="-warning")
            yield Button("✕  Reset",      id="btn-reset",    classes="-danger")

        # ── stats ──
        with Horizontal(id="stats-row"):
            yield Static("Files: [bold]0[/]",   id="stat-files",   classes="stat-chip")
            yield Static("Genres: [bold]0[/]",  id="stat-genres",  classes="stat-chip")
            yield Static("Unknown: [bold]0[/]", id="stat-unknown", classes="stat-chip")

        # ── genre table ──
        with Container(id="table-panel", classes="panel"):
            yield Label("Genre Breakdown", classes="panel-title")
            table = DataTable(id="genre-table", zebra_stripes=True)
            table.add_columns("Genre", "Files", "Sample")
            yield table

        # ── progress ──
        with Horizontal(id="progress-row"):
            yield ProgressBar(total=100, show_eta=False, id="progress-bar")
            yield Label("", id="progress-label")

        # ── log ──
        with Container(id="log-panel", classes="panel"):
            yield Label("Log", classes="panel-title")
            yield Log(id="log", max_lines=200)

        yield Footer()

    # ── UI helpers ────────────────────────────────────────────────────────────

    def log_msg(self, msg: str, style: str = "") -> None:
        log = self.query_one("#log", Log)
        if style:
            log.write_line(f"[{style}]{msg}[/{style}]")
        else:
            log.write_line(msg)

    def set_progress(self, value: float, label: str = "") -> None:
        bar = self.query_one("#progress-bar", ProgressBar)
        lbl = self.query_one("#progress-label", Label)
        bar.progress = value
        lbl.update(label)

    def update_stats(self) -> None:
        total   = sum(len(v) for v in self.genre_map.values())
        genres  = len(self.genre_map)
        unknown = len(self.genre_map.get(UNKNOWN_GENRE, []))
        self.query_one("#stat-files",   Static).update(f"Files: [bold]{total}[/]")
        self.query_one("#stat-genres",  Static).update(f"Genres: [bold]{genres}[/]")
        self.query_one("#stat-unknown", Static).update(f"Unknown: [bold]{unknown}[/]")

    def populate_table(self) -> None:
        table = self.query_one("#genre-table", DataTable)
        table.clear()
        for genre, files in sorted(self.genre_map.items(), key=lambda x: -len(x[1])):
            sample = files[0].name if files else ""
            if len(sample) > 42:
                sample = sample[:39] + "…"
            table.add_row(genre, str(len(files)), sample)

    def get_music_dir(self) -> Path | None:
        raw = self.query_one("#path-input", Input).value.strip()
        p = Path(raw).expanduser()
        if not p.exists():
            self.log_msg(f"Directory not found: {p}", "red")
            return None
        return p

    def _busy(self) -> bool:
        return self.scanning or self.organizing or self.finding_dupes

    # ── actions ───────────────────────────────────────────────────────────────

    def action_scan(self)     -> None: self.on_button_pressed_scan()
    def action_organize(self) -> None: self.on_button_pressed_organize()
    def action_dupes(self)    -> None: self.on_button_pressed_dupes()
    def action_reset(self)    -> None: self._do_reset()

    def _do_reset(self) -> None:
        self.genre_map = {}
        self.scanned   = []
        self.query_one("#genre-table", DataTable).clear()
        self.update_stats()
        self.set_progress(0, "")
        self.query_one("#log", Log).clear()
        self.log_msg("Reset.", "dim")

    # ── button handler ────────────────────────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        dispatch = {
            "btn-scan":     self.on_button_pressed_scan,
            "btn-organize": self.on_button_pressed_organize,
            "btn-dupes":    self.on_button_pressed_dupes,
            "btn-reset":    self._do_reset,
        }
        fn = dispatch.get(event.button.id)
        if fn:
            fn()

    def on_button_pressed_scan(self) -> None:
        if self._busy():
            return
        music_dir = self.get_music_dir()
        if music_dir:
            self._run_scan(music_dir)

    def on_button_pressed_organize(self) -> None:
        if self._busy():
            return
        if not self.genre_map:
            self.log_msg("Scan a directory first.", "yellow")
            return
        total = sum(len(v) for v in self.genre_map.values())

        def handle_confirm(confirmed: bool) -> None:
            if confirmed:
                music_dir = self.get_music_dir()
                if music_dir:
                    self._run_organize(music_dir)

        self.push_screen(
            ConfirmScreen("Confirm", f"Move {total} files into genre folders?"),
            callback=handle_confirm,
        )

    def on_button_pressed_dupes(self) -> None:
        if self._busy():
            return
        if not self.scanned:
            self.log_msg("Scan a directory first.", "yellow")
            return
        music_dir = self.get_music_dir()
        if music_dir is None:
            return
        self.log_msg("Detecting duplicates by track name…", "cyan")
        self._run_find_dupes(list(self.scanned), music_dir)

    # ── workers ───────────────────────────────────────────────────────────────

    @work(thread=True)
    def _run_scan(self, music_dir: Path) -> None:
        self.scanning = True
        self.call_from_thread(self.log_msg, f"Scanning [bold]{music_dir}[/] …", "cyan")
        self.call_from_thread(self.set_progress, 0, "Collecting files…")

        files = collect_files(music_dir)
        if not files:
            self.call_from_thread(self.log_msg, "No audio files found.", "yellow")
            self.scanning = False
            return

        self.call_from_thread(
            self.log_msg, f"Found {len(files)} audio file(s). Reading tags…", "dim"
        )

        genre_map: dict[str, list[Path]] = defaultdict(list)
        total = len(files)
        for i, f in enumerate(files, 1):
            genre = sanitize(get_genre(f))
            genre_map[genre].append(f)
            if i % max(1, total // 40) == 0 or i == total:
                pct = (i / total) * 100
                self.call_from_thread(self.set_progress, pct, f"{i}/{total}")

        self.genre_map = dict(genre_map)
        self.scanned   = files

        self.call_from_thread(self.populate_table)
        self.call_from_thread(self.update_stats)
        self.call_from_thread(
            self.log_msg,
            f"Scan complete — {len(files)} files across {len(genre_map)} genre(s).",
            "green",
        )
        self.call_from_thread(self.set_progress, 100, "Done")
        self.scanning = False

    @work(thread=True)
    def _run_organize(self, music_dir: Path) -> None:
        self.organizing = True
        files_list = [(genre, f) for genre, files in self.genre_map.items() for f in files]
        total = len(files_list)
        moved = skipped = errors = 0

        self.call_from_thread(self.log_msg, f"Organizing {total} file(s)…", "cyan")
        self.call_from_thread(self.set_progress, 0, "Working…")

        for i, (genre, filepath) in enumerate(files_list, 1):
            dest_dir  = music_dir / genre
            dest_file = dest_dir / filepath.name

            if filepath.parent == dest_dir:
                skipped += 1
            else:
                counter = 1
                while dest_file.exists():
                    dest_file = dest_dir / f"{filepath.stem} ({counter}){filepath.suffix}"
                    counter += 1
                try:
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(filepath), str(dest_file))
                    self.call_from_thread(
                        self.log_msg,
                        f"  [dim]{filepath.name}[/] → [bold]{genre}/[/]",
                    )
                    moved += 1
                except Exception as e:
                    self.call_from_thread(self.log_msg, f"  ERROR: {e}", "red")
                    errors += 1

            pct = (i / total) * 100
            self.call_from_thread(self.set_progress, pct, f"{i}/{total}")

        self.call_from_thread(
            self.log_msg,
            f"Done — moved: [green]{moved}[/]  skipped: [dim]{skipped}[/]  errors: [red]{errors}[/]",
        )
        self.call_from_thread(self._run_scan, music_dir)
        self.organizing = False

    @work(thread=True)
    def _run_find_dupes(self, files: list[Path], music_dir: Path) -> None:
        self.finding_dupes = True
        self.call_from_thread(self.set_progress, 0, "Detecting duplicates…")

        def progress_cb(current: int, total: int) -> None:
            pct = (current / total) * 100
            self.call_from_thread(self.set_progress, pct, f"{current}/{total}")

        groups = find_duplicates_by_track_name(files, progress_cb=progress_cb)

        self.call_from_thread(self.set_progress, 100, "Done")

        if not groups:
            self.call_from_thread(
                self.log_msg, "No duplicates found. Your library looks clean! ✔", "green"
            )
            self.finding_dupes = False
            return

        dup_count = sum(len(g) - 1 for g in groups)
        self.call_from_thread(
            self.log_msg,
            f"Found {len(groups)} duplicate group(s) ({dup_count} redundant file(s)).",
            "yellow",
        )

        # Show the review modal from the main thread
        self.call_from_thread(self._show_dup_screen, groups, music_dir)
        self.finding_dupes = False

    def _show_dup_screen(self, groups: list[list[Path]], music_dir: Path) -> None:
        def handle_result(to_delete: list[Path]) -> None:
            if not to_delete:
                self.log_msg("Duplicate deletion cancelled.", "dim")
                return
            self._run_delete_dupes(to_delete, music_dir)

        self.push_screen(DuplicateScreen(groups), callback=handle_result)

    @work(thread=True)
    def _run_delete_dupes(self, to_delete: list[Path], music_dir: Path) -> None:
        """Move approved duplicates to the trash folder instead of hard-deleting."""
        trash_dir = music_dir / TRASH_FOLDER
        trash_dir.mkdir(parents=True, exist_ok=True)
        deleted = errors = 0

        self.call_from_thread(
            self.log_msg, f"Moving {len(to_delete)} duplicate(s) to trash…", "cyan"
        )

        for i, filepath in enumerate(to_delete, 1):
            dest = trash_dir / filepath.name
            counter = 1
            while dest.exists():
                dest = trash_dir / f"{filepath.stem} ({counter}){filepath.suffix}"
                counter += 1
            try:
                shutil.move(str(filepath), str(dest))
                self.call_from_thread(
                    self.log_msg,
                    f"  [dim]{filepath.name}[/] → [bold]{TRASH_FOLDER}/[/]",
                )
                deleted += 1
            except Exception as e:
                self.call_from_thread(self.log_msg, f"  ERROR: {e}", "red")
                errors += 1

            pct = (i / len(to_delete)) * 100
            self.call_from_thread(self.set_progress, pct, f"{i}/{len(to_delete)}")

        self.call_from_thread(
            self.log_msg,
            f"Trash done — moved: [green]{deleted}[/]  errors: [red]{errors}[/]  "
            f"(files are in [bold]{TRASH_FOLDER}/[/], delete manually to free space)",
            "green",
        )
        # Refresh the scan so stats are up to date
        self.call_from_thread(self._run_scan, music_dir)


# ── entry ─────────────────────────────────────────────────────────────────────

def main():
    app = MusiOrg()
    app.run()


if __name__ == "__main__":
    main()
