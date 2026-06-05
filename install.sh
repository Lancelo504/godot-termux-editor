#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  Godot Editor for Termux — install.sh
#  Supports: Termux (Android) · Linux · macOS
# ─────────────────────────────────────────────────────────────────────────────
set -e

# ── Colors ────────────────────────────────────────────────────────────────────
CYAN="\033[0;36m"; BOLD="\033[1m"; GREEN="\033[0;32m"
YELLOW="\033[0;33m"; RED="\033[0;31m"; RESET="\033[0m"

info()    { echo -e "${CYAN}${BOLD}[INFO]${RESET}  $*"; }
ok()      { echo -e "${GREEN}${BOLD}[ OK ]${RESET}  $*"; }
warn()    { echo -e "${YELLOW}${BOLD}[WARN]${RESET}  $*"; }
err()     { echo -e "${RED}${BOLD}[ERR ]${RESET}  $*"; exit 1; }

# ── Header ────────────────────────────────────────────────────────────────────
echo -e ""
echo -e "${CYAN}${BOLD}"
echo -e "  ██████╗  ██████╗ ██████╗  ██████╗ ████████╗"
echo -e " ██╔════╝ ██╔═══██╗██╔══██╗██╔═══██╗╚══██╔══╝"
echo -e " ██║  ███╗██║   ██║██║  ██║██║   ██║   ██║   "
echo -e " ██║   ██║██║   ██║██║  ██║██║   ██║   ██║   "
echo -e " ╚██████╔╝╚██████╔╝██████╔╝╚██████╔╝   ██║   "
echo -e "  ╚═════╝  ╚═════╝ ╚═════╝  ╚═════╝   ╚═╝   "
echo -e "${RESET}"
echo -e "${BOLD}  Godot Engine code editor for Termux${RESET}"
echo -e "  GDScript · TSCN · TRES · C · C++ · C# · Shader"
echo -e ""

# ── Detect environment ────────────────────────────────────────────────────────
IS_TERMUX=false
if [ -n "$TERMUX_VERSION" ] || [ -d "/data/data/com.termux" ]; then
    IS_TERMUX=true
    info "Termux environment detected."
else
    info "Standard Linux/macOS environment detected."
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Install system packages (Termux only) ─────────────────────────────────────
if $IS_TERMUX; then
    info "Updating Termux packages..."
    pkg update -y 2>/dev/null || warn "pkg update failed, continuing..."
    info "Installing Python..."
    pkg install -y python 2>/dev/null || true
fi

# ── Check Python ──────────────────────────────────────────────────────────────
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        VER=$("$cmd" -c "import sys; print(sys.version_info >= (3, 8))")
        if [ "$VER" = "True" ]; then
            PYTHON="$cmd"
            break
        fi
    fi
done

[ -z "$PYTHON" ] && err "Python 3.8+ not found. Install it first."
ok "Python found: $($PYTHON --version)"

# ── Check/install pip ─────────────────────────────────────────────────────────
if ! "$PYTHON" -m pip --version &>/dev/null; then
    info "Installing pip..."
    if $IS_TERMUX; then
        pkg install -y python-pip 2>/dev/null || true
    else
        curl -sSL https://bootstrap.pypa.io/get-pip.py | "$PYTHON"
    fi
fi
ok "pip available: $($PYTHON -m pip --version | cut -d' ' -f1-2)"

# ── Install Python dependencies ───────────────────────────────────────────────
info "Installing Python dependencies..."
"$PYTHON" -m pip install --quiet --upgrade \
    "rich>=13.0.0" \
    "prompt_toolkit>=3.0.0" \
    "pygments>=2.14.0"
ok "Python dependencies installed."

# ── Determine installation directory ─────────────────────────────────────────
if $IS_TERMUX; then
    INSTALL_DIR="$HOME/.local/share/godot-editor"
    BIN_DIR="$PREFIX/bin"
else
    INSTALL_DIR="$HOME/.local/share/godot-editor"
    BIN_DIR="$HOME/.local/bin"
    mkdir -p "$BIN_DIR"
fi

# ── Copy application files ────────────────────────────────────────────────────
info "Installing application to $INSTALL_DIR ..."
mkdir -p "$INSTALL_DIR"

# Copy the godot_editor package
rm -rf "$INSTALL_DIR/godot_editor"
cp -r "$SCRIPT_DIR/godot_editor" "$INSTALL_DIR/"

ok "Application files copied."

# ── Create launcher script ────────────────────────────────────────────────────
LAUNCHER="$BIN_DIR/godot-editor"
info "Creating launcher at $LAUNCHER ..."

cat > "$LAUNCHER" << LAUNCHER_EOF
#!/usr/bin/env bash
# Godot Editor for Termux launcher
export PYTHONPATH="$INSTALL_DIR:\$PYTHONPATH"
exec "$PYTHON" -m godot_editor.main "\$@"
LAUNCHER_EOF

chmod +x "$LAUNCHER"
ok "Launcher created."

# ── Verify BIN_DIR is in PATH ─────────────────────────────────────────────────
if ! echo "$PATH" | grep -q "$BIN_DIR"; then
    warn "$BIN_DIR is not in your PATH."
    echo ""
    if $IS_TERMUX; then
        echo -e "  Add this to ${BOLD}~/.bashrc${RESET} or ${BOLD}~/.zshrc${RESET}:"
    else
        echo -e "  Add this to your shell profile:"
    fi
    echo -e "    ${CYAN}export PATH=\"\$PATH:$BIN_DIR\"${RESET}"
    echo ""
    LAUNCH_CMD="$LAUNCHER"
else
    LAUNCH_CMD="godot-editor"
fi

# ── Verify installation ───────────────────────────────────────────────────────
info "Verifying installation..."
if "$PYTHON" -c "
import sys
sys.path.insert(0, '$INSTALL_DIR')
from godot_editor.storage import init
from godot_editor.autocomplete import get_class_names
init()
classes = get_class_names()
print(f'  → Loaded {len(classes)} Godot API classes')
" 2>&1; then
    ok "Installation verified."
else
    warn "Verification had warnings (may still work)."
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════╗${RESET}"
echo -e "${GREEN}${BOLD}║  Installation complete!                  ║${RESET}"
echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════╝${RESET}"
echo ""
echo -e "  Start the editor:"
echo -e "    ${CYAN}${BOLD}${LAUNCH_CMD}${RESET}"
echo ""
echo -e "  Open a file directly:"
echo -e "    ${CYAN}${BOLD}${LAUNCH_CMD} path/to/script.gd${RESET}"
echo ""
echo -e "  Quick help:"
echo -e "    ${CYAN}${BOLD}${LAUNCH_CMD} --help${RESET}"
echo ""
