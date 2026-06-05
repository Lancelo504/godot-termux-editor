# Godot Editor for Termux

> A full-featured code editor for **Godot Engine** in the terminal —
> built for **Termux on Android** and any Linux / macOS shell.

```
 ██████╗  ██████╗ ██████╗  ██████╗ ████████╗
██╔════╝ ██╔═══██╗██╔══██╗██╔═══██╗╚══██╔══╝
██║  ███╗██║   ██║██║  ██║██║   ██║   ██║
██║   ██║██║   ██║██║  ██║██║   ██║   ██║
╚██████╔╝╚██████╔╝██████╔╝╚██████╔╝   ██║
 ╚═════╝  ╚═════╝ ╚═════╝  ╚═════╝   ╚═╝
```

[![Python](https://img.shields.io/badge/Python-3.8%2B-3776ab?logo=python&logoColor=white)](https://python.org)
[![PyPI](https://img.shields.io/pypi/v/godot-termux-editor?color=89b4fa)](https://pypi.org/project/godot-termux-editor/)
[![CI](https://github.com/Lancelot504/godot-termux-editor/actions/workflows/test.yml/badge.svg)](https://github.com/Lancelot504/godot-termux-editor/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-a6e3a1.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Termux%20%7C%20Linux%20%7C%20macOS-fab387)](https://termux.dev)

---

## Features

| | Feature |
|---|---|
| ✏️ | Full-screen editor with syntax highlighting (prompt_toolkit + pygments) |
| 🤖 | **Godot 4 API autocomplete** — 1,503 classes, methods, properties, constants |
| 🔗 | **Inheritance-aware** — `Node2D.` resolves all members from `Node2D`, `Node`, `Object` |
| 🎨 | **Dark IDE theme** (Catppuccin Mocha palette) |
| 📁 | Project manager and file browser |
| 👁️ | Read-only syntax-highlighted file preview |
| ⌨️ | Rich keyboard shortcuts (save, find, comment, duplicate, indent) |
| 🌐 | Multi-language: GDScript · TSCN · TRES · C · C++ · C# · GLSL · JSON · Config |
| 📦 | Pure Python — no native modules — works on Termux without root |

---

## Quick start

### Termux (Android)

```bash
pkg install git python
git clone https://github.com/Lancelot504/godot-termux-editor
cd godot-termux-editor
bash install.sh
```

### Linux / macOS

```bash
pip install godot-termux-editor
```

Or from source:

```bash
git clone https://github.com/Lancelot504/godot-termux-editor
cd godot-termux-editor
bash install.sh
```

---

## Usage

```bash
godot-editor               # project browser
godot-editor player.gd     # open file directly
godot-editor --settings    # settings
godot-editor --about
godot-editor --version
```

### Project browser

```
  1  My Platformer Game
  2  Godot Tests
  N  New project
  0  Quit
```

### File browser

```
  1  player.gd         [GDScript]      2.1 KB
  2  level_01.tscn     [Godot Scene]   4.7 KB
  3  items.tres        [Godot Resource] 1.2 KB

  N  New file
  D  Delete   (D <n>)
  R  Rename   (R <n>)
  V  View     (V <n>)   ← syntax-highlighted read-only preview
  0  Back
```

### Editor

```
┌─────────────────────────────────────────────────────────────┐
│  GODOT EDITOR  ━  player.gd  [GDScript]                     │
├─────────────────────────────────────────────────────────────┤
│  1  extends CharacterBody2D                                 │
│  2                                                          │
│  3  @export var speed: float = 200.0                        │
│  4  @export var jump_force: float = 400.0                   │
│  5                                                          │
│  6  func _ready() -> void:                                  │
│  7      print("Ready!")                                     │
├─────────────────────────────────────────────────────────────┤
│  Ctrl+S save  Ctrl+Q quit  Ctrl+F find  Ctrl+/ comment     │
├─────────────────────────────────────────────────────────────┤
│  Ln 7  Col 18  |  24 lines  |  GDScript                    │
└─────────────────────────────────────────────────────────────┘
```

### Key bindings

| Shortcut | Action |
|---|---|
| `Ctrl+S` | Save file |
| `Ctrl+Q` / `Ctrl+W` | Quit editor |
| `Ctrl+F` | Find / search |
| `Ctrl+/` | Toggle line comment |
| `Ctrl+D` | Duplicate current line |
| `Tab` | Indent / accept autocomplete |
| `Shift+Tab` | Dedent |
| `Ctrl+Space` | Trigger autocomplete |
| `Escape` | Dismiss autocomplete |
| `Page Up / Down` | Scroll |

---

## Autocomplete

Ships with the full **Godot 4 API** (664 KB, pre-processed):

```
# type a prefix → class suggestions
Node2D      ← class  (← Node)
NodePath    ← class  (← RefCounted)
...

# type obj. → member suggestions
position    ← Node2D
rotation    ← Node2D
add_child   ← Node
get_child   ← Node
free        ← Object
...

# annotations
@export
@onready
@export_range
...
```

---

## Supported languages

| Extension | Language | Completions |
|---|---|---|
| `.gd` | GDScript | Full Godot API + keywords + annotations |
| `.tscn` | Godot Scene | Section headers, keys, class names |
| `.tres` | Godot Resource | Section headers, keys, class names |
| `.c` `.h` | C | Keywords, preprocessor |
| `.cpp` `.hpp` | C++ | Keywords, templates |
| `.cs` | C# | Keywords, types |
| `.gdshader` `.glsl` | Shader | GLSL keywords |
| `.json` | JSON | Keys, values |
| `.cfg` `.ini` | Config | Sections, keys |
| `.md` `.txt` | Text | — |

---

## File storage

```
~/.config/godot-editor/
├── config.json
└── projects/
    └── <id>/
        ├── project.json
        └── files/
            ├── player.gd
            └── level.tscn
```

---

## Requirements

| Package | Version |
|---|---|
| Python | ≥ 3.8 |
| `rich` | ≥ 13.0.0 |
| `prompt_toolkit` | ≥ 3.0.0 |
| `pygments` | ≥ 2.14.0 |

---

## Building from source / publishing to PyPI

```bash
pip install build twine
python -m build
twine check dist/*
twine upload dist/*
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

---

## License

[MIT](LICENSE) — free to use, modify, and distribute.
