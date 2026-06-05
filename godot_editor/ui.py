"""Rich-based menus, file browser, and display helpers."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from rich import box
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.rule import Rule
from rich.style import Style
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

# ── Themed console ────────────────────────────────────────────────────────────

THEME = Theme({
    "primary":    "bold #89dceb",
    "secondary":  "#89b4fa",
    "accent":     "#cba6f7",
    "success":    "#a6e3a1",
    "warning":    "#f9e2af",
    "error":      "#f38ba8",
    "muted":      "#585b70",
    "dim_text":   "#6c7086",
    "fg":         "#cdd6f4",
    "gdscript":   "bold #cba6f7",
    "tscn":       "bold #89dceb",
    "tres":       "bold #89b4fa",
    "c":          "bold #fab387",
    "cpp":        "bold #f38ba8",
    "csharp":     "bold #a6e3a1",
    "text":       "dim #cdd6f4",
})

console = Console(theme=THEME, highlight=False)

# ── Branding ──────────────────────────────────────────────────────────────────

LOGO = r"""
 ██████╗  ██████╗ ██████╗  ██████╗ ████████╗
██╔════╝ ██╔═══██╗██╔══██╗██╔═══██╗╚══██╔══╝
██║  ███╗██║   ██║██║  ██║██║   ██║   ██║   
██║   ██║██║   ██║██║  ██║██║   ██║   ██║   
╚██████╔╝╚██████╔╝██████╔╝╚██████╔╝   ██║   
 ╚═════╝  ╚═════╝ ╚═════╝  ╚═════╝   ╚═╝   
