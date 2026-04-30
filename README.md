# musiorg 🎵

A terminal UI music organizer. Scans your music directory, reads genre tags from audio file metadata, and sorts everything into per-genre subfolders — all inside a clean, keyboard-driven TUI.

```
┌─────────────────────────────────────────────────────────────────┐
│  musiorg                                          12:34:56       │
├─────────────────────────────────────────────────────────────────┤
│  Directory: /home/user/Music                                     │
│  [ ⟳ Scan ]  [ ⏎ Organize ]  [ ⊕ Duplicates ]  [ ✕ Reset ]    │
│  Files: 312    Genres: 14    Unknown: 8                          │
│                                                                  │
│  Genre          │ Files │ Sample                                 │
│  ───────────────┼───────┼──────────────────────────────         │
│  Hip-Hop        │  87   │ some_track.mp3                         │
│  Jazz           │  64   │ kind_of_blue.flac                      │
│  Electronic     │  51   │ aphex_twin.ogg                         │
│  ...                                                             │
│                                                                  │
│  ████████████████████████░░░░  82/100                           │
│  Log                                                             │
│  Scanning /home/user/Music …                                     │
│  Found 312 audio files. Reading tags…                           │
│  Scan complete — 312 files across 14 genre(s).                  │
└─────────────────────────────────────────────────────────────────┘
  [S] Scan   [O] Organize   [D] Duplicates   [R] Reset   [Q] Quit
```

## Features

- Reads genre tags from **MP3, FLAC, OGG, OPUS, M4A, AAC, WAV, WMA, AIFF, APE** and more
- Live progress bar and log while scanning / moving
- Collision-safe file moving (appends a counter when a filename already exists)
- Re-run safe — skips files already in the right folder
- Confirm dialog before moving anything
- Files with no genre tag go into `Unknown/`
- **Duplicate detection** — finds duplicate tracks by title tag (falls back to filename stem), catches the same song across different formats with no extra dependencies
- Fully keyboard-driven

## Requirements

- Python 3.11+
- [`textual`](https://github.com/Textualize/textual) ≥ 0.80
- [`mutagen`](https://github.com/quodlibet/mutagen) ≥ 1.47

## Installation

### From source (recommended)

```bash
git clone https://codeberg.org/noobman/musiorg
cd musiorg
pip install .
```

### Directly with pip (editable)

```bash
pip install -e .
```

### No install — just run

```bash
pip install textual mutagen
python musiorg.py
```

## Usage

```bash
musiorg
```

| Key | Action |
|-----|--------|
| `S` | Scan directory |
| `O` | Organize files |
| `D` | Detect duplicates |
| `R` | Reset / clear |
| `Q` | Quit |
| `Y` / `N` | Confirm dialog |
| `A` | Accept all (duplicate screen) |
| `C` | Cancel (duplicate screen) |

1. Set the path to your music directory in the input field.
2. Press **S** (or click *Scan*) — musiorg reads all audio tags and shows a breakdown.
3. Review the genre table.
4. Press **O** (or click *Organize*) — confirm the dialog and watch the files move.
5. *(Optional)* Press **D** (or click *Duplicates*) — musiorg fingerprints your library and shows groups of duplicates. Review the suggestions and press **A** to accept.

## Duplicate detection

When you press **D**, musiorg:

1. Reads the `title` tag from every scanned file's metadata (falls back to the filename stem if no tag is set)
2. Groups files that share the same title — catching the same song across MP3, FLAC, OGG, etc.
3. Opens a review screen showing each group — the suggested file to keep is highlighted in green (prefers lossless formats, then largest file size)
4. If you press **A** to accept, the redundant files are moved to `.musiorg_trash/` inside your music directory — **nothing is permanently deleted**
5. You can review and empty the trash folder manually when you're satisfied

## Result structure

```
~/Music/
├── Jazz/
│   ├── kind_of_blue.flac
│   └── a_love_supreme.mp3
├── Hip-Hop/
│   └── illmatic.mp3
├── Electronic/
│   └── selected_ambient_works.ogg
├── Unknown/
│   └── untagged_file.mp3
└── .musiorg_trash/        ← duplicates land here, not permanently deleted
    └── kind_of_blue.mp3
```

## License

MIT
