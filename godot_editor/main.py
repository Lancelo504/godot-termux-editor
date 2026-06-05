"""Godot Editor for Termux — main entry point."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

import godot_editor.storage as storage
import godot_editor.ui as ui
from godot_editor.editor import open_editor
from godot_editor.fileutils import detect_language


# ── helpers ───────────────────────────────────────────────────────────────────

def _reload_files(project_id: str) -> list[dict]:
    return storage.list_files(project_id)


# ── project loop ──────────────────────────────────────────────────────────────

def run_project(project: dict, config: dict) -> None:
    project_id = project["id"]

    while True:
        files = _reload_files(project_id)
        choice = ui.show_files(project, files)

        if choice is None:
            return

        action = choice.get("_action")

        # ── open editor ──────────────────────────────────────────────
        if action == "edit":
            f = choice["_file"]
            content = storage.read_file(project_id, f["name"])
            language = f.get("language") or detect_language(f["name"])

            def on_save(text: str) -> None:
                storage.write_file(project_id, f["name"], text)
                ui.console.print(f"[success]  Saved {f['name']}[/success]")

            final = open_editor(
                filename=f["name"],
                content=content,
                language=language,
                on_save=on_save,
                tab_size=config.get("tab_size", 2),
                line_numbers=config.get("line_numbers", True),
                autocomplete=config.get("autocomplete", True),
            )
            # Auto-save on exit if there were unsaved changes
            if final is not None and final != content:
                if ui.confirm("Save changes before closing?", default=True):
                    storage.write_file(project_id, f["name"], final)

        # ── view (read-only syntax highlight) ────────────────────────
        elif action == "view":
            f = choice["_file"]
            content  = storage.read_file(project_id, f["name"])
            language = f.get("language") or detect_language(f["name"])
            ui.view_file(f["name"], content, language)

        # ── new file ─────────────────────────────────────────────────
        elif action == "new_file":
            result = ui.new_file_wizard()
            if result:
                fname, starter = result
                # Check for duplicate
                existing = [f["name"] for f in files]
                if fname in existing:
                    ui.console.print(f"[error]  File '{fname}' already exists.[/error]")
                    ui.console.print("[muted]  Press Enter to continue...[/muted]")
                    input()
                    continue
                meta = storage.create_file(project_id, fname, starter)
                # Open editor immediately
                language = detect_language(fname)

                def on_save_new(text: str, _fname=fname) -> None:
                    storage.write_file(project_id, _fname, text)

                final = open_editor(
                    filename=fname,
                    content=starter,
                    language=language,
                    on_save=on_save_new,
                    tab_size=config.get("tab_size", 2),
                    line_numbers=config.get("line_numbers", True),
                    autocomplete=config.get("autocomplete", True),
                )
                if final is not None and final != starter:
                    storage.write_file(project_id, fname, final)

        # ── delete file ───────────────────────────────────────────────
        elif action == "delete":
            f = choice["_file"]
            if ui.confirm(f"Delete '{f['name']}'? This cannot be undone.", default=False):
                storage.delete_file(project_id, f["name"])
                ui.console.print(f"[success]  Deleted {f['name']}[/success]")

        # ── rename file ───────────────────────────────────────────────
        elif action == "rename":
            f = choice["_file"]
            new_name = ui.ask(f"New name for '{f['name']}'", default=f["name"])
            if new_name and new_name != f["name"]:
                storage.rename_file(project_id, f["name"], new_name)
                ui.console.print(f"[success]  Renamed to {new_name}[/success]")


# ── main loop ─────────────────────────────────────────────────────────────────

def run_main_loop() -> None:
    storage.init()
    config = storage.load_config()

    while True:
        projects = storage.list_projects()
        choice   = ui.show_projects(projects)

        if choice is None:
            sys.exit(0)

        if choice.get("_action") == "new":
            result = ui.new_project_wizard()
            if result:
                name, desc = result
                proj = storage.create_project(name, desc)
                run_project(proj, config)
            continue

        # Open project
        if "_action" not in choice:
            project = storage.get_project(choice["id"]) or choice
            run_project(project, config)
            continue

        # Settings / About reached from project view — re-read config
        config = storage.load_config()


# ── direct-open CLI ───────────────────────────────────────────────────────────

def open_direct(filepath: Path, config: dict) -> None:
    """Open any file directly from the filesystem (no project needed)."""
    if not filepath.exists():
        # Create new file
        if not ui.confirm(f"'{filepath.name}' does not exist. Create it?", default=True):
            sys.exit(0)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text("")

    content  = filepath.read_text(encoding="utf-8", errors="replace")
    language = detect_language(filepath.name)

    def on_save(text: str) -> None:
        filepath.write_text(text, encoding="utf-8")

    final = open_editor(
        filename=str(filepath),
        content=content,
        language=language,
        on_save=on_save,
        tab_size=config.get("tab_size", 2),
        line_numbers=config.get("line_numbers", True),
        autocomplete=config.get("autocomplete", True),
    )
    if final is not None and final != content:
        if ui.confirm("Save changes?", default=True):
            filepath.write_text(final, encoding="utf-8")


# ── settings CLI ──────────────────────────────────────────────────────────────

def run_settings() -> None:
    storage.init()
    config = storage.load_config()
    new_config = ui.show_settings(config)
    if new_config != config:
        storage.save_config(new_config)
        ui.console.print("[success]  Settings saved.[/success]")


# ── entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="godot-editor",
        description="Godot Engine code editor for Termux",
    )
    parser.add_argument(
        "file",
        nargs="?",
        metavar="FILE",
        help="Open a file directly (skips project browser)",
    )
    parser.add_argument(
        "--settings",
        action="store_true",
        help="Open settings",
    )
    parser.add_argument(
        "--about",
        action="store_true",
        help="Show about info",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="godot-editor 1.0.0",
    )
    args = parser.parse_args()

    storage.init()
    config = storage.load_config()

    if args.about:
        ui.show_about()
        return

    if args.settings:
        run_settings()
        return

    if args.file:
        open_direct(Path(args.file), config)
        return

    try:
        run_main_loop()
    except (KeyboardInterrupt, EOFError):
        ui.console.print("\n[muted]  Goodbye.[/muted]")
        sys.exit(0)
