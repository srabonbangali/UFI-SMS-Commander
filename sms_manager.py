#!/home/srabonx/venv/bin/python3
# sms_manager.py - Full SMS Manager for ZTE UFI Router
# Updated with working Unicode encoding (UTF-16BE)

import os
import re
import sys
import socket
import requests
import json
import binascii
import base64
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,  # Added QGridLayout here
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QTextEdit, QLineEdit, QGroupBox, QMessageBox,
    QTabWidget, QHeaderView, QProgressBar, QStatusBar,
    QCheckBox, QComboBox, QSpinBox
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QAction

# ==================== Router Configuration ====================
# Instead of a hardcoded IP/password, connection details now live in a
# small JSON config file in the user's home directory, editable from the
# new Settings tab. This lets the same app work with any ZTE-style router
# (OLAX AX6 PRO, other ZTE UFI/MiFi models, etc.) without touching code.

CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".zte_sms_manager_config.json")

DEFAULT_CONFIG = {
    "router_ip": "192.168.150.1",   # host/IP only - no http:// prefix
    "username": "",                 # most ZTE routers don't need this; leave blank
    "password": "admin",
}

# A handful of default IPs used on ZTE/OLAX-style mobile routers and
# common home routers, tried during "Auto-Detect Router".
COMMON_ROUTER_IPS = [
    "192.168.150.1",  # ZTE/OLAX MiFi default
    "192.168.0.1",
    "192.168.1.1",
    "192.168.8.1",     # common ZTE/Huawei mobile hotspot
    "192.168.100.1",
    "10.0.0.1",
    "192.168.43.1",
]


def normalize_host(raw):
    """Strip scheme/trailing slash so users can paste a full URL or a bare IP."""
    host = (raw or "").strip()
    host = re.sub(r'^https?://', '', host, flags=re.IGNORECASE)
    host = host.rstrip('/')
    return host


def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                saved = json.load(f)
            cfg = DEFAULT_CONFIG.copy()
            cfg.update({k: v for k, v in saved.items() if k in DEFAULT_CONFIG})
            return cfg
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def save_config(cfg):
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(cfg, f, indent=2)
        return True
    except Exception:
        return False


def build_urls(router_ip):
    base = f"http://{router_ip}/goform/goform_set_cmd_process"
    get = f"http://{router_ip}/goform/goform_get_cmd_process"
    return base, get


def guess_default_gateway():
    """Best-effort guess of this machine's router IP (its default gateway)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        parts = local_ip.split(".")
        if len(parts) == 4:
            return ".".join(parts[:3] + ["1"])
    except Exception:
        pass
    return None


CONFIG = load_config()
BASE_URL, GET_URL = build_urls(CONFIG["router_ip"])

# ==================== Persistent Session ====================
# Two bugs stacked on top of each other were breaking login here:
#
# 1. The script called the module-level requests.get()/requests.post()
#    functions instead of a shared requests.Session(), so nothing was
#    reused between calls. This turned out not to matter for AUTH itself
#    (see point 3), but it's still fixed below since it's good practice
#    and needed for any future cookie-based behavior.
#
# 2. The password was sent as plain text ("admin"). This router's web UI
#    (per its own service.js) always Base64-encodes the password before
#    sending it in the LOGIN request. Sending it in plain text gets
#    silently rejected.
#
# 3. The success check was backwards. The router's real result codes
#    (also straight from service.js) are:
#       "0" or "4"  -> SUCCESS
#       "1"         -> Login Fail (generic)
#       "2"         -> duplicateUser
#       "3"         -> badPassword
#       "5"         -> badUsername
#    The old code checked for '"result":"1"' as SUCCESS, which is
#    actually the FAILURE code. Every "successful" login we ever saw
#    from this script was actually the router reporting failure.
#
# On top of that, this router authenticates by source IP rather than by
# cookie (confirmed: a session that never logged in successfully still
# showed as logged-in immediately after a different login succeeded from
# the same machine). So there's no cookie to carry - once login succeeds,
# every subsequent request from this machine's IP is treated as
# authenticated for a while.
SESSION = requests.Session()


def refresh_session_headers():
    """Re-point the shared session's Referer at whichever router is active."""
    SESSION.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "Referer": f"http://{CONFIG['router_ip']}/index.html",
        "X-Requested-With": "XMLHttpRequest",
    })


refresh_session_headers()

LOGIN_SUCCESS_CODES = ("0", "4")


def apply_router_settings(router_ip, password, username="", save=True):
    """
    Switch the app over to a different router: update CONFIG, rebuild the
    dependent BASE_URL/GET_URL globals, and refresh the session headers.
    Called from the Settings tab, and optionally persists to disk.
    """
    global BASE_URL, GET_URL
    CONFIG["router_ip"] = normalize_host(router_ip)
    CONFIG["password"] = password
    CONFIG["username"] = username
    BASE_URL, GET_URL = build_urls(CONFIG["router_ip"])
    refresh_session_headers()
    if save:
        save_config(CONFIG)


def router_login(session=None, password=None, username=None):
    """
    Real ZTE UFI login: Base64-encode the password, POST goformId=LOGIN,
    and check the result code correctly (0/4 = success).

    session/password/username default to the *current* values in CONFIG at
    call time (not at import time), so changing router settings at runtime
    is picked up immediately without restarting the app.
    """
    if session is None:
        session = SESSION
    if password is None:
        password = CONFIG["password"]
    if username is None:
        username = CONFIG.get("username", "")
    try:
        encoded_password = base64.b64encode(password.encode()).decode()
        data = {"isTest": "false", "goformId": "LOGIN", "password": encoded_password}
        if username:
            data["Username"] = username
        resp = session.post(BASE_URL, data=data, timeout=5)
        try:
            result_code = resp.json().get("result")
        except ValueError:
            return False
        return result_code in LOGIN_SUCCESS_CODES
    except requests.RequestException:
        return False

# ==================== SMS Decoder/Encoder ====================

def decode_unicode_sms(hex_string):
    """Decode Unicode SMS content (UTF-16BE)"""
    try:
        if not hex_string:
            return ""
        # Remove spaces if any
        hex_string = hex_string.strip()
        # Make sure it's valid hex
        if len(hex_string) % 2 != 0:
            hex_string = "0" + hex_string
        hex_bytes = bytes.fromhex(hex_string)
        return hex_bytes.decode('utf-16-be')
    except Exception as e:
        # Try fallback decoding
        try:
            # Try as UTF-8
            hex_bytes = bytes.fromhex(hex_string)
            return hex_bytes.decode('utf-8', errors='ignore')
        except:
            return f"[Decode Error]"

