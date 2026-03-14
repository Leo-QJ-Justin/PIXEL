#!/usr/bin/env bash
set -euo pipefail

# PIXEL setup script — works on Linux, macOS, and WSL

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
fail()  { echo -e "${RED}[✗]${NC} $1"; exit 1; }

cd "$(dirname "$0")"

echo ""
echo "  ╔══════════════════════════════╗"
echo "  ║     PIXEL Setup Script       ║"
echo "  ╚══════════════════════════════╝"
echo ""

# ── 1. Check Python ──────────────────────────────────────────────

if command -v python3 &>/dev/null; then
    PY=python3
elif command -v python &>/dev/null; then
    PY=python
else
    fail "Python not found. Install Python 3.10+ first."
fi

PY_VERSION=$($PY -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$($PY -c "import sys; print(sys.version_info.major)")
PY_MINOR=$($PY -c "import sys; print(sys.version_info.minor)")

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
    fail "Python $PY_VERSION found, but 3.10+ is required."
fi
info "Python $PY_VERSION"

# ── 2. Check uv ──────────────────────────────────────────────────

if ! command -v uv &>/dev/null; then
    warn "uv not found. Installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    if ! command -v uv &>/dev/null; then
        fail "uv installation failed. Install manually: https://docs.astral.sh/uv/"
    fi
fi
info "uv $(uv --version 2>/dev/null | head -1)"

# ── 3. Check Node.js ─────────────────────────────────────────────

if ! command -v node &>/dev/null; then
    fail "Node.js not found. Install Node.js 18+ first: https://nodejs.org"
fi

NODE_MAJOR=$(node -e "console.log(process.versions.node.split('.')[0])")
if [ "$NODE_MAJOR" -lt 18 ]; then
    fail "Node.js v$(node -v) found, but v18+ is required."
fi
info "Node.js $(node -v)"

if ! command -v npm &>/dev/null; then
    fail "npm not found. It should come with Node.js."
fi
info "npm $(npm -v)"

# ── 4. System libraries (Linux/WSL only) ─────────────────────────

if [[ "$(uname -s)" == "Linux" ]]; then
    MISSING_LIBS=()
    ldconfig -p 2>/dev/null | grep -q libnss3.so    || MISSING_LIBS+=("libnss3")
    if ! ldconfig -p 2>/dev/null | grep -q libasound.so.2; then
        # Ubuntu 24.04+ renamed libasound2 to libasound2t64
        if apt-cache show libasound2t64 &>/dev/null; then
            MISSING_LIBS+=("libasound2t64")
        else
            MISSING_LIBS+=("libasound2")
        fi
    fi

    if [ ${#MISSING_LIBS[@]} -gt 0 ]; then
        warn "Missing system libraries: ${MISSING_LIBS[*]}"
        echo "     WebEngine (Chromium) needs these to run."
        if command -v apt-get &>/dev/null; then
            echo ""
            echo "     Run: sudo apt-get install -y ${MISSING_LIBS[*]}"
            echo ""
            if [ -t 0 ]; then
                # Interactive terminal — ask
                read -rp "     Install now? (requires sudo) [y/N] " answer
                if [[ "$answer" =~ ^[Yy]$ ]]; then
                    sudo apt-get install -y "${MISSING_LIBS[@]}"
                    info "System libraries installed"
                else
                    warn "Skipped. Install them manually before opening React panels."
                fi
            else
                warn "Non-interactive shell. Install them manually before opening React panels."
            fi
        else
            warn "Install manually: ${MISSING_LIBS[*]}"
        fi
    else
        info "System libraries OK"
    fi
fi

# ── 5. Python dependencies ────────────────────────────────────────

echo ""
info "Installing Python dependencies..."
uv sync
info "Python dependencies installed"

# ── 6. React UI ───────────────────────────────────────────────────

echo ""
info "Installing React UI dependencies..."
cd ui
npm install --loglevel=warn
info "npm packages installed"

info "Building React UI..."
npm run build --silent
info "React UI built (ui/dist/)"
cd ..

# ── 7. Environment file ──────────────────────────────────────────

if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        info "Created .env from .env.example — fill in your API keys"
    else
        warn "No .env file found. Create one if you need Weather or Calendar integrations."
    fi
else
    info ".env already exists"
fi

# ── Done ──────────────────────────────────────────────────────────

echo ""
echo -e "${GREEN}  Setup complete!${NC}"
echo ""
echo "  Run the app:"
echo "    uv run python main.py"
echo ""
echo "  For React UI development (hot-reload):"
echo "    cd ui && npm run dev        # Terminal 1"
echo "    PIXEL_DEV_UI=1 uv run python main.py  # Terminal 2"
echo ""
