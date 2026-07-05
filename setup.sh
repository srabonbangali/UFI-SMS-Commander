#!/bin/bash

# UFI SMS Commander - Installation Script
# Compatible with Linux, macOS, and Windows (via Git Bash/WSL)

set -e  # Exit on error

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored messages
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo ""
    echo "============================================"
    echo -e "${BLUE}$1${NC}"
    echo "============================================"
    echo ""
}

# Start installation
clear
print_header "📱 UFI SMS Commander - Installation Script"
echo "This script will install all dependencies and set up the application."
echo ""

# Detect operating system
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        OS="windows"
    else
        OS="unknown"
    fi
    print_info "Detected OS: $OS"
}

detect_os

# Check for Python
check_python() {
    print_info "Checking Python installation..."
    
    if command -v python3 &>/dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &>/dev/null; then
        PYTHON_CMD="python"
    else
        print_error "Python 3.8+ is required but not found."
        print_info "Please install Python from https://python.org"
        exit 1
    fi
    
    # Check Python version
    PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [[ $PYTHON_MAJOR -lt 3 ]] || [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -lt 8 ]]; then
        print_error "Python 3.8+ is required (found $PYTHON_VERSION)"
        print_info "Please upgrade Python from https://python.org"
        exit 1
    fi
    
    print_success "Python $PYTHON_VERSION found at $(which $PYTHON_CMD)"
}

check_python

# Check for pip
check_pip() {
    print_info "Checking pip installation..."
    
    if ! command -v pip &>/dev/null && ! command -v pip3 &>/dev/null; then
        print_warning "pip not found. Installing pip..."
        $PYTHON_CMD -m ensurepip --upgrade
    fi
    
    if command -v pip3 &>/dev/null; then
        PIP_CMD="pip3"
    else
        PIP_CMD="pip"
    fi
    
    print_success "pip found"
}

check_pip

# Create virtual environment (optional)
setup_venv() {
    print_info "Would you like to install in a virtual environment? (Recommended)"
    echo "  [Y]es - Create a virtual environment"
    echo "  [N]o  - Install globally"
    read -p "Choice (Y/n): " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        USE_VENV=false
        print_info "Installing globally..."
    else
        USE_VENV=true
        print_info "Creating virtual environment..."
        
        $PYTHON_CMD -m venv venv
        if [ $? -ne 0 ]; then
            print_warning "Failed to create virtual environment. Installing globally..."
            USE_VENV=false
        else
            print_success "Virtual environment created"
            
            # Activate based on OS
            if [[ "$OS" == "windows" ]]; then
                source venv/Scripts/activate
            else
                source venv/bin/activate
            fi
            
            print_success "Virtual environment activated"
        fi
    fi
}

setup_venv

# Install dependencies
install_dependencies() {
    print_header "📦 Installing Dependencies"
    
    # Upgrade pip first
    print_info "Upgrading pip..."
    $PYTHON_CMD -m pip install --upgrade pip
    
    # Install requirements
    if [ -f "requirements.txt" ]; then
        print_info "Installing from requirements.txt..."
        $PYTHON_CMD -m pip install -r requirements.txt
        
        if [ $? -eq 0 ]; then
            print_success "Dependencies installed successfully"
        else
            print_error "Failed to install dependencies"
            print_info "Trying manual installation..."
            
            # Fallback to manual installation
            $PYTHON_CMD -m pip install PyQt6 requests
            if [ $? -eq 0 ]; then
                print_success "Manual installation succeeded"
            else
                print_error "Manual installation failed"
                exit 1
            fi
        fi
    else
        print_warning "requirements.txt not found. Installing manually..."
        $PYTHON_CMD -m pip install PyQt6 requests
    fi
}

install_dependencies

# Create config directory
create_config_dir() {
    print_header "📁 Creating Configuration Directory"
    
    CONFIG_DIR="$HOME/.config/ufi-sms-commander"
    mkdir -p "$CONFIG_DIR"
    print_success "Config directory created at: $CONFIG_DIR"
}

create_config_dir