def encode_unicode_sms(text):
    """Encode text to UTF-16BE hex (4 digits per character)"""
    # Convert to UTF-16BE and get uppercase hex
    hex_string = text.encode('utf-16-be').hex().upper()
    return hex_string

# ==================== Router Auto-Detect Worker ====================

class RouterScanWorker(QThread):
    """
    Tries to find a compatible router on the network without blocking the
    UI: checks this machine's default gateway first, then a list of common
    router IPs, attempting a real login against each with the password
    the user typed in.
    """
    progress = pyqtSignal(str)
    found = pyqtSignal(str)
    not_found = pyqtSignal()

    def __init__(self, password, username=""):
        super().__init__()
        self.password = password
        self.username = username

    def run(self):
        candidates = []
        gateway = guess_default_gateway()
        if gateway:
            candidates.append(gateway)
        for ip in COMMON_ROUTER_IPS:
            if ip not in candidates:
                candidates.append(ip)

        temp_session = requests.Session()
        temp_session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
        })

        for ip in candidates:
            self.progress.emit(f"Trying {ip}...")
            temp_session.headers["Referer"] = f"http://{ip}/index.html"
            base_url = f"http://{ip}/goform/goform_set_cmd_process"
            try:
                encoded_password = base64.b64encode(self.password.encode()).decode()
                data = {"isTest": "false", "goformId": "LOGIN", "password": encoded_password}
                if self.username:
                    data["Username"] = self.username
                resp = temp_session.post(base_url, data=data, timeout=1.5)
                result_code = resp.json().get("result")
                if result_code in LOGIN_SUCCESS_CODES:
                    self.found.emit(ip)
                    return
            except Exception:
                continue

        self.not_found.emit()

# ==================== SMS Worker Thread ====================

