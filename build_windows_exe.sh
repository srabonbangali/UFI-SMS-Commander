#!/bin/bash
# Build Windows .exe from Linux using Wine

set -e

print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_header() { echo ""; echo "============================================"; echo -e "${BLUE}$1${NC}"; echo "============================================"; echo ""; }

print_header "Building Windows .exe from Linux"

# Check for Wine
if ! command -v wine &>/dev/null; then
    print_error "Wine is required to build Windows .exe on Linux"
    print_info "Install Wine: sudo apt-get install wine64"
    exit 1
fi

# Check for PyInstaller in Wine
print_info "Setting up Windows Python environment..."
wine python -m pip install pyinstaller PyQt6 requests

# Build
print_info "Building .exe..."
wine python -m pyinstaller \
    --onefile \
    --windowed \
    --name="UFI-SMS-Commander" \
    --add-data="docs;docs" \
    --hidden-import=PyQt6 \
    --hidden-import=requests \
    --clean \
    sms_manager.py

print_success "Build complete: dist/UFI-SMS-Commander.exe"
