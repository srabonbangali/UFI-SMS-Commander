#!/bin/bash
# Build Debian package (.deb) for UFI SMS Commander

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_header() { echo ""; echo "============================================"; echo -e "${BLUE}$1${NC}"; echo "============================================"; echo ""; }

# Version
VERSION="2.0"
PACKAGE_NAME="ufi-sms-commander"
ARCH="all"

print_header "📦 Building Debian Package: $PACKAGE_NAME-$VERSION"

# Create build directories
print_info "Creating build structure..."
rm -rf debian-build
mkdir -p debian-build

# Create package structure
PACKAGE_ROOT="debian-build/$PACKAGE_NAME-$VERSION"
mkdir -p "$PACKAGE_ROOT/DEBIAN"
mkdir -p "$PACKAGE_ROOT/usr/bin"
mkdir -p "$PACKAGE_ROOT/usr/share/applications"
mkdir -p "$PACKAGE_ROOT/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$PACKAGE_ROOT/usr/share/doc/$PACKAGE_NAME"
mkdir -p "$PACKAGE_ROOT/usr/lib/$PACKAGE_NAME"

# Copy application files
print_info "Copying application files..."
cp sms_manager.py "$PACKAGE_ROOT/usr/lib/$PACKAGE_NAME/"
cp requirements.txt "$PACKAGE_ROOT/usr/lib/$PACKAGE_NAME/"
cp -r docs "$PACKAGE_ROOT/usr/lib/$PACKAGE_NAME/"

# Create wrapper script
cat > "$PACKAGE_ROOT/usr/bin/ufi-sms-commander" << 'EOF'
#!/bin/bash
# Wrapper script for UFI SMS Commander

DIR="/usr/lib/ufi-sms-commander"
cd "$DIR"
python3 sms_manager.py
EOF

chmod +x "$PACKAGE_ROOT/usr/bin/ufi-sms-commander"

# Create desktop entry
cat > "$PACKAGE_ROOT/usr/share/applications/ufi-sms-commander.desktop" << EOF
[Desktop Entry]
Name=UFI SMS Commander
Comment=Manage SMS on ZTE/OLAX 4G routers
Exec=ufi-sms-commander
Icon=ufi-sms-commander
Terminal=false
Type=Application
Categories=Network;Utility;
StartupNotify=true
EOF

# Create icon (placeholder - you can add real icon later)
cat > "$PACKAGE_ROOT/usr/share/icons/hicolor/256x256/apps/ufi-sms-commander.svg" << 'EOF'
<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">
  <rect width="256" height="256" rx="50" fill="#1e1e1e"/>
  <text x="128" y="140" font-family="Arial" font-size="80" text-anchor="middle" fill="#00c8ff">📱</text>
  <text x="128" y="210" font-family="Arial" font-size="24" text-anchor="middle" fill="#00c8ff">SMS</text>
</svg>
EOF

# Create control file
cat > "$PACKAGE_ROOT/DEBIAN/control" << EOF
Package: $PACKAGE_NAME
Version: $VERSION
Section: net
Priority: optional
Architecture: $ARCH
Depends: python3, python3-pyqt6, python3-requests, python3-pyqt6.qtcore, python3-pyqt6.qtgui, python3-pyqt6.qtwidgets
Maintainer: Srabon Hasan <me@srabon.net>
Description: Complete SMS Management Suite for ZTE/OLAX 4G Routers
 Read, send, delete SMS with Unicode support. Features include:
  - SMS inbox management
  - Send SMS with UTF-16BE encoding
  - Real-time signal and network status
  - Router control (reboot, internet toggle)
  - WiFi settings management
  - Auto-detect router on network
Homepage: https://github.com/srabonbangali/UFI-SMS-Commander
EOF

# Create post-install script
cat > "$PACKAGE_ROOT/DEBIAN/postinst" << 'EOF'
#!/bin/bash
# Post-installation script

echo "📱 UFI SMS Commander installed successfully!"
echo ""
echo "To run: ufi-sms-commander"
echo "Or find it in your application menu"
echo ""
echo "📖 Documentation: /usr/share/doc/ufi-sms-commander/"
echo ""

# Create config directory
mkdir -p /home/$SUDO_USER/.config/ufi-sms-commander
chown $SUDO_USER:$SUDO_USER /home/$SUDO_USER/.config/ufi-sms-commander

exit 0
EOF

chmod +x "$PACKAGE_ROOT/DEBIAN/postinst"

# Create pre-remove script
cat > "$PACKAGE_ROOT/DEBIAN/prerm" << 'EOF'
#!/bin/bash
# Pre-removal script

echo "Removing UFI SMS Commander..."
echo "Your configuration files in ~/.config/ufi-sms-commander will be preserved."

exit 0
EOF

chmod +x "$PACKAGE_ROOT/DEBIAN/prerm"

# Build the package
print_info "Building .deb package..."
dpkg-deb --build "$PACKAGE_ROOT"

if [ $? -eq 0 ]; then
    # Move package to current directory
    mv "debian-build/$PACKAGE_NAME-$VERSION.deb" ./
    print_success "Package built: $PACKAGE_NAME-$VERSION.deb"
    
    # Cleanup
    rm -rf debian-build
    
    print_info "To install: sudo dpkg -i $PACKAGE_NAME-$VERSION.deb"
    print_info "To fix dependencies: sudo apt-get install -f"
else
    print_error "Failed to build package"
    exit 1
fi

print_header "🎉 Build Complete!"
ls -lh "$PACKAGE_NAME-$VERSION.deb"
