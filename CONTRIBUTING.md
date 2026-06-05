# Contributing to Godot Editor for Termux

Thank you for your interest in contributing!

## Development setup

```bash
git clone https://github.com/Lancelot504/godot-termux-editor
cd godot-termux-editor

# Create a virtual environment (optional but recommended)
python -m venv .venv
source .venv/bin/activate          # Linux / macOS / Termux
# .venv\Scripts\activate           # Windows

# Install in editable mode with all dependencies
pip install -e .

# Run the editor
godot-editor
# or
python run.py
```

## Project structure

```
godot_editor/
├── main.py          Entry point, CLI argument parsing, main loop
├── ui.py            Rich-based menus, file browser, project browser
├── editor.py        Full-screen prompt_toolkit editor + key bindings
├── autocomplete.py  Godot API completer (1,503 classes)
├── storage.py       Projects / files persistence (~/.config/godot-editor/)
├── fileutils.py     Language detection, starter templates
└── data/
    └── godot_api_compact.json   Pre-processed Godot 4 API
```

## Adding a new language

1. Add the file extension(s) to `EXTENSION_MAP` in `fileutils.py`
2. Add a label in `LANGUAGE_LABELS`
3. Add a color in `LANGUAGE_COLORS`
4. Add a starter template in `FILE_STARTER_CONTENT`
5. Map to a pygments lexer in `get_pygments_lexer_name()`

## Updating the Godot API data

The `godot_editor/data/godot_api_compact.json` is generated from
the full Godot API JSON using:

```bash
node -e "
const fs = require('fs');
const data = JSON.parse(fs.readFileSync('godot_api_full.json', 'utf8'));
const compact = {};
for (const [cls, info] of Object.entries(data)) {
  compact[cls] = {
    i: info.inherits || null,
    m: (info.methods || []).map(m => m.name),
    p: (info.properties || []).map(p => p.name),
    c: Object.keys(info.constants || {})
  };
}
fs.writeFileSync('godot_editor/data/godot_api_compact.json', JSON.stringify(compact));
"
```

## Pull request guidelines

- Keep PRs focused — one feature or fix per PR
- Add or update tests if applicable
- Update `README.md` if you add a feature
- Follow the existing code style (no external linters required)

## Reporting bugs

Use the [Bug Report](.github/ISSUE_TEMPLATE/bug_report.md) issue template.

## License

By contributing, you agree your contributions will be licensed under the MIT License.
