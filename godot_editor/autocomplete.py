from __future__ import annotations

import json
from pathlib import Path
from typing import Generator, Optional

from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document

# ── API data ──────────────────────────────────────────────────────────────────

_API: Optional[dict] = None
_CLASS_NAMES: Optional[list[str]] = None

def _load_api() -> dict:
    global _API, _CLASS_NAMES
    if _API is None:
        data_path = Path(__file__).parent / "data" / "godot_api_compact.json"
        with open(data_path, encoding="utf-8") as f:
            _API = json.load(f)
        _CLASS_NAMES = sorted(_API.keys())
    return _API


def get_class_names() -> list[str]:
    _load_api()
    return _CLASS_NAMES or []


def get_class_members(class_name: str) -> list[str]:
    api = _load_api()
    info = api.get(class_name)
    if not info:
        return []
    return info.get("m", []) + info.get("p", []) + info.get("c", [])


def get_all_members_in_chain(class_name: str) -> list[str]:
    api = _load_api()
    members: set[str] = set()
    current: Optional[str] = class_name
    depth = 0
    while current and depth < 20:
        info = api.get(current)
        if not info:
            break
        members.update(info.get("m", []))
        members.update(info.get("p", []))
        members.update(info.get("c", []))
        current = info.get("i")
        depth += 1
    return sorted(members)


# ── GDScript vocabulary ───────────────────────────────────────────────────────

KEYWORDS = [
    "var", "const", "func", "class", "class_name", "extends", "signal",
    "enum", "static", "if", "elif", "else", "for", "while", "match",
    "break", "continue", "return", "pass", "not", "and", "or", "in",
    "is", "as", "self", "true", "false", "null", "void", "await",
    "super", "breakpoint", "new",
]

BUILTINS = [
    "print", "printerr", "push_error", "push_warning", "typeof",
    "str", "int", "float", "bool", "len", "range", "abs", "min",
    "max", "clamp", "lerp", "sign", "floor", "ceil", "round",
    "sqrt", "pow", "sin", "cos", "tan", "atan2",
    "deg_to_rad", "rad_to_deg",
    "preload", "load",
    "get_node", "add_child", "remove_child", "queue_free",
    "emit_signal", "connect", "disconnect", "call_deferred",
    "instantiate", "duplicate",
    "Vector2", "Vector3", "Vector2i", "Vector3i",
    "Color", "Rect2", "Transform2D", "Transform3D",
    "Basis", "Quaternion", "AABB", "Plane",
    "Array", "Dictionary", "PackedScene", "NodePath", "StringName",
    "RID", "Callable",
]

ANNOTATIONS = [
    "@export", "@onready", "@tool", "@static_unload", "@icon",
    "@warning_ignore", "@export_range", "@export_enum", "@export_file",
    "@export_dir", "@export_multiline", "@export_placeholder",
    "@export_color_no_alpha", "@export_node_path",
]


# ── Completer ────────────────────────────────────────────────────────────────

def _word_before_cursor(text: str) -> str:
    """Return the identifier fragment directly before the cursor."""
    i = len(text)
    while i > 0 and (text[i - 1].isalnum() or text[i - 1] == "_"):
        i -= 1
    return text[i:]


def _try_resolve_type(code: str, var_name: str) -> Optional[str]:
    """Best-effort variable → class resolution from surrounding code."""
    import re
    patterns = [
        rf"\bvar\s+{re.escape(var_name)}\s*:\s*(\w+)",
        rf"\bvar\s+{re.escape(var_name)}\s*=\s*(\w+)\.new\(",
    ]
    for pat in patterns:
        m = re.search(pat, code)
        if m:
            return m.group(1)
    if var_name == "self":
        m = re.search(r"^extends\s+(\w+)", code, re.MULTILINE)
        if m:
            return m.group(1)
    return None


class GodotCompleter(Completer):
    def __init__(self, language: str, get_full_text: "callable[[], str] | None" = None):
        self.language = language
        self.get_full_text = get_full_text

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Generator[Completion, None, None]:
        if self.language not in ("gdscript", "tscn", "tres"):
            return

        text_before = document.text_before_cursor
        current_line = text_before.split("\n")[-1]

        # ── Member access:  SomeClass.prefix  or  var.prefix ──────────────
        if "." in current_line:
            dot_pos = current_line.rfind(".")
            prefix  = current_line[dot_pos + 1:]
            obj_str = current_line[:dot_pos].split()[-1] if current_line[:dot_pos].split() else ""

            # Strip leading ( or operators
            obj_name = obj_str.lstrip("(").rstrip(")")

            full_text = self.get_full_text() if self.get_full_text else ""
            class_name: Optional[str] = None

            if obj_name[0:1].isupper():
                class_name = obj_name
            else:
                class_name = _try_resolve_type(full_text, obj_name)
                if not class_name:
                    class_name = "Node"  # fallback

            members = get_all_members_in_chain(class_name)[:200]
            for m in members:
                if m.lower().startswith(prefix.lower()):
                    yield Completion(m, start_position=-len(prefix),
                                     display_meta=class_name)
            return

        # ── Annotation: @prefix ───────────────────────────────────────────
        if current_line.lstrip().startswith("@"):
            at_text = current_line.lstrip()
            prefix  = at_text.lstrip("@")
            for ann in ANNOTATIONS:
                if ann.lstrip("@").startswith(prefix):
                    yield Completion(ann, start_position=-(len(at_text)),
                                     display_meta="annotation")
            return

        # ── General: word at cursor ───────────────────────────────────────
        word = _word_before_cursor(current_line)
        if len(word) < 2:
            return

        seen: set[str] = set()

        for kw in KEYWORDS:
            if kw.startswith(word) and kw not in seen:
                seen.add(kw)
                yield Completion(kw, start_position=-len(word), display_meta="keyword")

        for bi in BUILTINS:
            if bi.startswith(word) and bi not in seen:
                seen.add(bi)
                yield Completion(bi, start_position=-len(word), display_meta="builtin")

        try:
            classes = get_class_names()
        except Exception:
            return

        count = 0
        for cls in classes:
            if cls.startswith(word) and cls not in seen:
                seen.add(cls)
                api  = _load_api()
                info = api.get(cls, {})
                meta = f"class  ← {info.get('i', '')}" if info.get("i") else "class"
                yield Completion(cls, start_position=-len(word), display_meta=meta)
                count += 1
                if count >= 40:
                    break