# Create desktop entry (Linux only)
create_desktop_entry() {
    if [[ "$OS" == "linux" ]]; then
        print_header "🖥️  Creating Desktop Entry"
        
        # Get absolute path
        SCRIPT_DIR="$(pwd)"
        
        if [[ "$USE_VENV" == true ]]; then
            EXEC_PATH="$SCRIPT_DIR/venv/bin/python3 $SCRIPT_DIR/sms_manager.py"
        else
            EXEC_PATH="$PYTHON_CMD $SCRIPT_DIR/sms_manager.py"
        fi
        
        # Create .desktop file
        DESKTOP_FILE="$HOME/.local/share/applications/ufi-sms-commander.desktop"
        
        # Check if .local/share/applications exists
        mkdir -p "$HOME/.local/share/applications"
        
        cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Name=UFI SMS Commander
Comment=Manage SMS on ZTE/OLAX 4G routers
Exec=$EXEC_PATH
Icon=network-wireless
Terminal=false
Type=Application
Categories=Network;Utility;
StartupNotify=true
EOF
        
        if [ $? -eq 0 ]; then
            print_success "Desktop entry created at: $DESKTOP_FILE"
            print_info "You can now find 'UFI SMS Commander' in your application menu"
        else
            print_warning "Failed to create desktop entry"
        fi
    elif [[ "$OS" == "macos" ]]; then
        print_info "macOS: You can create an application shortcut manually"
    else
        print_info "Windows: Create a shortcut to sms_manager.py if needed"
    fi
}

create_desktop_entry

# Create start script
create_start_script() {
    print_header "📝 Creating Start Script"
    
    START_SCRIPT="start_ufi_sms.sh"
    
    cat > "$START_SCRIPT" << EOF
#!/bin/bash
# UFI SMS Commander - Quick Start Script

# Get the directory where this script is located
DIR="\$( cd "\$( dirname "\${BASH_SOURCE[0]}" )" && pwd )"

# Run the application
if [ -d "\$DIR/venv" ]; then
    source "\$DIR/venv/bin/activate"
    python3 "\$DIR/sms_manager.py"
else
    python3 "\$DIR/sms_manager.py"
fi
EOF
    
    chmod +x "$START_SCRIPT"
    print_success "Start script created: $START_SCRIPT"
}

create_start_script

# Check for required system packages (Linux only)
check_system_packages() {
    if [[ "$OS" == "linux" ]]; then
        print_header "🔍 Checking System Packages"
        
        # Check for Qt dependencies
        if ! ldconfig -p | grep -q libQt5Core; then
            print_warning "Some Qt libraries may be missing"
            print_info "On Ubuntu/Debian, install: sudo apt-get install libqt5core5a libqt5gui5 libqt5widgets5"
            print_info "On Fedora/RHEL, install: sudo dnf install qt5-qtbase"
        fi
        
        # Check for X11 (for GUI)
        if [[ -z "$DISPLAY" ]] && [[ -z "$WAYLAND_DISPLAY" ]]; then
            print_warning "No display server detected. The GUI may not work."
            print_info "If you're on a headless system, consider using X11 forwarding."
        fi
    fi
}

check_system_packages

# Final summary
print_header "🎉 Installation Complete!"

echo "┌────────────────────────────────────────────────────────────┐"
echo "│  📱 UFI SMS Commander has been installed successfully!   │"
echo "│                                                            │"
echo "│  To run the application:                                  │"
echo "│                                                            │"
if [[ "$USE_VENV" == true ]]; then
    echo "│     source venv/bin/activate                            │"
    echo "│     python3 sms_manager.py                              │"
else
    echo "│     python3 sms_manager.py                              │"
fi
echo "│                                                            │"
echo "│  Or use the quick start script:                           │"
echo "│     ./start_ufi_sms.sh                                   │"
echo "│                                                            │"
echo "│  📖 Documentation:                                        │"
echo "│     docs/API.md                                           │"
echo "│     docs/TROUBLESHOOTING.md                               │"
echo "│     docs/COMPATIBLE_DEVICES.md                            │"
echo "│                                                            │"
echo "│  📧 Need help? Contact: me@srabon.net                     │"
echo "│  🐙 Report issues: https://github.com/srabonbangali/     │"
echo "│                          UFI-SMS-Commander/issues          │"
echo "│                                                            │"
echo "│  ⭐ Don't forget to star the repository!                   │"
echo "└────────────────────────────────────────────────────────────┘"
echo ""

# Ask if user wants to run the app
read -p "Do you want to run UFI SMS Commander now? (Y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo ""
    print_info "Starting UFI SMS Commander..."
    
    # Activate virtual environment if used
    if [[ "$USE_VENV" == true ]]; then
        if [[ "$OS" == "windows" ]]; then
            source venv/Scripts/activate
        else
            source venv/bin/activate
        fi
    fi
    
    # Run the app
    $PYTHON_CMD sms_manager.py
fi

echo ""
print_success "Thanks for installing UFI SMS Commander!"
