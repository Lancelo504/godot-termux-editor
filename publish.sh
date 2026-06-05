#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  publish.sh — helper script to publish godot-termux-editor to GitHub
#  Run this from INSIDE the godot-termux/ directory.
# ─────────────────────────────────────────────────────────────────────────────
set -e

CYAN="\033[0;36m"; BOLD="\033[1m"; GREEN="\033[0;32m"
YELLOW="\033[0;33m"; RED="\033[0;31m"; RESET="\033[0m"

info() { echo -e "${CYAN}${BOLD}[INFO]${RESET}  $*"; }
ok()   { echo -e "${GREEN}${BOLD}[ OK ]${RESET}  $*"; }
warn() { echo -e "${YELLOW}${BOLD}[WARN]${RESET}  $*"; }
err()  { echo -e "${RED}${BOLD}[ERR ]${RESET}  $*"; exit 1; }
ask()  { echo -e "${CYAN}${BOLD}[ >> ]${RESET}  $*"; }

echo -e ""
echo -e "${CYAN}${BOLD}  Godot Editor for Termux — GitHub publisher${RESET}"
echo -e "  ──────────────────────────────────────────"
echo -e ""

# ── 1. Check git ──────────────────────────────────────────────────────────────
command -v git &>/dev/null || err "git not found. Install it first: pkg install git"
ok "git found: $(git --version)"

# ── 2. Ask for GitHub username ────────────────────────────────────────────────
echo ""
ask "Your GitHub username:"
read -r GH_USER
[ -z "$GH_USER" ] && err "Username cannot be empty."

REPO_NAME="godot-termux-editor"
REMOTE_URL="https://github.com/${GH_USER}/${REPO_NAME}.git"

# ── 3. Check if already a git repo ───────────────────────────────────────────
if [ ! -d ".git" ]; then
    info "Initializing git repository..."
    git init
    ok "Git repository initialized."
fi

# ── 4. Update placeholders with real username ─────────────────────────────────
info "Updating your GitHub username in project files..."
for file in README.md pyproject.toml CONTRIBUTING.md; do
    if [ -f "$file" ]; then
        sed -i "s|your-username|${GH_USER}|g" "$file"
        ok "  Updated $file"
    fi
done

# ── 5. Stage all files ────────────────────────────────────────────────────────
info "Staging files..."
git add -A
git status --short
ok "Files staged."

# ── 6. Initial commit ─────────────────────────────────────────────────────────
if git log --oneline 2>/dev/null | grep -q .; then
    warn "Repo already has commits. Adding new commit..."
    git commit -m "Update: automated publish setup" 2>/dev/null || warn "Nothing new to commit."
else
    info "Creating initial commit..."
    git commit -m "feat: initial release v1.0.0

Godot Engine code editor for Termux and Linux CLI.
- Full-screen editor with syntax highlighting
- Godot 4 API autocomplete (1,503 classes)
- Project and file manager
- GDScript, TSCN, TRES, C, C++, C#, GLSL support
- pip-installable (godot-termux-editor)"
    ok "Initial commit created."
fi

# ── 7. Set main branch ────────────────────────────────────────────────────────
git branch -M main 2>/dev/null || true

# ── 8. Instructions ───────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════════════════╗${RESET}"
echo -e "${GREEN}${BOLD}║  Local repo ready!  Follow these steps to publish:       ║${RESET}"
echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════════════════════╝${RESET}"
echo ""
echo -e "  ${BOLD}Step 1${RESET} — Create the repo on GitHub:"
echo -e "  ${CYAN}  https://github.com/new${RESET}"
echo -e "  Set name:  ${BOLD}${REPO_NAME}${RESET}"
echo -e "  Description: Godot Engine code editor for Termux"
echo -e "  Visibility: ${BOLD}Public${RESET}"
echo -e "  ⚠  Do NOT add README, .gitignore or license (already in the project)"
echo ""
echo -e "  ${BOLD}Step 2${RESET} — Add remote and push:"
echo -e "  ${CYAN}  git remote add origin ${REMOTE_URL}${RESET}"
echo -e "  ${CYAN}  git push -u origin main${RESET}"
echo ""
echo -e "  ${BOLD}Step 3${RESET} — Create a release tag (triggers PyPI publish):"
echo -e "  ${CYAN}  git tag v1.0.0${RESET}"
echo -e "  ${CYAN}  git push origin v1.0.0${RESET}"
echo ""
echo -e "  ${BOLD}Your repo will be at:${RESET}"
echo -e "  ${CYAN}  https://github.com/${GH_USER}/${REPO_NAME}${RESET}"
echo ""
echo -e "  ${BOLD}Install command for users:${RESET}"
echo -e "  ${CYAN}  pip install git+https://github.com/${GH_USER}/${REPO_NAME}.git${RESET}"
echo ""
