#!/bin/bash
# Build for all platforms: .deb, .exe, .appimage

set -e

print_header "🏗️  Building UFI SMS Commander for All Platforms"

# Build Debian package
echo ""
print_info "Building Debian package..."
./build_deb.sh

# Build AppImage (Linux portable)
echo ""
print_info "Building AppImage..."
./build_appimage.sh

# Build Windows .exe (if Wine is available)
if command -v wine &>/dev/null; then
    echo ""
    print_info "Building Windows .exe..."
    ./build_windows_exe.sh
else
    print_warning "Wine not found. Skipping Windows .exe build"
    print_info "To build Windows .exe, install Wine: sudo apt-get install wine64"
fi

print_header "🎉 All builds complete!"
echo "Available packages:"
ls -lh *.deb *.AppImage *.exe 2>/dev/null || echo "Check build directories"
