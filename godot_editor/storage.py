from __future__ import annotations

import json
import shutil
import time
from pathlib import Path
from typing import Optional

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR     = Path.home() / ".config" / "godot-editor"
PROJECTS_DIR = BASE_DIR / "projects"
CONFIG_FILE  = BASE_DIR / "config.json"

DEFAULT_CONFIG = {
    "tab_size":     2,
    "autocomplete": True,
    "line_numbers": True,
    "word_wrap":    False,
    "theme":        "dark",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def _short_id() -> str:
    import random, string
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=8))


# ── Init ──────────────────────────────────────────────────────────────────────

def init() -> None:
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)


# ── Config ────────────────────────────────────────────────────────────────────

def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            return {**DEFAULT_CONFIG, **json.loads(CONFIG_FILE.read_text())}
        except Exception:
            pass
    return dict(DEFAULT_CONFIG)


def save_config(config: dict) -> None:
    CONFIG_FILE.write_text(json.dumps(config, indent=2))


# ── Projects ──────────────────────────────────────────────────────────────────

def list_projects() -> list[dict]:
    if not PROJECTS_DIR.exists():
        return []
    result = []
    for d in PROJECTS_DIR.iterdir():
        meta_file = d / "project.json"
        if d.is_dir() and meta_file.exists():
            try:
                result.append(json.loads(meta_file.read_text()))
            except Exception:
                pass
    result.sort(key=lambda p: p.get("updated_at", 0), reverse=True)
    return result


def get_project(project_id: str) -> Optional[dict]:
    meta_file = PROJECTS_DIR / project_id / "project.json"
    if meta_file.exists():
        try:
            return json.loads(meta_file.read_text())
        except Exception:
            pass
    return None


def create_project(name: str, description: str = "") -> dict:
    pid  = _short_id()
    pdir = PROJECTS_DIR / pid
    pdir.mkdir(parents=True)
    (pdir / "files").mkdir()
    meta = {
        "id":          pid,
        "name":        name.strip(),
        "description": description.strip(),
        "created_at":  time.time(),
        "updated_at":  time.time(),
    }
    (pdir / "project.json").write_text(json.dumps(meta, indent=2))
    return meta


def delete_project(project_id: str) -> None:
    pdir = PROJECTS_DIR / project_id
    if pdir.exists():
        shutil.rmtree(pdir)


def _touch_project(project_id: str) -> None:
    meta_file = PROJECTS_DIR / project_id / "project.json"
    if meta_file.exists():
        try:
            meta = json.loads(meta_file.read_text())
            meta["updated_at"] = time.time()
            meta_file.write_text(json.dumps(meta, indent=2))
        except Exception:
            pass


# ── Files ─────────────────────────────────────────────────────────────────────

def _files_dir(project_id: str) -> Path:
    return PROJECTS_DIR / project_id / "files"


def list_files(project_id: str) -> list[dict]:
    fdir = _files_dir(project_id)
    if not fdir.exists():
        return []
    result = []
    for f in fdir.iterdir():
        if f.is_file() and not f.name.endswith(".meta"):
            meta_file = Path(str(f) + ".meta")
            if meta_file.exists():
                try:
                    meta = json.loads(meta_file.read_text())
                    meta["size"] = f.stat().st_size
                    result.append(meta)
                except Exception:
                    pass
    result.sort(key=lambda x: x.get("updated_at", 0), reverse=True)
    return result


def get_file_meta(project_id: str, file_id: str) -> Optional[dict]:
    fdir = _files_dir(project_id)
    for meta_file in fdir.glob("*.meta"):
        try:
            meta = json.loads(meta_file.read_text())
            if meta.get("id") == file_id:
                return meta
        except Exception:
            pass
    return None


def get_file_path(project_id: str, filename: str) -> Path:
    return _files_dir(project_id) / filename


def create_file(project_id: str, filename: str, content: str = "") -> dict:
    from godot_editor.fileutils import detect_language
    fdir = _files_dir(project_id)
    fdir.mkdir(parents=True, exist_ok=True)

    filepath = fdir / filename
    filepath.write_text(content, encoding="utf-8")

    fid  = _short_id()
    meta = {
        "id":         fid,
        "name":       filename,
        "language":   detect_language(filename),
        "created_at": time.time(),
        "updated_at": time.time(),
    }
    Path(str(filepath) + ".meta").write_text(json.dumps(meta, indent=2))
    _touch_project(project_id)
    return meta


def read_file(project_id: str, filename: str) -> str:
    filepath = get_file_path(project_id, filename)
    if filepath.exists():
        return filepath.read_text(encoding="utf-8", errors="replace")
    return ""


def write_file(project_id: str, filename: str, content: str) -> None:
    filepath = get_file_path(project_id, filename)
    filepath.write_text(content, encoding="utf-8")
    meta_file = Path(str(filepath) + ".meta")
    if meta_file.exists():
        try:
            meta = json.loads(meta_file.read_text())
            meta["updated_at"] = time.time()
            meta_file.write_text(json.dumps(meta, indent=2))
        except Exception:
            pass
    _touch_project(project_id)


def delete_file(project_id: str, filename: str) -> None:
    filepath = get_file_path(project_id, filename)
    meta_file = Path(str(filepath) + ".meta")
    if filepath.exists():
        filepath.unlink()
    if meta_file.exists():
        meta_file.unlink()
    _touch_project(project_id)


def rename_file(project_id: str, old_name: str, new_name: str) -> None:
    from godot_editor.fileutils import detect_language
    fdir = _files_dir(project_id)
    old_path = fdir / old_name
    new_path = fdir / new_name
    old_meta = Path(str(old_path) + ".meta")
    new_meta = Path(str(new_path) + ".meta")
    if old_path.exists():
        old_path.rename(new_path)
    if old_meta.exists():
        meta = json.loads(old_meta.read_text())
        meta["name"]     = new_name
        meta["language"] = detect_language(new_name)
        meta["updated_at"] = time.time()
        new_meta.write_text(json.dumps(meta, indent=2))
        old_meta.unlink()
    _touch_project(project_id)
