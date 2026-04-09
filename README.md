# musiorg 🎵

A terminal UI music organizer. Scans your music directory, reads genre tags from audio file metadata, and sorts everything into per-genre subfolders — all inside a clean, keyboard-driven TUI.

```
┌─────────────────────────────────────────────────────────────────┐
│  musiorg                                          12:34:56       │
├─────────────────────────────────────────────────────────────────┤
│  Directory: /home/user/Music                                     │
│  [ ⟳ Scan ]   [ ⏎ Organize ]   [ ✕ Reset ]                     │
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
  [S] Scan   [O] Organize   [R] Reset   [Q] Quit
```

## Features

- Reads genre tags from **MP3, FLAC, OGG, OPUS, M4A, AAC, WAV, WMA, AIFF, APE** and more
- Live progress bar and log while scanning / moving
- Collision-safe file moving (appends a counter when a filename already exists)
- Re-run safe — skips files already in the right folder
- Confirm dialog before moving anything
- Files with no genre tag go into `Unknown/`
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

| Key | Action           |
|-----|------------------|
| `S` | Scan directory   |
| `O` | Organize files   |
| `R` | Reset / clear    |
| `Q` | Quit             |
| `Y` / `N` | Confirm dialog |

1. Set the path to your music directory in the input field.
2. Press **S** (or click *Scan*) — musiorg reads all audio tags and shows a breakdown.
3. Review the genre table.
4. Press **O** (or click *Organize*) — confirm the dialog and watch the files move.

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
└── Unknown/
    └── untagged_file.mp3
```

## License

MIT
