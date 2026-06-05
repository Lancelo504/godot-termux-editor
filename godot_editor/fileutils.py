from __future__ import annotations

EXTENSION_MAP: dict[str, str] = {
    "gd":       "gdscript",
    "tscn":     "tscn",
    "tres":     "tres",
    "c":        "c",
    "h":        "c",
    "cpp":      "cpp",
    "cc":       "cpp",
    "cxx":      "cpp",
    "hpp":      "cpp",
    "cs":       "csharp",
    "glsl":     "glsl",
    "gdshader": "gdshader",
    "json":     "json",
    "cfg":      "cfg",
    "ini":      "cfg",
    "godot":    "cfg",
    "md":       "markdown",
    "txt":      "text",
}

LANGUAGE_LABELS: dict[str, str] = {
    "gdscript": "GDScript",
    "tscn":     "Godot Scene",
    "tres":     "Godot Resource",
    "c":        "C",
    "cpp":      "C++",
    "csharp":   "C#",
    "glsl":     "GLSL",
    "gdshader": "GD Shader",
    "json":     "JSON",
    "cfg":      "Config",
    "markdown": "Markdown",
    "text":     "Plain Text",
}

LANGUAGE_COLORS: dict[str, str] = {
    "gdscript": "bold magenta",
    "tscn":     "bold cyan",
    "tres":     "bold blue",
    "c":        "bold yellow",
    "cpp":      "bold red",
    "csharp":   "bold green",
    "glsl":     "bold bright_yellow",
    "gdshader": "bold bright_yellow",
    "json":     "bold green",
    "cfg":      "bold white",
    "markdown": "bold white",
    "text":     "dim white",
}

FILE_STARTER_CONTENT: dict[str, str] = {
    "gdscript": """\
extends Node

@export var speed: float = 200.0


func _ready() -> void:
\tprint("Hello from Godot!")


func _process(delta: float) -> void:
\tpass
""",
    "tscn": """\
[gd_scene load_steps=1 format=3 uid="uid://sample"]

[node name="Root" type="Node2D"]
""",
    "tres": """\
[gd_resource type="Resource" format=3]

[resource]
""",
    "c": """\
#include <stdio.h>

int main(int argc, char *argv[]) {
\tprintf("Hello, World!\\n");
\treturn 0;
}
""",
    "cpp": """\
#include <iostream>

int main() {
\tstd::cout << "Hello, World!" << std::endl;
\treturn 0;
}
""",
    "csharp": """\
using Godot;

public partial class MyNode : Node
{
\tpublic override void _Ready()
\t{
\t\tGD.Print("Hello from C#!");
\t}
}
""",
    "gdshader": """\
shader_type canvas_item;

void fragment() {
\tCOLOR = vec4(1.0, 1.0, 1.0, 1.0);
}
""",
    "json": """\
{
  "name": "my_resource",
  "version": "1.0.0"
}
""",
    "cfg": """\
[settings]
key=value
""",
    "text": "",
}


def detect_language(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return EXTENSION_MAP.get(ext, "text")


def get_label(language: str) -> str:
    return LANGUAGE_LABELS.get(language, "Text")


def get_color(language: str) -> str:
    return LANGUAGE_COLORS.get(language, "white")


def get_starter(language: str) -> str:
    return FILE_STARTER_CONTENT.get(language, "")


def get_pygments_lexer_name(language: str) -> str:
    mapping = {
        "gdscript": "gdscript",
        "tscn":     "text",
        "tres":     "text",
        "c":        "c",
        "cpp":      "cpp",
        "csharp":   "csharp",
        "glsl":     "glsl",
        "gdshader": "glsl",
        "json":     "json",
        "cfg":      "ini",
        "markdown": "markdown",
        "text":     "text",
    }
    return mapping.get(language, "text")
