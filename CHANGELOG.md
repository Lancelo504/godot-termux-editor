# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2025-06-05

### Added
- Full-screen code editor using `prompt_toolkit` with dark IDE theme (Catppuccin Mocha)
- Syntax highlighting for GDScript, `.tscn`, `.tres`, C, C++, C#, GLSL, GD Shader, JSON, Config
- Godot 4 API autocomplete — 1,503 classes with full inheritance-chain resolution
- Project manager — create, list, delete projects stored in `~/.config/godot-editor/`
- File browser — create, rename, delete, and preview files
- Read-only syntax-highlighted view mode (`V <n>`)
- Key bindings: `Ctrl+S`, `Ctrl+Q`, `Ctrl+F`, `Ctrl+/`, `Ctrl+D`, `Tab`, `Shift+Tab`
- Open any file from the filesystem directly (`godot-editor path/to/file.gd`)
- Settings — tab size, autocomplete, line numbers, word wrap
- `install.sh` for Termux and Linux/macOS
- `pyproject.toml` — pip-installable package (`godot-termux-editor`)
- GitHub Actions CI — tests on Python 3.8–3.12
- GitHub Actions release — automatic PyPI publish on git tag
