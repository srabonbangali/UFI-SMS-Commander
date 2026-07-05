# 📱 UFI SMS Commander

### Complete SMS Management Suite for ZTE/OLAX 4G Routers

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20Windows%20%7C%20macOS-lightgrey.svg)]()

> **Built from scratch by a curious guy who believes in making tech accessible!**

---

## 🌟 Why I Built This

I needed a simple way to manage SMS on my 4G router without the clunky web interface. After hours of tinkering, reading router APIs, and many cups of tea, this tool was born. It's designed for anyone who wants to:
- **Read SMS** without logging into the router's web UI
- **Send messages** quickly from their desktop
- **Monitor signal strength** and network status
- **Control their router** with a few clicks

No coding experience needed - just download and run!

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📨 **Read SMS** | View, filter, and organize messages with proper Unicode support |
| 📤 **Send SMS** | Send messages with UTF-16BE encoding (works with Bangla, Arabic, etc.) |
| 🗑️ **Bulk Operations** | Delete single messages or clear your entire inbox |
| 📊 **Real-time Status** | Signal strength, network type, SIM status, IMEI, and more |
| 🔄 **Auto-Refresh** | Automatic inbox updates every 30 seconds |
| 🌐 **Multi-Router Support** | Works with various ZTE and OLAX models |
| 🎨 **Modern UI** | Clean dark theme with intuitive tabbed interface |
| 🔍 **Auto-Detect** | Automatically finds your router on the network |
| 📝 **Quick Templates** | Pre-defined message templates for common replies |
| 🛠️ **Advanced Tools** | Reboot router, toggle internet, change WiFi settings |
| ⚙️ **Custom Commands** | Send any router command for advanced users |

---

## 🖥️ Quick Preview

```
┌──────────────────────────────────────────────────────────┐
│  📱 UFI SMS Commander - 192.168.150.1                   │
│  📶 ████░ (4/5)           📨 12 messages               │
│  ┌────────────────────────────────────────────────────┐ │
│  │ 📥 Inbox  📤 Send  📊 Status  🛠️ Tools  ⚙️ Settings │ │
│  ├────────────────────────────────────────────────────┤ │
│  │ [Refresh] [Delete All]           [Filter: All ▼]   │ │
│  │ ┌────┬─────────────┬──────────┬──────────┬──────┐ │ │
│  │ │ ID │ From/To     │ Date     │ Content  │ Type │ │ │
│  │ ├────┼─────────────┼──────────┼──────────┼──────┤ │ │
│  │ │ 45 │ +8801841... │ 2026-07-│ Hello!   │ 📥  │ │ │
│  │ │    │             │ 05 14:30│ How are  │     │ │ │
│  │ │    │             │         │ you?     │     │ │ │
│  │ └────┴─────────────┴──────────┴──────────┴──────┘ │ │
│  └────────────────────────────────────────────────────┘ │
│  Ready                                                │
└──────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- A compatible 4G router (see list below)
- Your router's IP address and password

### One-Click Install (Linux/macOS)

```bash
# Clone the repository
git clone https://github.com/srabonbangali/UFI-SMS-Commander.git
cd UFI-SMS-Commander

# Make the setup script executable and run it
chmod +x setup.sh
./setup.sh
```

### Manual Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python3 sms_manager.py
```

### Windows Users

