"""Full-screen code editor using prompt_toolkit."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Callable, Optional

from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.filters import Condition
from prompt_toolkit.key_binding import KeyBindings, merge_key_bindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import ConditionalContainer, HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.margins import NumberedMargin, ScrollbarMargin
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.output import ColorDepth
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import SearchToolbar, TextArea

from godot_editor.autocomplete import GodotCompleter
from godot_editor.fileutils import get_label, get_pygments_lexer_name


# ── Pygments lexer lookup ────────────────────────────────────────────────────

def _get_lexer(language: str):
    from pygments.lexers import get_lexer_by_name
    from pygments.util import ClassNotFound

    lexer_name = get_pygments_lexer_name(language)
    try:
        return get_lexer_by_name(lexer_name)
    except ClassNotFound:
        from pygments.lexers import TextLexer
        return TextLexer()


# ── Dark IDE style ────────────────────────────────────────────────────────────

EDITOR_STYLE = Style.from_dict({
    # Chrome
    "titlebar":               "bg:#89dceb #11111b bold",
    "titlebar.filename":      "bg:#89dceb #11111b bold",
    "statusbar":              "bg:#89dceb #11111b",
    "statusbar.dirty":        "bg:#f38ba8 #11111b bold",
    "helpbar":                "bg:#181825 #585b70",
    "helpbar.key":            "bg:#181825 #89dceb bold",
    # Editor background
    "":                       "bg:#11111b #cdd6f4",
    # Line numbers (via margin)
    "line-number":            "#585b70",
    "line-number.current":    "#b4befe bold",
    # Autocomplete
    "completion-menu":                    "bg:#1e1e2e #cdd6f4",
    "completion-menu.completion":         "bg:#1e1e2e #cdd6f4",
    "completion-menu.completion.current": "bg:#313244 #89dceb bold",
    "completion-menu.meta.completion":              "#6c7086",
    "completion-menu.meta.completion.current":      "#89b4fa",
    "completion-menu.border":             "#313244",
    # Search
    "search":                 "bg:#f9e2af #11111b",
    "search.current":         "bg:#f38ba8 #11111b bold",
    "incsearch.current":      "bg:#f9e2af #11111b",
    # Pygments tokens (catppuccin mocha)
    "pygments.keyword":            "#cba6f7 bold",
    "pygments.keyword.constant":   "#fab387",
    "pygments.keyword.namespace":  "#cba6f7",
    "pygments.name.builtin":       "#94e2d5",
    "pygments.name.function":      "#89b4fa",
    "pygments.name.class":         "#f5c2e7 bold",
    "pygments.name.decorator":     "#f9e2af",
    "pygments.name.exception":     "#f38ba8",
    "pygments.literal.string":     "#a6e3a1",
    "pygments.literal.string.doc": "#a6e3a1 italic",
    "pygments.literal.number":     "#fab387",
    "pygments.comment":            "#585b70 italic",
    "pygments.operator":           "#89dceb",
    "pygments.punctuation":        "#cdd6f4",
    "pygments.generic.heading":    "#89dceb bold",   # TSCN section headers
    "pygments.name.attribute":     "#89b4fa",         # TSCN keys
    "pygments.name.tag":           "#89dceb",
    "pygments.token":              "#cdd6f4",
})


# ── Key bindings ──────────────────────────────────────────────────────────────

def _make_keybindings(
    text_area: TextArea,
    saved_flag: list[bool],
    status_msg: list[str],
    on_save: Callable[[str], None],
    tab_size: int,
    language: str,
) -> KeyBindings:
    kb = KeyBindings()

    # ── Save ────────────────────────────────────────────
    @kb.add("c-s")
    def do_save(event):
        on_save(text_area.text)
        saved_flag[0] = True
        status_msg[0] = "  ✓ Saved"

    # ── Quit ────────────────────────────────────────────
    @kb.add("c-q")
    @kb.add("c-w")
    def do_quit(event):
        event.app.exit(result=text_area.text)

    # ── Tab (indent / accept completion) ────────────────
    @kb.add("tab")
    def do_tab(event):
        buf = event.app.current_buffer
        if buf.complete_state:
            buf.complete_next()
        else:
            buf.insert_text(" " * tab_size)

    @kb.add("s-tab")
    def do_shift_tab(event):
        buf = event.app.current_buffer
        if buf.complete_state:
            buf.complete_previous()
        else:
            # Dedent current line
            doc  = buf.document
            line = doc.current_line
            col  = doc.cursor_position_col
            if line.startswith(" " * tab_size):
                # Move cursor to start
                buf.cursor_left(count=col)
                for _ in range(tab_size):
                    if buf.document.current_line.startswith(" "):
                        buf.delete()

    # ── Escape (close completion) ────────────────────────
    @kb.add("escape")
    def do_escape(event):
        buf = event.app.current_buffer
        if buf.complete_state:
            buf.cancel_completion()
        status_msg[0] = ""

    # ── Ctrl+/ — toggle line comment ─────────────────────
    # Ctrl+/ sends c-_ in many terminals
    @kb.add("c-_")
    def toggle_comment(event):
        if language not in ("gdscript", "c", "cpp", "csharp", "glsl", "gdshader"):
            return
        buf  = event.app.current_buffer
        doc  = buf.document
        line = doc.current_line
        col  = doc.cursor_position_col
        start = doc.cursor_position - col

        if language == "gdscript":
            prefix = "#"
        else:
            prefix = "//"

        stripped = line.lstrip()
        indent   = len(line) - len(stripped)

        if stripped.startswith(prefix + " "):
            new_line = " " * indent + stripped[len(prefix) + 1:]
        elif stripped.startswith(prefix):
            new_line = " " * indent + stripped[len(prefix):]
        else:
            new_line = " " * indent + prefix + " " + stripped

        buf.cursor_position = start
        buf.delete(count=len(line))
        buf.insert_text(new_line)
        status_msg[0] = ""

    # ── Ctrl+D — duplicate line ───────────────────────────
    @kb.add("c-d")
    def duplicate_line(event):
        buf  = event.app.current_buffer
        doc  = buf.document
        line = doc.current_line
        col  = doc.cursor_position_col
        end  = doc.cursor_position - col + len(line)
        buf.cursor_position = end
        buf.insert_text("\n" + line)

    # ── Ctrl+G — go to line ───────────────────────────────
    @kb.add("c-g")
    def go_to_line(event):
        status_msg[0] = "  [Ctrl+G] Type line number and Enter in the editor"

    # ── Mark dirty on text change ─────────────────────────
    def on_text_changed(_):
        saved_flag[0] = False
        if status_msg[0].startswith("  ✓"):
            status_msg[0] = ""

    text_area.buffer.on_text_changed += on_text_changed

    return kb


# ── Main editor function ──────────────────────────────────────────────────────

def open_editor(
    filename: str,
    content: str,
    language: str,
    on_save: Callable[[str], None],
    tab_size: int = 2,
    line_numbers: bool = True,
    autocomplete: bool = True,
) -> str:
    """
    Open a full-screen editor.
    Returns the final text (caller can save it again if needed).
    """
    saved_flag  = [True]
    status_msg  = [""]

    lexer_obj   = _get_lexer(language)
    completer   = None

    if autocomplete:
        _text_ref: list[str] = [content]
        completer = GodotCompleter(
            language=language,
            get_full_text=lambda: _text_ref[0],
        )

    search_toolbar = SearchToolbar(
        text_if_not_searching=[("class:helpbar", "  Ctrl+F: find")],
        forward_search_prompt="Find: ",
        backward_search_prompt="Find (back): ",
    )

    left_margins = [NumberedMargin()] if line_numbers else []

    text_area = TextArea(
        text=content,
        lexer=PygmentsLexer(type(lexer_obj)),
        completer=completer,
        complete_while_typing=(autocomplete and language == "gdscript"),
        multiline=True,
        wrap_lines=False,
        scrollbar=True,
        line_numbers=False,          # we use left_margins instead
        left_margins=left_margins,
        search_field=search_toolbar,
        focus_on_click=True,
        read_only=False,
    )

    if autocomplete and completer:
        def _sync_text(_):
            _text_ref[0] = text_area.text
        text_area.buffer.on_text_changed += _sync_text

    kb = _make_keybindings(
        text_area, saved_flag, status_msg, on_save, tab_size, language
    )

    # ── UI windows ────────────────────────────────────────

    def title_text():
        dirty  = "● " if not saved_flag[0] else "  "
        lang   = get_label(language)
        return [
            ("class:titlebar", f"  GODOT EDITOR  ━  {dirty}"),
            ("class:titlebar.filename", filename),
            ("class:titlebar", f"  [{lang}]" + " " * 40),
        ]

    def status_text():
        doc  = text_area.document
        row  = doc.cursor_position_row + 1
        col  = doc.cursor_position_col + 1
        lc   = len(text_area.text.split("\n"))
        lang = get_label(language)
        msg  = status_msg[0]
        hint = "  Ctrl+S:save  Ctrl+Q:quit  Ctrl+/:comment  Ctrl+D:dup  Tab:indent"
        style = "class:statusbar.dirty" if not saved_flag[0] else "class:statusbar"
        return [(style, f"  Ln {row}  Col {col}  |  {lc} lines  |  {lang}{msg}{hint}  ")]

    def help_text():
        return [
            ("class:helpbar", "  "),
            ("class:helpbar.key", "Ctrl+S"),
            ("class:helpbar", " save  "),
            ("class:helpbar.key", "Ctrl+Q"),
            ("class:helpbar", " quit  "),
            ("class:helpbar.key", "Ctrl+F"),
            ("class:helpbar", " find  "),
            ("class:helpbar.key", "Ctrl+/"),
            ("class:helpbar", " comment  "),
            ("class:helpbar.key", "Ctrl+Space"),
            ("class:helpbar", " autocomplete  "),
            ("class:helpbar.key", "Tab"),
            ("class:helpbar", " indent  "),
        ]

    title_win  = Window(FormattedTextControl(title_text),  height=1)
    status_win = Window(FormattedTextControl(status_text), height=1)
    help_win   = Window(FormattedTextControl(help_text),   height=1)

    layout = Layout(
        HSplit([
            title_win,
            text_area,
            search_toolbar,
            help_win,
            status_win,
        ]),
        focused_element=text_area,
    )

    app: Application = Application(
        layout=layout,
        key_bindings=kb,
        style=EDITOR_STYLE,
        full_screen=True,
        mouse_support=True,
        color_depth=ColorDepth.TRUE_COLOR,
        enable_page_navigation_bindings=True,
    )

    result = app.run()
    return result if result is not None else text_area.text
