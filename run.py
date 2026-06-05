#!/usr/bin/env python3
"""Launcher — run this directly: python run.py [FILE]"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from godot_editor.main import main

if __name__ == "__main__":
    main()