1. Install Python from [python.org](https://python.org)
2. Open Command Prompt as Administrator
3. Run:
```cmd
pip install -r requirements.txt
python sms_manager.py
```

---

## 🎯 First Run Guide

1. **Open the app** - It starts on the Settings tab
2. **Enter your router details**:
   - Router IP (default: `192.168.150.1`)
   - Password (default: `admin`)
   - Username (leave blank for most routers)
3. **Click "Search Router"** to auto-detect, or **"Save & Connect"**
4. **Start managing your SMS!** 🎉

---

## 📡 Compatible Routers

### ✅ Tested & Confirmed Working

| Brand | Model | Type | Status |
|-------|-------|------|--------|
| **OLAX** | AX6 PRO | 4G Router | ✅ Fully compatible |
| **ZTE** | MF79U | USB Dongle | ✅ Works perfectly |
| **ZTE** | MF253M | 4G Router | ✅ All features work |
| **ZTE** | MF823L | USB Dongle | ✅ SMS working |
| **ZTE** | MF266 | 4G Router | ✅ Full support |
| **ZTE** | MF283+ | 4G Router | ✅ SMS commands work |
| **ZTE** | MF90 (Beeline B10) | Mobile Hotspot | ✅ Fully supported |
| **ZTE** | MF920V | Mobile Hotspot | ✅ All features work |
| **ZTE** | MF286 | 4G Router | ✅ Complete support |
| **ZTE** | D1001 | Industrial Router | ✅ SMS management |
| **ZTE** | D1002 | Industrial Router | ✅ SMS management |

### 🔍 Likely Compatible

- Any ZTE router with a `/goform/` web interface
- Most ZTE mobile hotspots (MF series)
- OEM/rebranded devices using ZTE firmware
- Huawei E series (some models)

> **Not sure if your router works?** Use the auto-detect feature in Settings!

---

## 🎮 Using the App

### 📥 Inbox Tab
- **View messages** - All SMS appear in a sortable table
- **Double-click** any message to see full content
- **Delete** individual messages or clear all
- **Filter** by type (Received/Sent/Drafts)
- **Auto-refresh** every 30 seconds

### 📤 Send SMS Tab
1. Enter phone number (international format, e.g., `8801841946896`)
2. Type your message (supports Bangla, Arabic, all languages)
3. Click **"SEND SMS"**
4. You'll get confirmation when sent!

### 📊 Status Tab
- Signal strength (bars)
- Network type (4G/3G/2G)
- WiFi client count
- IMEI number
- SIM status
- Network provider

### 🛠️ Tools Tab
- **Restart Router** - Reboot your device
- **Internet Control** - Turn data on/off
- **WiFi Settings** - Change SSID and password
- **Custom Commands** - For advanced users

---

## ❓ Common Questions

### "Can this send Bangla SMS?"
**Yes!** The app uses UTF-16BE encoding which supports Bangla, Arabic, Hindi, and all Unicode languages.

### "Is my data safe?"
**Yes!** All communication stays within your local network. Passwords are not stored in plain text.

### "Do I need to be a programmer?"
**No!** Just download, install, and run. Everything has a friendly interface.

### "Will this work with my router?"
If your router has a web interface at an IP like `192.168.150.1`, it will likely work. Try the auto-detect feature!

### "What if something doesn't work?"
Check the [Troubleshooting Guide](docs/TROUBLESHOOTING.md) or open an issue on GitHub.

---

## 🐛 Troubleshooting

### Common Issues Quick Fix

| Problem | Solution |
|---------|----------|
| "Login failed" | Check IP and password (default: `admin`) |
| "Cannot connect" | Ensure router is powered on and connected |
| "No messages" | Click Refresh or wait for auto-refresh |
| "Can't send SMS" | Check phone number format and SIM balance |

**Detailed help**: See [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

---

## 🛠️ For Developers

### Project Structure
```
UFI-SMS-Commander/
├── sms_manager.py          # Main application
├── requirements.txt        # Python dependencies
├── setup.sh               # Installation script
├── docs/
│   ├── API.md             # API documentation
│   ├── TROUBLESHOOTING.md # Troubleshooting guide
│   └── COMPATIBLE_DEVICES.md # Router compatibility list
└── screenshots/           # Application screenshots
```

### Building from Source
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Create standalone executable
pyinstaller --onefile --windowed --name="UFI-SMS-Commander" sms_manager.py
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 About the Author

**Srabon Hasan**
- 🎯 "Just a curious guy! I am not a coder, but I build stuff from scratch!"
- 🌐 Website: [https://srabon.net](https://srabon.net)
- 📧 Email: me@srabon.net
- 🐙 GitHub: [@srabonbangali](https://github.com/srabonbangali)

---

## 🙏 Acknowledgments

- **PyQt6** for the beautiful UI framework
- **ZTE** for making routers with accessible APIs
- **Open-source community** for inspiration and support
- **You** for using this tool! ❤️

---

## 🌟 Support the Project

If you find this tool useful:
- ⭐ **Star the repository** on GitHub
- 📣 **Share** it with friends who have 4G routers
- 🐛 **Report issues** to help improve it
- 💡 **Suggest features** you'd like to see

---

## 📞 Get Help

- **GitHub Issues**: [Report a bug](https://github.com/srabonbangali/UFI-SMS-Commander/issues)
- **GitHub Discussions**: [Ask questions](https://github.com/srabonbangali/UFI-SMS-Commander/discussions)
- **Email**: me@srabon.net

---

## 📊 Version History

| Version | Date | Changes |
|---------|------|---------|
| v2.0 | July 2026 | Complete rewrite with PyQt6, Unicode support, auto-detect |
| v1.0 | 2025 | Initial release (CLI only) |

---

## 🔮 Future Plans

- [ ] Message search functionality
- [ ] SMS backup/export
- [ ] Scheduled SMS sending
- [ ] Contact management
- [ ] Multi-language support
- [ ] Mobile-friendly version

---

**Made with ❤️ for everyone who just wants their router SMS to work properly**

---

> *"I am not a coder, but I build stuff from scratch!"* — Srabon Hasan