class SMSWorker(QThread):
    """Worker thread for SMS operations"""
    
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)
    
    def __init__(self, operation, **kwargs):
        super().__init__()
        self.operation = operation
        self.kwargs = kwargs
        
    def run(self):
        try:
            if self.operation == "load_messages":
                result = self.load_messages()
            elif self.operation == "send_sms":
                result = self.send_sms()
            elif self.operation == "delete_sms":
                result = self.delete_sms()
            elif self.operation == "refresh_status":
                result = self.refresh_status()
            else:
                result = {"error": "Unknown operation"}
            
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
    
    def login(self):
        """Login to router (uses the shared, cookie-persistent SESSION)"""
        return router_login()
    
    def load_messages(self):
        """Load SMS messages from router"""
        if not self.login():
            return {"error": "Login failed"}
        
        try:
            params = {
                "isTest": "false",
                "cmd": "sms_data_total",
                "page": "0",
                "data_per_page": "500",
                "mem_store": "1",
                "tags": "10",
                "order_by": "order by id desc"
            }
            
            response = SESSION.get(GET_URL, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                messages = data.get('messages', [])
                
                # Decode all messages
                for msg in messages:
                    if msg.get('content'):
                        msg['decoded_content'] = decode_unicode_sms(msg['content'])
                
                return {"messages": messages, "count": len(messages)}
            else:
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def send_sms(self):
        """Send SMS"""
        phone = self.kwargs.get('phone', '')
        message = self.kwargs.get('message', '')
        
        if not phone or not message:
            return {"error": "Phone number and message are required"}
        
        if not self.login():
            return {"error": "Login failed"}
        
        try:
            # Encode message using working format
            encoded = encode_unicode_sms(message)
            
            # Get timestamp
            now = datetime.now()
            sms_time = f"{now.year:04d};{now.month:02d};{now.day:02d};{now.hour:02d};{now.minute:02d};{now.second:02d}"
            
            data = {
                "isTest": "false",
                "goformId": "SEND_SMS",
                "notCallback": "true",
                "Number": phone,
                "sms_time": sms_time,
                "MessageBody": encoded,
                "ID": "-1",
                "encode_type": "UNICODE",
                "AD": ""
            }
            
            response = SESSION.post(BASE_URL, data=data, timeout=10)
            
            if "success" in response.text:
                return {"success": True, "response": response.text}
            else:
                return {"error": f"Send failed: {response.text}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def delete_sms(self):
        """Delete SMS by ID"""
        sms_id = self.kwargs.get('id', '')
        
        if not sms_id:
            return {"error": "SMS ID is required"}
        
        if not self.login():
            return {"error": "Login failed"}
        
        try:
            data = {
                "goformId": "DELETE_SMS",
                "id": sms_id
            }
            
            response = SESSION.post(BASE_URL, data=data, timeout=5)
            
            if response.status_code == 200:
                return {"success": True, "response": response.text}
            else:
                return {"error": f"Delete failed: {response.status_code}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def refresh_status(self):
        """Refresh router status"""
        if not self.login():
            return {"error": "Login failed"}
        
        try:
            # Get signal and network info
            # NOTE: ZTE UFI routers only return ALL of the requested comma-
            # separated "cmd" fields if "multi_data=1" is also sent. Without
            # it, the router silently returns just a single field (usually
            # not the one you expect), which is why the Status tab looked
            # completely empty before this fix.
            cmd = "signalbar,network_type,sub_network_type,sta_count,imei,cpin,mcc,mnc,network_provider"
            params = {
                "isTest": "false",
                "cmd": cmd,
                "multi_data": "1",
            }
            response = SESSION.get(GET_URL, params=params, timeout=3)
            
            if response.status_code == 200:
                return {"status": response.json()}
            else:
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

# ==================== Main SMS Manager GUI ====================

class SMSManager(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"📱 ZTE UFI SMS Manager - {CONFIG['router_ip']}")
        self.setFixedSize(900, 700)
        
        self.messages = []
        self.is_loading = False
        self.current_status = {}
        self.scan_worker = None
        self.connected = False
        
        self.init_ui()
        
        # No auto-login on startup: the app opens on the Settings tab and
        # waits for the user to hit "Search Router" and/or "Save & Connect"
        # before it ever talks to a router. This also means a saved
        # router/password from a previous run is pre-filled but NOT used
        # until the user actively connects.
        self.status_bar.showMessage("Not connected - go to the Settings tab to connect to your router")
        
        # Auto-refresh timer is created but only started once connected
        # (see save_and_connect_router)
        self.timer = QTimer()
        self.timer.timeout.connect(self.load_messages)
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        
        # ===== Title =====
        title = QLabel("📱 ZTE UFI SMS Manager")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont("Arial", 18, QFont.Weight.Bold)
        title.setFont(title_font)
        main_layout.addWidget(title)
        
        # ===== Top Status Bar =====
        status_layout = QHBoxLayout()
        
        self.signal_label = QLabel("📶 --")
        self.signal_label.setStyleSheet("color: #888; font-size: 11px; padding: 5px;")
        status_layout.addWidget(self.signal_label)
        
        status_layout.addStretch()
        
        self.msg_count_label = QLabel("📨 0 messages")
        self.msg_count_label.setStyleSheet("color: #888; font-size: 11px; padding: 5px;")
        status_layout.addWidget(self.msg_count_label)
        
        status_layout.addStretch()
        
        self.last_update_label = QLabel("Last update: Never")
        self.last_update_label.setStyleSheet("color: #888; font-size: 10px; padding: 5px;")
        status_layout.addWidget(self.last_update_label)
        
        main_layout.addLayout(status_layout)
        
        # ===== Tabs =====
        tabs = QTabWidget()
        
        # ---- Inbox Tab ----
        inbox_tab = QWidget()
        inbox_layout = QVBoxLayout()
        
        # Toolbar
        inbox_toolbar = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_messages)
        refresh_btn.setStyleSheet("QPushButton { padding: 5px 15px; }")
        inbox_toolbar.addWidget(refresh_btn)
        
        delete_all_btn = QPushButton("🗑️ Delete All")
        delete_all_btn.clicked.connect(self.delete_all_messages)
        delete_all_btn.setStyleSheet("QPushButton { padding: 5px 15px; }")
        inbox_toolbar.addWidget(delete_all_btn)
        
        inbox_toolbar.addStretch()
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All Messages", "Received", "Sent", "Drafts"])
        self.filter_combo.currentTextChanged.connect(self.filter_messages)
        inbox_toolbar.addWidget(self.filter_combo)
        
        inbox_layout.addLayout(inbox_toolbar)
        
        # Message table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "From/To", "Date", "Content", "Type"])
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.cellDoubleClicked.connect(self.view_message)
        self.table.setStyleSheet("""
            QTableWidget::item:selected {
                background-color: #2a5c8a;
            }
        """)
        inbox_layout.addWidget(self.table)
        
        inbox_tab.setLayout(inbox_layout)
        tabs.addTab(inbox_tab, "📥 Inbox")
        
        # ---- Send SMS Tab ----
        send_tab = QWidget()
        send_layout = QVBoxLayout()
        
        send_group = QGroupBox("Compose SMS")
        send_group_layout = QVBoxLayout()
        send_group_layout.setSpacing(10)
        
        # Phone number
        number_layout = QHBoxLayout()
        number_layout.addWidget(QLabel("📞 To:"))
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("e.g., 8801841946896")
        self.phone_input.setStyleSheet("padding: 8px; font-size: 14px;")
        number_layout.addWidget(self.phone_input)
        send_group_layout.addLayout(number_layout)
        
        # Message
        send_group_layout.addWidget(QLabel("💬 Message:"))
        self.message_input = QTextEdit()
        self.message_input.setMaximumHeight(150)
        self.message_input.setStyleSheet("padding: 8px; font-size: 13px;")
        send_group_layout.addWidget(self.message_input)
        
        # Character counter
        self.char_count = QLabel("0 characters")
        self.char_count.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.char_count.setStyleSheet("color: #888; font-size: 10px;")
        send_group_layout.addWidget(self.char_count)
        self.message_input.textChanged.connect(self.update_char_count)
        
        # Options
        options_layout = QHBoxLayout()
        
        self.unicode_check = QCheckBox("Force Unicode")
        self.unicode_check.setChecked(True)
        self.unicode_check.setToolTip("Use Unicode encoding (recommended for all messages)")
        options_layout.addWidget(self.unicode_check)
        
        options_layout.addStretch()
        
        self.delivery_report = QCheckBox("Request Delivery Report")
        options_layout.addWidget(self.delivery_report)
        
        send_group_layout.addLayout(options_layout)
        
        # Send button
        send_btn = QPushButton("📤 SEND SMS")
        send_btn.clicked.connect(self.send_sms)
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border: none;
                padding: 15px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #888;
            }
        """)
        send_group_layout.addWidget(send_btn)
        
        # Send status
        self.send_status = QLabel("")
        self.send_status.setStyleSheet("padding: 5px; font-size: 12px;")
        send_group_layout.addWidget(self.send_status)
        
        send_group.setLayout(send_group_layout)
        send_layout.addWidget(send_group)
        
        # Quick templates
        templates_group = QGroupBox("Quick Templates")
        templates_layout = QHBoxLayout()
        
        templates = [
            "Hello! How are you?",
            "I'll call you later.",
            "Please call me back.",
            "Thank you!",
            "See you soon."
        ]
        
        for template in templates:
            btn = QPushButton(template[:15] + ("..." if len(template) > 15 else ""))
            btn.setToolTip(template)
            btn.clicked.connect(lambda checked, t=template: self.message_input.setText(t))
            btn.setStyleSheet("QPushButton { padding: 5px 10px; font-size: 11px; }")
            templates_layout.addWidget(btn)
        
        templates_group.setLayout(templates_layout)
        send_layout.addWidget(templates_group)
        
        send_tab.setLayout(send_layout)
        tabs.addTab(send_tab, "📤 Send SMS")
        
        # ---- Status Tab ----
        status_tab = QWidget()
        
        status_grid = QGridLayout()
        status_grid.setSpacing(10)
        
        self.status_items = {}
        status_fields = [
            ("Signal Bars", "signalbar"),
            ("Network Type", "network_type"),
            ("Sub Network", "sub_network_type"),
            ("WiFi Clients", "sta_count"),
            ("IMEI", "imei"),
            ("SIM Status", "cpin"),
            ("MCC", "mcc"),
            ("MNC", "mnc"),
            ("Provider", "network_provider"),
        ]
        
        for row, (label, key) in enumerate(status_fields):
            status_grid.addWidget(QLabel(f"{label}:"), row, 0)
            self.status_items[key] = QLabel("--")
            self.status_items[key].setStyleSheet("color: #00c8ff; font-weight: bold;")
            status_grid.addWidget(self.status_items[key], row, 1)
        
        # Manual refresh button for the status tab, and a place to surface
        # errors instead of failing silently.
        status_refresh_btn = QPushButton("🔄 Refresh Status")
        status_refresh_btn.clicked.connect(self.update_status)
        status_refresh_btn.setStyleSheet("QPushButton { padding: 5px 15px; }")
        status_grid.addWidget(status_refresh_btn, len(status_fields), 0, 1, 2)
        
        status_grid.setColumnStretch(1, 1)
        status_tab.setLayout(status_grid)
        tabs.addTab(status_tab, "📊 Status")
        
        # ---- Tools Tab ----
        tools_tab = QWidget()
        tools_layout = QVBoxLayout()
        tools_layout.setSpacing(15)
        
        # --- Router Control ---
        control_group = QGroupBox("Router Control")
        control_layout = QHBoxLayout()
        
        reboot_btn = QPushButton("🔁 Restart Router")
        reboot_btn.clicked.connect(self.restart_router)
        reboot_btn.setStyleSheet("QPushButton { padding: 10px 15px; }")
        control_layout.addWidget(reboot_btn)
        
        internet_on_btn = QPushButton("🌐 Turn Internet On")
        internet_on_btn.clicked.connect(lambda: self.toggle_internet(True))
        internet_on_btn.setStyleSheet("QPushButton { padding: 10px 15px; background-color: #2ecc71; }")
        control_layout.addWidget(internet_on_btn)
        
        internet_off_btn = QPushButton("🚫 Turn Internet Off")
        internet_off_btn.clicked.connect(lambda: self.toggle_internet(False))
        internet_off_btn.setStyleSheet("QPushButton { padding: 10px 15px; background-color: #e74c3c; }")
        control_layout.addWidget(internet_off_btn)
        
        control_group.setLayout(control_layout)
        tools_layout.addWidget(control_group)
        
        # --- WiFi Settings ---
        wifi_group = QGroupBox("WiFi Settings")
        wifi_form = QVBoxLayout()
        wifi_form.setSpacing(8)
        
        ssid_row = QHBoxLayout()
        ssid_row.addWidget(QLabel("📶 SSID:"))
        self.wifi_ssid_input = QLineEdit()
        self.wifi_ssid_input.setPlaceholderText("New WiFi name (leave blank to keep current)")
        self.wifi_ssid_input.setStyleSheet("padding: 8px;")
        ssid_row.addWidget(self.wifi_ssid_input)
        wifi_form.addLayout(ssid_row)
        
        pass_row = QHBoxLayout()
        pass_row.addWidget(QLabel("🔑 Password:"))
        self.wifi_pass_input = QLineEdit()
        self.wifi_pass_input.setPlaceholderText("New WiFi password, 8-63 chars (leave blank to keep current)")
        self.wifi_pass_input.setStyleSheet("padding: 8px;")
        pass_row.addWidget(self.wifi_pass_input)
        wifi_form.addLayout(pass_row)
        
        wifi_apply_btn = QPushButton("💾 Apply WiFi Settings")
        wifi_apply_btn.clicked.connect(self.apply_wifi_settings)
        wifi_apply_btn.setStyleSheet("QPushButton { padding: 10px; }")
        wifi_form.addWidget(wifi_apply_btn)
        
        wifi_note = QLabel(
            "⚠️ Applying WiFi settings restarts the WiFi radio - if you're connected "
            "over WiFi (not USB/Ethernet) this device will briefly disconnect."
        )
        wifi_note.setWordWrap(True)
        wifi_note.setStyleSheet("color: #888; font-size: 10px;")
        wifi_form.addWidget(wifi_note)
        
        wifi_group.setLayout(wifi_form)
        tools_layout.addWidget(wifi_group)
        
        # --- Advanced / Custom Command (for "other options") ---
        advanced_group = QGroupBox("Advanced: Custom Command")
        advanced_layout = QVBoxLayout()
        advanced_layout.setSpacing(8)
        
        advanced_info = QLabel(
            "Send any raw router command here. Handy for adding features this app "
            "doesn't have a dedicated button for yet - find the goformId/cmd name and "
            "parameters from the router's own web UI (browser DevTools → Network tab "
            "while you click the equivalent option there), then try it here."
        )
        advanced_info.setWordWrap(True)
        advanced_info.setStyleSheet("color: #888; font-size: 10px;")
        advanced_layout.addWidget(advanced_info)
        
        goform_row = QHBoxLayout()
        goform_row.addWidget(QLabel("Command:"))
        self.custom_goform_input = QLineEdit()
        self.custom_goform_input.setPlaceholderText("e.g. REBOOT_DEVICE (POST) or signalbar (GET)")
        self.custom_goform_input.setStyleSheet("padding: 8px;")
        goform_row.addWidget(self.custom_goform_input)
        advanced_layout.addLayout(goform_row)
        
        params_row = QHBoxLayout()
        params_row.addWidget(QLabel("Params:"))
        self.custom_params_input = QLineEdit()
        self.custom_params_input.setPlaceholderText("key1=value1;key2=value2 (optional)")
        self.custom_params_input.setStyleSheet("padding: 8px;")
        params_row.addWidget(self.custom_params_input)
        advanced_layout.addLayout(params_row)
        
        custom_btn_row = QHBoxLayout()
        custom_get_btn = QPushButton("📥 Send as GET (query status)")
        custom_get_btn.clicked.connect(lambda: self.send_custom_command("GET"))
        custom_btn_row.addWidget(custom_get_btn)
        
        custom_post_btn = QPushButton("📤 Send as POST (perform action)")
        custom_post_btn.clicked.connect(lambda: self.send_custom_command("POST"))
        custom_btn_row.addWidget(custom_post_btn)
        advanced_layout.addLayout(custom_btn_row)
        
        self.custom_output = QTextEdit()
        self.custom_output.setReadOnly(True)
        self.custom_output.setMaximumHeight(90)
        self.custom_output.setPlaceholderText("Raw response will appear here...")
        self.custom_output.setStyleSheet("padding: 8px; font-family: monospace; font-size: 11px;")
        advanced_layout.addWidget(self.custom_output)
        
        advanced_group.setLayout(advanced_layout)
        tools_layout.addWidget(advanced_group)
        
        tools_layout.addStretch()
        
        self.tools_status = QLabel("")
        self.tools_status.setStyleSheet("padding: 5px; font-size: 12px;")
        tools_layout.addWidget(self.tools_status)
        
        tools_tab.setLayout(tools_layout)
        tabs.addTab(tools_tab, "🛠️ Tools")
        
        # ---- Settings Tab ----
        settings_tab = QWidget()
        settings_layout = QVBoxLayout()
        settings_layout.setSpacing(15)
        
        conn_group = QGroupBox("Router Connection")
        conn_form = QVBoxLayout()
        conn_form.setSpacing(8)
        
        conn_info = QLabel(
            "Works with any ZTE-style UFI/MiFi router (OLAX AX6 PRO and similar). "
            "Search for it automatically, or enter its address and login details "
            "below - nothing connects until you press one of the buttons."
        )
        conn_info.setWordWrap(True)
        conn_info.setStyleSheet("color: #888; font-size: 10px;")
        conn_form.addWidget(conn_info)
        
        search_btn = QPushButton("🔍 Search Router")
        search_btn.clicked.connect(self.auto_detect_router)
        search_btn.setStyleSheet(
            "QPushButton { background-color: #00c8ff; color: #1e1e1e; padding: 12px; "
            "font-weight: bold; font-size: 14px; }"
        )
        conn_form.addWidget(search_btn)
        self.search_router_btn = search_btn
        
        search_note = QLabel(
            "Scans this computer's network gateway plus common router addresses, "
            "trying to log in with the password below. It won't guess the "
            "password for you - enter that first if you know it."
        )
        search_note.setWordWrap(True)
        search_note.setStyleSheet("color: #888; font-size: 10px;")
        conn_form.addWidget(search_note)
        
        manual_label = QLabel("— or enter details manually —")
        manual_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        manual_label.setStyleSheet("color: #666; font-size: 10px; padding-top: 5px;")
        conn_form.addWidget(manual_label)
        
        ip_row = QHBoxLayout()
        ip_row.addWidget(QLabel("🌐 Router Homepage:"))
        self.settings_ip_input = QLineEdit()
        self.settings_ip_input.setText(CONFIG["router_ip"])
        self.settings_ip_input.setPlaceholderText("e.g. 192.168.1.1 or http://192.168.150.1")
        self.settings_ip_input.setStyleSheet("padding: 8px;")
        ip_row.addWidget(self.settings_ip_input)
        conn_form.addLayout(ip_row)
        
        user_row = QHBoxLayout()
        user_row.addWidget(QLabel("👤 Username:"))
        self.settings_username_input = QLineEdit()
        self.settings_username_input.setText(CONFIG.get("username", ""))
        self.settings_username_input.setPlaceholderText("optional - most ZTE routers don't need one")
        self.settings_username_input.setStyleSheet("padding: 8px;")
        user_row.addWidget(self.settings_username_input)
        conn_form.addLayout(user_row)
        
        pass_row = QHBoxLayout()
        pass_row.addWidget(QLabel("🔑 Password:"))
        self.settings_password_input = QLineEdit()
        self.settings_password_input.setText(CONFIG["password"])
        self.settings_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.settings_password_input.setStyleSheet("padding: 8px;")
        pass_row.addWidget(self.settings_password_input)
        
        self.settings_show_pass = QCheckBox("Show")
        self.settings_show_pass.toggled.connect(
            lambda checked: self.settings_password_input.setEchoMode(
                QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
            )
        )
        pass_row.addWidget(self.settings_show_pass)
        conn_form.addLayout(pass_row)
        
        save_connect_btn = QPushButton("🔌 Save && Connect")
        save_connect_btn.clicked.connect(self.save_and_connect_router)
        save_connect_btn.setStyleSheet(
            "QPushButton { background-color: #2ecc71; color: white; padding: 10px; font-weight: bold; }"
        )
        conn_form.addWidget(save_connect_btn)
        
        self.settings_status = QLabel("Not connected yet")
        self.settings_status.setStyleSheet("padding: 5px; font-size: 12px; color: #888;")
        conn_form.addWidget(self.settings_status)
        
        conn_group.setLayout(conn_form)
        settings_layout.addWidget(conn_group)
        settings_layout.addStretch()
        
        settings_tab.setLayout(settings_layout)
        settings_tab_index = tabs.addTab(settings_tab, "⚙️ Settings")
        
        # ---- About Tab ----
        about_tab = QWidget()
        about_layout = QVBoxLayout()
        
        self.about_label = QLabel()
        self.about_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.about_label.setStyleSheet("color: #f0f0f0; font-size: 14px; line-height: 1.6;")
        self.refresh_about_text()
        about_layout.addWidget(self.about_label)
        
        about_tab.setLayout(about_layout)
        tabs.addTab(about_tab, "ℹ️ About")
        
        main_layout.addWidget(tabs)
        self.tabs = tabs
        tabs.setCurrentIndex(settings_tab_index)
        
        # ===== Status Bar =====
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("QStatusBar { background-color: #2b2b2b; color: #888; padding: 3px; }")
        self.status_bar.showMessage("Ready")
        main_layout.addWidget(self.status_bar)
        
        self.setLayout(main_layout)
        
        # ===== Dark Theme =====
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #f0f0f0;
                font-size: 12px;
            }
            QGroupBox {
                border: 1px solid #444;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #00c8ff;
            }
            QTableWidget {
                background-color: #2b2b2b;
                alternate-background-color: #333333;
                gridline-color: #444444;
                selection-background-color: #2a5c8a;
            }
            QHeaderView::section {
                background-color: #3a3a3a;
                padding: 8px;
                border: 1px solid #444;
                font-weight: bold;
            }
            QLineEdit, QTextEdit, QComboBox {
                background-color: #2b2b2b;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 8px;
                color: #f0f0f0;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 1px solid #00c8ff;
            }
            QTabWidget::pane {
                border: 1px solid #444;
                border-radius: 5px;
                background-color: #1e1e1e;
            }
            QTabBar::tab {
                background-color: #2b2b2b;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: #3a3a3a;
                color: #00c8ff;
            }
            QTabBar::tab:hover {
                background-color: #444;
            }
            QPushButton {
                background-color: #4a4a4a;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
            QPushButton:pressed {
                background-color: #3a3a3a;
            }
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QProgressBar {
                border: 1px solid #444;
                border-radius: 5px;
                background: #2b2b2b;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #00c8ff;
                border-radius: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: #2b2b2b;
                color: #f0f0f0;
                selection-background-color: #2a5c8a;
            }
            QScrollBar:vertical {
                background-color: #2b2b2b;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #555;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #666;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)
    
    # ==================== Methods ====================
    
    def update_char_count(self):
        """Update character counter"""
        text = self.message_input.toPlainText()
        count = len(text)
        self.char_count.setText(f"{count} characters")
        
        if count > 160:
            self.char_count.setStyleSheet("color: #e74c3c; font-size: 10px;")
        else:
            self.char_count.setStyleSheet("color: #888; font-size: 10px;")
    
    def login(self):
        """Login to router (uses the shared, cookie-persistent SESSION)"""
        return router_login()
    
    def load_messages(self):
        """Load SMS messages"""
        if self.is_loading:
            return
        
        self.is_loading = True
        self.status_bar.showMessage("Loading messages...")
        
        if not self.login():
            self.status_bar.showMessage("❌ Login failed")
            self.is_loading = False
            return
        
        try:
            params = {
                "isTest": "false",
                "cmd": "sms_data_total",
                "page": "0",
                "data_per_page": "500",
                "mem_store": "1",
                "tags": "10",
                "order_by": "order by id desc"
            }
            
            response = SESSION.get(GET_URL, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                self.messages = data.get('messages', [])
                
                # Decode messages
                for msg in self.messages:
                    if msg.get('content'):
                        msg['decoded_content'] = decode_unicode_sms(msg['content'])
                
                self.update_table()
                self.msg_count_label.setText(f"📨 {len(self.messages)} messages")
                
                # Update timestamp
                now = datetime.now()
                self.last_update_label.setText(f"Last update: {now.strftime('%H:%M:%S')}")
                self.status_bar.showMessage(f"✅ Loaded {len(self.messages)} messages")
            else:
                self.status_bar.showMessage(f"❌ Failed: HTTP {response.status_code}")
                
        except Exception as e:
            self.status_bar.showMessage(f"❌ Error: {e}")
        
        self.is_loading = False
        
        # Also update status
        self.update_status()
    
    def update_table(self):
        """Update the message table"""
        self.table.setRowCount(len(self.messages))
        
        for row, msg in enumerate(self.messages):
            # ID
            self.table.setItem(row, 0, QTableWidgetItem(str(msg.get('id', ''))))
            
            # From/To
            number = msg.get('number', 'Unknown')
            # Check if it's a sent message
            if msg.get('tag') == '2':  # Sent
                number = f"→ {number}"
            self.table.setItem(row, 1, QTableWidgetItem(number))
            
            # Date
            date_str = msg.get('date', '')
            parts = date_str.split(',')
            if len(parts) >= 6:
                year = f"20{parts[0]}" if len(parts[0]) == 2 else parts[0]
                formatted = f"{year}-{parts[1]}-{parts[2]} {parts[3]}:{parts[4]}:{parts[5]}"
                self.table.setItem(row, 2, QTableWidgetItem(formatted))
            else:
                self.table.setItem(row, 2, QTableWidgetItem(date_str))
            
            # Content
            decoded = msg.get('decoded_content', '')
            display_text = decoded[:60] + ("..." if len(decoded) > 60 else "")
            self.table.setItem(row, 3, QTableWidgetItem(display_text))
            
            # Type
            tag = msg.get('tag', '0')
            if tag == '1':
                msg_type = "📥 Received"
            elif tag == '2':
                msg_type = "📤 Sent"
            else:
                msg_type = "📄 Draft"
            self.table.setItem(row, 4, QTableWidgetItem(msg_type))
    
    def filter_messages(self, filter_text):
        """Filter messages by type"""
        # TODO: Implement filtering
        pass
    
    def view_message(self, row, col):
        """View full message content"""
        if row < len(self.messages):
            msg = self.messages[row]
            decoded = msg.get('decoded_content', '')
            number = msg.get('number', 'Unknown')
            date = msg.get('date', 'Unknown')
            msg_id = msg.get('id', 'Unknown')
            
            # Create dialog
            dialog = QMessageBox(self)
            dialog.setWindowTitle(f"SMS from {number}")
            dialog.setText(
                f"📞 From: {number}\n"
                f"🆔 ID: {msg_id}\n"
                f"📅 Date: {date}\n\n"
                f"💬 Message:\n{decoded}"
            )
            
            # Add delete button
            delete_btn = dialog.addButton("🗑️ Delete", QMessageBox.ButtonRole.ActionRole)
            dialog.addButton("Close", QMessageBox.ButtonRole.RejectRole)
            
            dialog.exec()
            
            if dialog.clickedButton() == delete_btn:
                self.delete_message(msg_id)
    
    def send_sms(self):
        """Send SMS"""
        phone = self.phone_input.text().strip()
        message = self.message_input.toPlainText().strip()
        
        if not phone or not message:
            QMessageBox.warning(self, "Error", "Please enter both phone number and message")
            return
        
        # Clean phone number
        phone = phone.replace('+', '').replace(' ', '').replace('-', '')
        
        # Confirm
        reply = QMessageBox.question(
            self,
            "Confirm Send",
            f"📤 Send SMS to {phone}?\n\n"
            f"Message: {message[:100]}{'...' if len(message) > 100 else ''}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        self.send_status.setText("⏳ Sending...")
        self.send_status.setStyleSheet("color: #f39c12;")
        self.send_status.repaint()
        
        try:
            if not self.login():
                self.send_status.setText("❌ Login failed")
                self.send_status.setStyleSheet("color: #e74c3c;")
                return
            
            # Encode message using working format
            encoded = encode_unicode_sms(message)
            
            # Get timestamp
            now = datetime.now()
            sms_time = f"{now.year:04d};{now.month:02d};{now.day:02d};{now.hour:02d};{now.minute:02d};{now.second:02d}"
            
            data = {
                "isTest": "false",
                "goformId": "SEND_SMS",
                "notCallback": "true",
                "Number": phone,
                "sms_time": sms_time,
                "MessageBody": encoded,
                "ID": "-1",
                "encode_type": "UNICODE",
                "AD": ""
            }
            
            response = SESSION.post(BASE_URL, data=data, timeout=10)
            
            if "success" in response.text:
                self.send_status.setText(f"✅ SMS sent successfully to {phone}!")
                self.send_status.setStyleSheet("color: #2ecc71;")
                self.message_input.clear()
                self.phone_input.clear()
                self.char_count.setText("0 characters")
                
                QMessageBox.information(
                    self,
                    "Success",
                    f"✅ SMS sent successfully to {phone}!\n\n"
                    "The message should arrive in a few seconds."
                )
                
                # Refresh inbox after delay
                QTimer.singleShot(3000, self.load_messages)
            else:
                self.send_status.setText(f"❌ Failed: {response.text}")
                self.send_status.setStyleSheet("color: #e74c3c;")
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to send SMS\n\nResponse: {response.text}"
                )
                
        except Exception as e:
            self.send_status.setText(f"❌ Error: {e}")
            self.send_status.setStyleSheet("color: #e74c3c;")
            QMessageBox.warning(self, "Error", f"Failed to send SMS\n\nError: {e}")
    
    def delete_message(self, sms_id):
        """Delete a single message"""
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete SMS ID {sms_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            if not self.login():
                QMessageBox.warning(self, "Error", "Login failed")
                return
            
            data = {
                "goformId": "DELETE_SMS",
                "id": sms_id
            }
            
            response = SESSION.post(BASE_URL, data=data, timeout=5)
            
            if response.status_code == 200:
                self.load_messages()
                QMessageBox.information(self, "Success", f"✅ SMS {sms_id} deleted")
            else:
                QMessageBox.warning(self, "Error", f"Delete failed: {response.status_code}")
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error: {e}")
    
    def delete_all_messages(self):
        """Delete all messages"""
        if not self.messages:
            QMessageBox.information(self, "Info", "No messages to delete")
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete All",
            f"🗑️ Delete all {len(self.messages)} messages?\n\nThis action cannot be undone!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            if not self.login():
                QMessageBox.warning(self, "Error", "Login failed")
                return
            
            # Delete one by one
            progress = QProgressBar()
            progress.setMaximum(len(self.messages))
            progress.setVisible(True)
            self.status_bar.addWidget(progress)
            
            for i, msg in enumerate(self.messages):
                msg_id = msg.get('id')
                if msg_id:
                    data = {"goformId": "DELETE_SMS", "id": msg_id}
                    SESSION.post(BASE_URL, data=data, timeout=3)
                    progress.setValue(i + 1)
                    QApplication.processEvents()
            
            self.status_bar.removeWidget(progress)
            progress.deleteLater()
            
            self.load_messages()
            QMessageBox.information(self, "Success", f"✅ Deleted all messages")
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error: {e}")
    
    def restart_router(self):
        """Reboot the router"""
        reply = QMessageBox.question(
            self,
            "Confirm Restart",
            "🔁 Restart the router now?\n\nYou'll lose connection for a minute or two while it reboots.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        self.tools_status.setText("⏳ Restarting...")
        self.tools_status.setStyleSheet("color: #f39c12;")
        self.tools_status.repaint()
        
        try:
            if not self.login():
                self.tools_status.setText("❌ Login failed")
                self.tools_status.setStyleSheet("color: #e74c3c;")
                return
            
            # Standard ZTE reboot command. If your firmware uses a different
            # goformId, check the Advanced section below to find the real one.
            data = {"isTest": "false", "goformId": "REBOOT_DEVICE"}
            response = SESSION.post(BASE_URL, data=data, timeout=5)
            self.tools_status.setText(f"✅ Restart command sent: {response.text}")
            self.tools_status.setStyleSheet("color: #2ecc71;")
        except Exception as e:
            self.tools_status.setText(f"❌ Error: {e}")
            self.tools_status.setStyleSheet("color: #e74c3c;")
    
    def toggle_internet(self, turn_on):
        """Enable or disable the mobile data / internet connection"""
        action_label = "enable" if turn_on else "disable"
        reply = QMessageBox.question(
            self,
            "Confirm",
            f"Are you sure you want to {action_label} internet access?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        self.tools_status.setText(f"⏳ Trying to {action_label} internet...")
        self.tools_status.setStyleSheet("color: #f39c12;")
        self.tools_status.repaint()
        
        try:
            if not self.login():
                self.tools_status.setText("❌ Login failed")
                self.tools_status.setStyleSheet("color: #e74c3c;")
                return
            
            # Standard ZTE mobile-data commands. Some firmware builds instead
            # use a single "goformId=SET_CONNECTION_MODE" with
            # "ConnectionMode"="0" (auto) / "1" (manual) / "2" (disabled) -
            # if this pair doesn't work on your router, try that combo via
            # the Advanced section below.
            goform_id = "CONNECT_NETWORK" if turn_on else "DISCONNECT_NETWORK"
            data = {"isTest": "false", "goformId": goform_id}
            response = SESSION.post(BASE_URL, data=data, timeout=5)
            self.tools_status.setText(f"✅ Tried to {action_label} internet: {response.text}")
            self.tools_status.setStyleSheet("color: #2ecc71;")
        except Exception as e:
            self.tools_status.setText(f"❌ Error: {e}")
            self.tools_status.setStyleSheet("color: #e74c3c;")
    
    def apply_wifi_settings(self):
        """Change WiFi SSID and/or password"""
        ssid = self.wifi_ssid_input.text().strip()
        password = self.wifi_pass_input.text().strip()
        
        if not ssid and not password:
            QMessageBox.warning(self, "Error", "Enter a new SSID and/or password first")
            return
        
        if password and len(password) < 8:
            QMessageBox.warning(self, "Error", "WiFi password must be at least 8 characters")
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm",
            "Apply these WiFi settings? This will restart the WiFi radio.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        self.tools_status.setText("⏳ Applying WiFi settings...")
        self.tools_status.setStyleSheet("color: #f39c12;")
        self.tools_status.repaint()
        
        try:
            if not self.login():
                self.tools_status.setText("❌ Login failed")
                self.tools_status.setStyleSheet("color: #e74c3c;")
                return
            
            # Common ZTE WiFi config fields - naming varies quite a bit
            # between firmware builds. If SSID/password don't actually
            # change, open your router's web UI, change WiFi settings there
            # with DevTools' Network tab open, and use the real
            # goformId/params via the Advanced section below.
            data = {
                "isTest": "false",
                "goformId": "SET_WIFI_INFO",
                "notCallback": "true",
                "AuthMode": "WPA2PSK",
                "EncrypType": "AES",
            }
            if ssid:
                data["WifiName"] = ssid
                data["SSID"] = ssid
            if password:
                data["WifiPwd"] = password
                data["WPAPSK1"] = password
            
            response = SESSION.post(BASE_URL, data=data, timeout=5)
            self.tools_status.setText(f"✅ WiFi settings sent: {response.text}")
            self.tools_status.setStyleSheet("color: #2ecc71;")
        except Exception as e:
            self.tools_status.setText(f"❌ Error: {e}")
            self.tools_status.setStyleSheet("color: #e74c3c;")
    
    def send_custom_command(self, method):
        """Send an arbitrary router command - for options not built in yet"""
        command = self.custom_goform_input.text().strip()
        raw_params = self.custom_params_input.text().strip()
        
        if not command:
            QMessageBox.warning(self, "Error", "Enter a command name first")
            return
        
        extra_params = {}
        if raw_params:
            for pair in raw_params.split(";"):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    extra_params[k.strip()] = v.strip()
        
        self.custom_output.setPlainText("⏳ Sending...")
        QApplication.processEvents()
        
        try:
            if not self.login():
                self.custom_output.setPlainText("❌ Login failed")
                return
            
            if method == "GET":
                params = {"isTest": "false", "cmd": command, **extra_params}
                response = SESSION.get(GET_URL, params=params, timeout=5)
            else:
                data = {"isTest": "false", "goformId": command, **extra_params}
                response = SESSION.post(BASE_URL, data=data, timeout=5)
            
            self.custom_output.setPlainText(response.text)
        except Exception as e:
            self.custom_output.setPlainText(f"❌ Error: {e}")
    
    def refresh_about_text(self):
        """(Re)build the About tab text - called on startup and after router changes"""
        self.about_label.setText(
            "📱 ZTE UFI SMS Manager\n\n"
            "Version: 2.0\n"
            f"Router: {CONFIG['router_ip']}\n"
            f"Python: {sys.version.split()[0]}\n\n"
            "Features:\n"
            "• Read SMS messages\n"
            "• Send SMS messages\n"
            "• Delete SMS messages\n"
            "• Auto-refresh inbox\n"
            "• SMS templates\n"
            "• Unicode support\n"
            "• Works with any ZTE-style router (configurable in Settings)\n\n"
            "Made with ❤️ for ZTE UFI routers\n\n"
            "Developed by Srabon Hasan\n"
            "me@srabon.net\n"
            "https://srabon.net"
        )
    
    def save_and_connect_router(self):
        """Apply the router address/username/password from the Settings tab"""
        router_ip = self.settings_ip_input.text().strip()
        username = self.settings_username_input.text().strip()
        password = self.settings_password_input.text()
        
        if not router_ip:
            QMessageBox.warning(self, "Error", "Enter a router address first")
            return
        
        self.settings_status.setText("⏳ Connecting...")
        self.settings_status.setStyleSheet("color: #f39c12;")
        self.settings_status.repaint()
        
        # Try the new settings before committing to them, so a typo doesn't
        # silently lock the app out of the router it was already talking to.
        normalized_ip = normalize_host(router_ip)
        test_base_url = f"http://{normalized_ip}/goform/goform_set_cmd_process"
        try:
            encoded_password = base64.b64encode(password.encode()).decode()
            data = {"isTest": "false", "goformId": "LOGIN", "password": encoded_password}
            if username:
                data["Username"] = username
            resp = SESSION.post(test_base_url, data=data, timeout=5)
            result_code = resp.json().get("result")
            success = result_code in LOGIN_SUCCESS_CODES
        except Exception as e:
            success = False
            self.settings_status.setText(f"❌ Couldn't reach {normalized_ip}: {e}")
            self.settings_status.setStyleSheet("color: #e74c3c;")
            reply = QMessageBox.question(
                self,
                "Save anyway?",
                f"Couldn't confirm a login at {normalized_ip}.\n\n"
                "Save these settings anyway? (useful if the router is just offline right now)",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            apply_router_settings(router_ip, password, username)
            self.setWindowTitle(f"📱 ZTE UFI SMS Manager - {CONFIG['router_ip']}")
            self.refresh_about_text()
            return
        
        apply_router_settings(router_ip, password, username)
        self.setWindowTitle(f"📱 ZTE UFI SMS Manager - {CONFIG['router_ip']}")
        self.refresh_about_text()
        
        if success:
            self.connected = True
            self.settings_status.setText(f"✅ Connected to {CONFIG['router_ip']} and saved")
            self.settings_status.setStyleSheet("color: #2ecc71;")
            self.status_bar.showMessage(f"✅ Connected to {CONFIG['router_ip']}")
            if not self.timer.isActive():
                self.timer.start(30000)
            self.load_messages()
        else:
            self.settings_status.setText(
                f"⚠️ Saved {CONFIG['router_ip']}, but login failed - check the password"
            )
            self.settings_status.setStyleSheet("color: #f39c12;")
    
    def auto_detect_router(self):
        """Scan the network for a compatible router in the background"""
        password = self.settings_password_input.text() or "admin"
        username = self.settings_username_input.text().strip()
        
        self.search_router_btn.setEnabled(False)
        self.settings_status.setText("🔍 Scanning for routers...")
        self.settings_status.setStyleSheet("color: #f39c12;")
        
        self.scan_worker = RouterScanWorker(password, username)
        self.scan_worker.progress.connect(
            lambda msg: self.settings_status.setText(f"🔍 {msg}")
        )
        self.scan_worker.found.connect(self.on_router_found)
        self.scan_worker.not_found.connect(self.on_router_not_found)
        self.scan_worker.start()
    
    def on_router_found(self, ip):
        self.search_router_btn.setEnabled(True)
        self.settings_ip_input.setText(ip)
        self.settings_status.setText(f"✅ Found a router at {ip} - click Save & Connect to use it")
        self.settings_status.setStyleSheet("color: #2ecc71;")
    
    def on_router_not_found(self):
        self.search_router_btn.setEnabled(True)
        self.settings_status.setText(
            "❌ No router found automatically with that password - enter the address manually"
        )
        self.settings_status.setStyleSheet("color: #e74c3c;")
    
    def update_status(self):
        """Update status tab"""
        try:
            if not self.login():
                self.status_bar.showMessage("❌ Status update: login failed")
                return
            
            # NOTE: ZTE UFI routers only return ALL of the requested comma-
            # separated "cmd" fields when "multi_data=1" is also sent.
            # Without it, the router either returns just one field or an
            # empty/partial payload, which is why every label in this tab
            # was stuck on "--" before this fix.
            cmd = "signalbar,network_type,sub_network_type,sta_count,imei,cpin,mcc,mnc,network_provider"
            params = {
                "isTest": "false",
                "cmd": cmd,
                "multi_data": "1",
            }
            response = SESSION.get(GET_URL, params=params, timeout=3)
            
            if response.status_code == 200:
                data = response.json()
                self.current_status = data
                
                # Update status items
                for key, value in data.items():
                    if key in self.status_items:
                        display_value = value if value not in (None, "") else "--"
                        self.status_items[key].setText(str(display_value))
                
                # Update signal bar visual
                signalbar = data.get('signalbar', '0')
                try:
                    bars = int(signalbar)
                    bar_display = "█" * bars + "░" * (5 - bars)
                    self.signal_label.setText(f"📶 {bar_display} ({bars}/5)")
                except:
                    self.signal_label.setText(f"📶 {signalbar}/5")
            else:
                self.status_bar.showMessage(f"❌ Status update failed: HTTP {response.status_code}")
                
        except Exception as e:
            # Surface the error instead of silently swallowing it, so a
            # broken status fetch is visible instead of just leaving every
            # field blank with no explanation.
            self.status_bar.showMessage(f"⚠️ Status update error: {e}")

# ==================== Main ====================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = SMSManager()
    window.show()
    
    sys.exit(app.exec())