"""

BANNER_SMALL = "[primary]GODOT EDITOR[/primary] [muted]for Termux[/muted]"


def print_header(subtitle: str = "") -> None:
    console.print()
    console.print(Panel(
        LOGO.strip() + f"\n[muted]Code editor for Godot Engine · 1,503 API classes[/muted]"
        + (f"\n[secondary]{subtitle}[/secondary]" if subtitle else ""),
        border_style="#89dceb",
        padding=(0, 2),
    ))
    console.print()


def print_divider(title: str = "") -> None:
    if title:
        console.print(Rule(f"[primary]{title}[/primary]", style="#313244"))
    else:
        console.print(Rule(style="#313244"))


def clear() -> None:
    console.clear()


# ── Input helpers ─────────────────────────────────────────────────────────────

def ask(prompt: str, default: str = "") -> str:
    return Prompt.ask(f"[secondary]  {prompt}[/secondary]", default=default, console=console)


def confirm(prompt: str, default: bool = False) -> bool:
    return Confirm.ask(f"[warning]  {prompt}[/warning]", default=default, console=console)


def menu(title: str, options: list[tuple[str, str]], back_label: str = "Back") -> Optional[str]:
    """
    Display a numbered menu.
    options: [(key, label), ...]
    Returns the selected key or None if user chose back/quit.
    """
    console.print()
    console.print(f"[primary]  {title}[/primary]")
    console.print()

    for i, (key, label) in enumerate(options, 1):
        console.print(f"  [secondary]{i:>2}[/secondary]  {label}")

    console.print(f"  [muted] 0  {back_label}[/muted]")
    console.print()

    while True:
        raw = Prompt.ask("[dim_text]  ›[/dim_text]", default="0", console=console)
        if raw == "0" or raw.lower() in ("q", "quit", "back", "b"):
            return None
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(options):
                return options[idx][0]
        except ValueError:
            # Try matching by key directly
            for key, _ in options:
                if raw.lower() == key.lower():
                    return key
        console.print("[error]  Invalid choice, try again.[/error]")


# ── Project views ─────────────────────────────────────────────────────────────

def show_projects(projects: list[dict]) -> Optional[dict]:
    """Show project list, return selected project or None."""
    import time

    clear()
    print_header()
    print_divider("Projects")
    console.print()

    if not projects:
        console.print(Panel(
            "[dim_text]No projects yet.\nChoose [secondary]New Project[/secondary] to create one.[/dim_text]",
            border_style="#313244",
            padding=(1, 4),
        ))
        console.print()
    else:
        t = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="primary",
                  border_style="#313244", expand=True)
        t.add_column("#",       width=4,  style="muted", justify="right")
        t.add_column("Project", min_width=20, style="fg")
        t.add_column("Updated", width=20, style="dim_text")

        for i, p in enumerate(projects, 1):
            from datetime import datetime
            ts  = p.get("updated_at", 0)
            upd = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M") if ts else "—"
            t.add_row(str(i), p["name"], upd)

        console.print(t)

    options = [(str(i + 1), p["name"]) for i, p in enumerate(projects)]

    console.print("  [secondary] N[/secondary]  New project")
    console.print("  [muted] 0  Quit[/muted]")
    console.print()

    while True:
        raw = Prompt.ask("[dim_text]  ›[/dim_text]", default="0", console=console).strip().lower()
        if raw in ("0", "q", "quit"):
            sys.exit(0)
        if raw == "n":
            return {"_action": "new"}
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(projects):
                return projects[idx]
        except ValueError:
            pass
        console.print("[error]  Invalid choice.[/error]")


def show_files(project: dict, files: list[dict]) -> Optional[dict]:
    """Show file list for a project, return selected file meta or action dict."""
    from godot_editor.fileutils import get_label, get_color

    clear()
    print_header(subtitle=f"Project: {project['name']}")
    print_divider(f"Files  ({len(files)})")
    console.print()

    if not files:
        console.print(Panel(
            "[dim_text]No files yet.\nChoose [secondary]New File[/secondary] to create one.[/dim_text]",
            border_style="#313244",
            padding=(1, 4),
        ))
        console.print()
    else:
        t = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="primary",
                  border_style="#313244", expand=True)
        t.add_column("#",        width=4,  style="muted", justify="right")
        t.add_column("Filename", min_width=24)
        t.add_column("Language", width=16)
        t.add_column("Size",     width=10, style="dim_text", justify="right")

        for i, f in enumerate(files, 1):
            lang  = f.get("language", "text")
            label = get_label(lang)
            color = get_color(lang)
            size  = f.get("size", 0)
            size_str = f"{size:,} B" if size < 1024 else f"{size / 1024:.1f} KB"
            t.add_row(str(i), f["name"], f"[{color}]{label}[/{color}]", size_str)

        console.print(t)

    console.print("  [secondary] N[/secondary]  New file")
    console.print("  [secondary] D[/secondary]  Delete file  [muted](D <number>)[/muted]")
    console.print("  [secondary] R[/secondary]  Rename file  [muted](R <number>)[/muted]")
    console.print("  [secondary] V[/secondary]  View file (syntax highlight)  [muted](V <number>)[/muted]")
    console.print("  [muted] 0  Back to projects[/muted]")
    console.print()

    while True:
        raw = Prompt.ask("[dim_text]  ›[/dim_text]", default="0", console=console).strip()
        raw_lower = raw.lower()

        if raw == "0" or raw_lower in ("q", "b", "back"):
            return None

        if raw_lower == "n":
            return {"_action": "new_file"}

        # "D 3" or "d3" → delete file 3
        dm = _parse_action(raw_lower, ("d", "delete"))
        if dm is not None:
            idx = dm - 1
            if 0 <= idx < len(files):
                return {"_action": "delete", "_file": files[idx]}
            console.print("[error]  Bad file number.[/error]")
            continue

        # "R 3"  → rename file 3
        rm = _parse_action(raw_lower, ("r", "rename"))
        if rm is not None:
            idx = rm - 1
            if 0 <= idx < len(files):
                return {"_action": "rename", "_file": files[idx]}
            console.print("[error]  Bad file number.[/error]")
            continue

        # "V 3" → view (syntax highlight) file 3
        vm = _parse_action(raw_lower, ("v", "view"))
        if vm is not None:
            idx = vm - 1
            if 0 <= idx < len(files):
                return {"_action": "view", "_file": files[idx]}
            console.print("[error]  Bad file number.[/error]")
            continue

        try:
            idx = int(raw) - 1
            if 0 <= idx < len(files):
                return {"_action": "edit", "_file": files[idx]}
        except ValueError:
            pass
        console.print("[error]  Invalid choice.[/error]")


def _parse_action(raw: str, prefixes: tuple) -> Optional[int]:
    """Parse 'd3', 'd 3', 'delete 3', etc. → int."""
    import re
    for p in prefixes:
        m = re.fullmatch(rf"{re.escape(p)}\s*(\d+)", raw)
        if m:
            return int(m.group(1))
    return None


# ── File views ────────────────────────────────────────────────────────────────

def view_file(filename: str, content: str, language: str) -> None:
    """Display a file with full syntax highlighting (read-only)."""
    from godot_editor.fileutils import get_pygments_lexer_name

    clear()
    print_divider(f"  {filename}")

    lexer_name = get_pygments_lexer_name(language)
    syntax = Syntax(
        content,
        lexer_name,
        theme="monokai",
        line_numbers=True,
        background_color="#11111b",
        indent_guides=False,
        word_wrap=False,
    )
    console.print(syntax)
    print_divider()
    console.print("[muted]  Press Enter to go back...[/muted]")
    input()


# ── New-file wizard ───────────────────────────────────────────────────────────

TEMPLATE_MENU = [
    ("gdscript",  "GDScript (.gd)"),
    ("tscn",      "Godot Scene (.tscn)"),
    ("tres",      "Godot Resource (.tres)"),
    ("c",         "C (.c / .h)"),
    ("cpp",       "C++ (.cpp / .hpp)"),
    ("csharp",    "C# (.cs)"),
    ("gdshader",  "GD Shader (.gdshader)"),
    ("json",      "JSON (.json)"),
    ("cfg",       "Config (.cfg / .ini)"),
    ("text",      "Plain Text (.txt)"),
]

EXT_FOR_TEMPLATE = {
    "gdscript":  ".gd",
    "tscn":      ".tscn",
    "tres":      ".tres",
    "c":         ".c",
    "cpp":       ".cpp",
    "csharp":    ".cs",
    "gdshader":  ".gdshader",
    "json":      ".json",
    "cfg":       ".cfg",
    "text":      ".txt",
}


def new_file_wizard() -> Optional[tuple[str, str]]:
    """
    Interactive wizard for creating a new file.
    Returns (filename, starter_content) or None if cancelled.
    """
    from godot_editor.fileutils import get_starter

    console.print()
    print_divider("New File")
    console.print()

    console.print("[primary]  Choose a template:[/primary]")
    console.print()
    for i, (key, label) in enumerate(TEMPLATE_MENU, 1):
        console.print(f"  [secondary]{i:>2}[/secondary]  {label}")
    console.print("  [muted]  0  Cancel[/muted]")
    console.print()

    tmpl_key: Optional[str] = None
    while True:
        raw = Prompt.ask("[dim_text]  ›[/dim_text]", default="0", console=console).strip()
        if raw == "0":
            return None
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(TEMPLATE_MENU):
                tmpl_key = TEMPLATE_MENU[idx][0]
                break
        except ValueError:
            pass
        console.print("[error]  Invalid choice.[/error]")

    default_ext = EXT_FOR_TEMPLATE.get(tmpl_key, ".txt")
    console.print()
    name = Prompt.ask(
        f"[secondary]  File name[/secondary] [muted](default extension: {default_ext})[/muted]",
        default=f"untitled{default_ext}",
        console=console,
    ).strip()

    if not name:
        return None

    if "." not in name:
        name += default_ext

    starter = get_starter(tmpl_key)
    console.print(f"[success]  → Creating [fg]{name}[/fg][/success]")
    return name, starter


# ── New-project wizard ────────────────────────────────────────────────────────

def new_project_wizard() -> Optional[tuple[str, str]]:
    """Returns (name, description) or None."""
    console.print()
    print_divider("New Project")
    console.print()

    name = ask("Project name").strip()
    if not name:
        return None
    desc = ask("Description (optional)", default="")
    return name, desc


# ── Settings ──────────────────────────────────────────────────────────────────

def show_settings(config: dict) -> Optional[dict]:
    while True:
        clear()
        print_header()
        print_divider("Settings")
        console.print()

        t = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="primary",
                  border_style="#313244")
        t.add_column("#",       width=4,  style="muted", justify="right")
        t.add_column("Setting", min_width=20, style="fg")
        t.add_column("Value",   min_width=16, style="secondary")

        settings = [
            ("1", "Tab size",        str(config.get("tab_size",    2))),
            ("2", "Autocomplete",    "on" if config.get("autocomplete", True) else "off"),
            ("3", "Line numbers",    "on" if config.get("line_numbers", True) else "off"),
            ("4", "Word wrap",       "on" if config.get("word_wrap",    False) else "off"),
        ]
        for num, name, val in settings:
            t.add_row(num, name, val)

        console.print(t)
        console.print("  [muted] 0  Back[/muted]")
        console.print()

        raw = Prompt.ask("[dim_text]  ›[/dim_text]", default="0", console=console).strip()
        if raw == "0":
            return config

        new_cfg = dict(config)
        if raw == "1":
            v = ask("Tab size (2 or 4)", default=str(config.get("tab_size", 2)))
            new_cfg["tab_size"] = int(v) if v in ("2", "4") else config.get("tab_size", 2)
        elif raw == "2":
            new_cfg["autocomplete"] = not config.get("autocomplete", True)
        elif raw == "3":
            new_cfg["line_numbers"] = not config.get("line_numbers", True)
        elif raw == "4":
            new_cfg["word_wrap"] = not config.get("word_wrap", False)
        else:
            continue

        console.print("[success]  Setting updated.[/success]")
        config = new_cfg
        return config


# ── About ─────────────────────────────────────────────────────────────────────

def show_about() -> None:
    clear()
    print_header()

    grid = Table.grid(expand=True, padding=(0, 2))
    grid.add_column(justify="left",  min_width=20)
    grid.add_column(justify="left",  min_width=30)

    grid.add_row("[primary]Version[/primary]",       "[fg]1.0.0[/fg]")
    grid.add_row("[primary]Platform[/primary]",       "[fg]Termux / Python 3.8+[/fg]")
    grid.add_row("[primary]Godot API[/primary]",      "[fg]v4  ·  1,503 classes[/fg]")
    grid.add_row("[primary]Languages[/primary]",      "[fg]GDScript, TSCN, TRES, C, C++, C#, GLSL[/fg]")
    grid.add_row("[primary]Editor[/primary]",         "[fg]prompt_toolkit + pygments[/fg]")
    grid.add_row("[primary]Display[/primary]",        "[fg]rich[/fg]")
    grid.add_row("[primary]Storage[/primary]",        "[fg]~/.config/godot-editor/[/fg]")

    console.print(Panel(grid, title="[primary]About Godot Editor[/primary]",
                        border_style="#89dceb", padding=(1, 3)))
    console.print()
    console.print("[muted]  Press Enter to go back...[/muted]")
    input()
