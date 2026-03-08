import re
import json
import tempfile
import os
import sys
import shutil
import subprocess
import time
from datetime import datetime, timedelta
from threading import Thread
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import seaborn as sns
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QWidget, QLabel, QTabWidget, QMenuBar, QToolBar, QDialog, QFormLayout,
    QDialogButtonBox, QCheckBox, QHeaderView, QTextEdit , QVBoxLayout, QPushButton
)
from PyQt6.QtGui import QIcon, QAction
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtCore import QTimer
from PyQt6.QtCore import pyqtSignal, QObject
import difflib
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QSplitter
import re
from pathlib import Path
# import yaml   # optional: only if you already use pyyaml; if not present we build YAML manually below
import textwrap
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QToolButton, QSizePolicy
from PyQt6.QtGui import QFont, QPalette, QColor
from PyQt6.QtCore import Qt


# ---------- Runtime hardening helpers ----------
import json
from pathlib import Path

def apply_modern_dark_theme(app):
    """
    Call once with the QApplication instance to enable a modern dark theme + stylesheet.
    Example: apply_modern_dark_theme(app)
    """
    # 1) Use Fusion style and dark palette
    app.setStyle("Fusion")
    palette = QPalette()

    # base colors
    base = QColor(18, 18, 20)
    alt_base = QColor(28, 28, 30)
    text = QColor(235, 235, 240)
    disabled_text = QColor(150, 150, 150)
    mid = QColor(60, 60, 70)
    highlight = QColor(85, 170, 255)

    palette.setColor(QPalette.ColorRole.Window, base)
    palette.setColor(QPalette.ColorRole.WindowText, text)
    palette.setColor(QPalette.ColorRole.Base, QColor(22, 22, 24))
    palette.setColor(QPalette.ColorRole.AlternateBase, alt_base)
    palette.setColor(QPalette.ColorRole.ToolTipBase, text)
    palette.setColor(QPalette.ColorRole.ToolTipText, text)
    palette.setColor(QPalette.ColorRole.Text, text)
    palette.setColor(QPalette.ColorRole.Button, QColor(30, 30, 34))
    palette.setColor(QPalette.ColorRole.ButtonText, text)
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.ColorRole.Highlight, highlight)
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.Link, QColor(100, 160, 255))
    # Qt6: Set disabled text color using setColorGroup() or setColor() with disabled brush
    palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, disabled_text)

    app.setPalette(palette)

    # 2) Global font tweaks
    font = QFont("Segoe UI", 9)  # fallback to system font if not present
    app.setFont(font)

    # 3) Stylesheet: rounded cards, nice buttons, modern tabs, refined table
    stylesheet = """
    /* Container main window */
    QMainWindow {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                    stop:0 #121214, stop:1 #0f0f10);
    }

    /* Toolbar styling */
    QToolBar {
        spacing: 8px;
        padding: 6px;
        background: transparent;
        border: none;
    }
    /* Strong QToolButton rules to guarantee visible labels */
    QToolButton {
        background: transparent !important;
        color: #E9EEF7 !important;                /* default readable color */
        padding: 6px !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 11px !important;
        qproperty-iconSize: 28px 28px;           /* hint for some Qt builds */
    }

    /* Hover — force highest contrast */
    QToolButton:hover {
        background: rgba(255,255,255,0.04) !important;
        color: #FFFFFF !important;                /* force white on hover */
        text-shadow: 0 1px 0 rgba(0,0,0,0.6) !important;
    }

    /* Pressed — keep label visible */
    QToolButton:pressed {
        background: rgba(255,255,255,0.07) !important;
        color: #FFFFFF !important;
    }

    /* Disabled */
    QToolButton:disabled {
        color: rgba(255,255,255,0.34) !important;
    }

    /* Ensure text-under-icon style keeps label visible */
    QToolButton[toolButtonStyle="2"],
    QToolButton[toolButtonStyle="Qt::ToolButtonTextUnderIcon"] {
        color: #E9EEF7 !important;
    }
    QToolButton[toolButtonStyle="2"]:hover,
    QToolButton[toolButtonStyle="Qt::ToolButtonTextUnderIcon"]:hover {
        color: #FFFFFF !important;
    }


    /* Tabs */
    QTabBar::tab {
        background: transparent;
        padding: 10px 14px;
        margin: 2px;
        border-radius: 8px;
        color: #dfe7ef;
    }
    QTabBar::tab:selected {
        background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 rgba(85,170,255,0.12), stop:1 rgba(85,170,255,0.06));
        color: white;
        font-weight: 600;
    }

    /* Card-like widgets */
    QWidget#card {
        background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                                    stop:0 rgba(255,255,255,0.02),
                                    stop:1 rgba(255,255,255,0.01));
        border: 1px solid rgba(255,255,255,0.03);
        border-radius: 10px;
        padding: 10px;
    }

    /* Table styling */
    QTableWidget {
        background: transparent;
        border: 1px solid rgba(255,255,255,0.03);
        gridline-color: rgba(255,255,255,0.03);
        selection-background-color: rgba(85,170,255,0.13);
        selection-color: white;
        alternate-background-color: rgba(255,255,255,0.01);
    }
    QHeaderView::section {
        background: rgba(255,255,255,0.02);
        padding: 8px;
        border: none;
        color: #cfd8e6;
    }

    /* QTextEdit / Logs */
    QTextEdit {
        background: #0f1113;
        border: 1px solid rgba(255,255,255,0.03);
        border-radius: 8px;
        padding: 8px;
        color: #e6eef8;
    }

    /* Buttons */
    QPushButton {
        background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #5aa8ff, stop:1 #2f7fdc);
        color: white;
        padding: 8px 12px;
        border-radius: 10px;
        border: none;
        font-weight: 600;
    }
    QPushButton:disabled {
        background: rgba(200,200,200,0.08);
        color: rgba(255,255,255,0.4);
    }
    QPushButton:hover {
        transform: none;
        filter: brightness(1.05);
    }

    /* Dialogs */
    QDialog {
        background: transparent;
    }

    /* Figure canvas border */
    FigureCanvasQTAgg, QWidget#plotCard {
        border-radius: 10px;
        border: 1px solid rgba(255,255,255,0.03);
        background: #0c0d0e;
    }
    """

    app.setStyleSheet(stylesheet)



def inspect_container_runtime(container_id, timeout=10):
    """
    Returns the parsed docker inspect dictionary for the container.
    Raises RuntimeError on failure.
    """
    try:
        proc = subprocess.run(
            ["docker", "inspect", container_id],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout
        )
    except Exception as e:
        raise RuntimeError(f"docker inspect failed: {e}")

    if proc.returncode != 0:
        raise RuntimeError(f"docker inspect error: {proc.stderr.strip() or proc.stdout.strip()}")

    try:
        data = json.loads(proc.stdout)
        if isinstance(data, list) and len(data) > 0:
            return data[0]
        return data
    except Exception as e:
        raise RuntimeError(f"Failed to parse docker inspect JSON: {e}")

def build_runtime_suggestions_and_override(inspect_json):
    """
    Given docker inspect JSON for one container, produce:
      - suggestions: list of human-friendly suggestions
      - override_yaml_text: docker-compose override snippet as text
    """
    suggestions = []
    override = {}
    service_name = (inspect_json.get("Name") or "").lstrip("/") or inspect_json.get("Config", {}).get("Image", "service")
    # HostConfig fields
    hc = inspect_json.get("HostConfig", {})

    # 1) readonly rootfs
    readonly_rootfs = hc.get("ReadonlyRootfs", False)
    if not readonly_rootfs:
        suggestions.append("Set the container root filesystem to read_only (ReadonlyRootfs).")
        override.setdefault(service_name, {})["read_only"] = True
    else:
        suggestions.append("Container already has ReadonlyRootfs enabled.")

    # 2) drop capabilities
    cap_drop = hc.get("CapDrop") or []
    if "ALL" not in [str(x).upper() for x in cap_drop]:
        suggestions.append("Drop all Linux capabilities (cap_drop: [ALL]).")
        override.setdefault(service_name, {})["cap_drop"] = ["ALL"]
    else:
        suggestions.append("Capabilities are already dropped.")

    # 3) no-new-privileges
    sec_opts = hc.get("SecurityOpt") or []
    if not any("no-new-privileges" in so for so in sec_opts):
        suggestions.append("Add security_opt: [\"no-new-privileges\"].")
        override.setdefault(service_name, {})["security_opt"] = ["no-new-privileges"]
    else:
        suggestions.append("no-new-privileges is already present in security_opt.")

    # 4) tmpfs for /tmp
    tmpfs = hc.get("Tmpfs") or {}
    # Note: Tmpfs can be dict mapping mountpoint->options. Inspect may show Tmpfs as dict or None
    has_tmp = False
    if isinstance(tmpfs, dict):
        has_tmp = "/tmp" in tmpfs.keys()
    elif isinstance(tmpfs, list):
        # older formats might show list: ["tmpfs:/tmp:rw"]
        has_tmp = any("/tmp" in t for t in tmpfs)
    if not has_tmp:
        suggestions.append("Mount a tmpfs at /tmp to avoid writing secrets to disk (tmpfs: /tmp).")
        override.setdefault(service_name, {})["tmpfs"] = ["/tmp"]
    else:
        suggestions.append("/tmp is already configured as tmpfs.")

    # 5) seccomp profile hint
    current_seccomp = inspect_json.get("HostConfig", {}).get("SecurityOpt") or []
    # we won't attempt to change the entire seccomp profile, but recommend using 'default' or a custom restricted profile
    suggestions.append("Consider applying a restrictive seccomp profile (e.g., use Docker's default seccomp or provide a custom profile).")

    # build override YAML text manually to avoid dependency
    # Compose format (v2+): serviceName: { <overrides> }
    def format_yaml_from_override(ov):
        lines = []
        lines.append("version: '3.8'")
        lines.append("services:")
        for svc, conf in ov.items():
            lines.append(f"  {svc}:")
            for key, val in conf.items():
                # basic formatting for lists and booleans
                if isinstance(val, bool):
                    lines.append(f"    {key}: {str(val).lower()}")
                elif isinstance(val, list):
                    # list of scalars
                    if len(val) == 0:
                        lines.append(f"    {key}: []")
                    else:
                        lines.append(f"    {key}:")
                        for item in val:
                            lines.append(f"      - {item}")
                elif isinstance(val, dict):
                    lines.append(f"    {key}:")
                    for k2, v2 in val.items():
                        lines.append(f"      {k2}: {v2}")
                else:
                    lines.append(f"    {key}: {val}")
        return "\n".join(lines)

    override_yaml = format_yaml_from_override(override) if override else "# No runtime hardening suggestions — container already hardened."

    return suggestions, override_yaml
# ---------- end helpers ----------




class TrivySignals(QObject):
    # emits log lines (string)
    log = pyqtSignal(str)
    # emits summary dict, container_id (str), duration_seconds (float), trivy_json_path (str or None)
    summary = pyqtSignal(object, str, float, object)


class DockerBenchSignals(QObject):
    log = pyqtSignal(str)  # string log lines
    result = pyqtSignal(object, str, float, object)  # summary_dict, container_id_or_host, duration_seconds, report_path



# put this near the top, after imports
TRIVY_BIN = r"D:\total data\Document Data\DCM-main\trivy_0.67.0_windows-64bit"


def QTimer_single_shot(fn):
    QTimer.singleShot(0, fn)


def analyze_dockerfile(path):
    text = Path(path).read_text(encoding="utf-8", errors="ignore")
    suggestions = []

    # 1. Use pinned base image
    m = re.search(r'^\s*FROM\s+([^\s:]+)(?::([^\s]+))?', text, re.MULTILINE)
    if m:
        if not m.group(2):
            suggestions.append("Pin base image by adding a specific tag (avoid `:latest`).")
    else:
        suggestions.append("No FROM line found (invalid Dockerfile).")

    # 2. Avoid ADD when COPY suffices
    if re.search(r'^\s*ADD\s+', text, re.MULTILINE):
        suggestions.append("Replace ADD with COPY unless you need auto-extract or remote URLs.")

    # 3. Use non-root user
    if not re.search(r'^\s*USER\s+', text, re.MULTILINE):
        suggestions.append("Add a non-root USER with a fixed UID/GID where possible.")

    # 4. Combine apt-get install and clean apt cache
    if re.search(r'apt-get\s+install', text) and ('rm -rf /var/lib/apt/lists' not in text):
        suggestions.append("Clean apt lists after install: add `rm -rf /var/lib/apt/lists/*` in the same RUN.")

    # 5. Use --no-install-recommends
    if re.search(r'apt-get\s+install', text) and ('--no-install-recommends' not in text):
        suggestions.append("Use '--no-install-recommends' during apt-get install to limit packages.")

    # 6. Prefer multi-stage builds
    if 'COPY --from=' not in text and text.count('FROM') >= 1 and not re.search(r'^\s*FROM\s+\S+\s+AS\s+\S+', text, re.MULTILINE | re.IGNORECASE):
        suggestions.append("Consider multi-stage builds to reduce final image size and leak build-time artifacts.")

    # 7. Remove secrets and hard-coded credentials
    if re.search(r'(?i)(password|passwd|secret|token|key)\s*[:=]', text):
        suggestions.append("Remove hard-coded credentials. Use build args / Docker secrets or environment injection at runtime.")

    return suggestions

def generate_patch(path):
    """
    Return (patched_text, pinned_base_was_modified_bool)
    Simple, conservative transforms:
      - if FROM without tag -> append ':stable' (user should review)
      - replace ADD -> COPY
      - add USER non-root if missing
      - append apt cleanup if apt-get present
    """
    text = Path(path).read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    patched_lines = []
    pinned = False

    for line in lines:
        # Pin base image (first FROM encountered)
        if line.lstrip().upper().startswith('FROM ') and ':' not in line.split()[1]:
            # keep original but append a placeholder tag
            # safer to append :stable than :latest — user must verify
            parts = line.split(None, 1)
            if len(parts) > 1:
                base = parts[1].strip()
                if ':' not in base:
                    patched_lines.append(f"{parts[0]} {base}:stable")
                    pinned = True
                    continue
        # replace ADD with COPY
        if re.match(r'^\s*ADD\s+', line):
            patched_lines.append(re.sub(r'^\s*ADD', 'COPY', line))
        else:
            patched_lines.append(line)

    patched_text = "\n".join(patched_lines)

    # add non-root user if missing
    if not re.search(r'^\s*USER\s+', patched_text, re.MULTILINE):
        patched_text += '\n\n# Hardening: create and switch to non-root user\nRUN groupadd -r app && useradd -r -g app -u 1000 app || true\nUSER 1000:1000\n'

    # add apt cleanup heuristic
    if re.search(r'apt-get\s+install', patched_text) and 'rm -rf /var/lib/apt/lists' not in patched_text:
        patched_text += '\n# Hardening: clean apt lists to reduce image size\nRUN rm -rf /var/lib/apt/lists/*\n'

    return patched_text, pinned
# ---------- end helpers ----------
class ContainerMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Docker Container Monitor")
        self.setGeometry(100, 100, 800, 800)

        # Universal stats configuration
        self.active_stats = {"CPU": True, "Memory": True, "Network I/O": False, "Disk I/O": False}

        # create trivy signals and connect handlers
        self.trivy_signals = TrivySignals()
        self.trivy_signals.log.connect(self._handle_trivy_log)
        self.trivy_signals.summary.connect(self._handle_trivy_summary)
        self.dbench_signals = DockerBenchSignals()
        self.dbench_signals.log.connect(self._handle_trivy_log)      # reuse log handler to show logs in debug window
        self.dbench_signals.result.connect(self._handle_dockerbench_result)

        self.init_ui()

    def init_ui(self):
        # Main layout with tabs
        self.tabs = QTabWidget(self)
        self.tabs.setTabsClosable(True)
        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tabs)

        # Menu bar
        self.menu_bar = self.menuBar()
        view_menu = self.menu_bar.addMenu("View")

        # Recreate Containers tab
        recreate_action = QAction("Show Containers", self)
        recreate_action.triggered.connect(self.recreate_containers_tab)
        view_menu.addAction(recreate_action)

        # Recreate Network Tab
        network_activity_action = QAction("Show Network Activity", self)
        network_activity_action.triggered.connect(self.recreate_network_tab)
        view_menu.addAction(network_activity_action)

        # Preferences submenu
        preferences_action = QAction("Preferences...", self)
        preferences_action.triggered.connect(self.open_configure_dialog)
        view_menu.addAction(preferences_action)

        # Toolbar (modern, icon-first buttons)
        import os
        from PyQt6.QtWidgets import QToolButton
        from PyQt6.QtCore import QSize

        self.toolbar = QToolBar(self)
        self.toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)

        from PyQt6.QtCore import QSize

        # ensure icons are not huge and text isn't clipped
        self.toolbar.setIconSize(QSize(28, 28))

        # Defensive: enforce text color on any toolbutton (applies after buttons created)
        for tb in self.toolbar.findChildren(QToolButton):
            tb.setStyleSheet("color: #E9EEF7;")   # fallback in case stylesheet was ignored by the widget
            tb.setIconSize(QSize(28, 28))


        # helper to add a modern toolbutton
        def add_toolbutton(icon_path, tooltip, slot, text=None):
            btn = QToolButton()
            if icon_path and os.path.exists(icon_path):
                btn.setIcon(QIcon(icon_path))
            else:
                btn.setText(text or tooltip)
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            btn.setAutoRaise(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip(tooltip)
            btn.clicked.connect(slot)
            btn.setProperty("pushButton", True)
            btn.setMinimumWidth(96)
            self.toolbar.addWidget(btn)
            return btn

        # add toolbar buttons (icons optional)
        add_toolbutton("refresh.ico", "Refresh Containers", self.load_containers, text="Refresh")
        add_toolbutton("network.ico", "Network Graph", self.plot_network_graph, text="Graph")
        add_toolbutton("heatmap.ico", "Heatmap", self.plot_connection_heatmap, text="Heatmap")
        add_toolbutton("trivy.ico", "Trivy Scan", self.trivy_scan_clicked, text="Trivy")
        add_toolbutton("dockerbench.ico", "Docker Bench", self.dockerbench_clicked, text="DockerBench")
        add_toolbutton("dockerfile.ico", "Check Dockerfile", self.check_dockerfile_clicked, text="Dockerfile")
        add_toolbutton("nmap.ico", "Nmap Scan", self.nmap_scan_clicked, text="Nmap")
        # add_toolbutton("runtime.ico", "Check Runtime Config", self.check_runtime_config_clicked, text="Runtime")

        # Tab for listing all containers
        self.container_list_tab = QWidget()
        self.container_list_layout = QVBoxLayout()
        self.container_list_tab.setLayout(self.container_list_layout)
        self.tabs.addTab(self.container_list_tab, "Containers")

        # Table to display containers
        self.container_table = QTableWidget()
        self.container_list_layout.addWidget(self.container_table)
        self.container_table.setColumnCount(5)
        self.container_table.setHorizontalHeaderLabels(["Container ID", "Container Name", "Image Name", "Status", "Command"])
        self.container_table.cellClicked.connect(self.container_clicked)

        self.load_containers()

        self.network_tab = None
        self.recreate_network_tab()



    #newww


    # inside ContainerMonitor class
    def nmap_scan_clicked(self):
        """
        Run a quick nmap TCP connect scan against the selected container IP.
        Saves full nmap output to a temp file and shows a summary dialog.
        """
        import time, traceback

        # get selected container id
        container_id, stats_tab = self.get_selected_container_id()
        if not container_id:
            dlg = QDialog(self)
            dlg.setWindowTitle("Nmap Scan — No container selected")
            layout = QVBoxLayout(dlg)
            layout.addWidget(QLabel("Select a container row or open the container stats tab first."))
            btn = QPushButton("OK")
            btn.clicked.connect(dlg.accept)
            layout.addWidget(btn)
            dlg.exec()
            return

        # quick helper to emit logs (reuse trivy debug window)
        def emit_log(s):
            try:
                # prefer trivy_signals if available
                if hasattr(self, "trivy_signals") and getattr(self.trivy_signals, "log", None):
                    self.trivy_signals.log.emit(str(s))
                else:
                    print(s)
            except Exception:
                try:
                    print(s)
                except Exception:
                    pass

        emit_log(f"\n--- Nmap quick scan started: {datetime.now().isoformat()} for {container_id[:12]} ---\n")

        def worker():
            start = time.time()
            nmap_report_path = None
            try:
                # 1) Resolve container IP
                emit_log(f"[debug] Resolving container IP for {container_id}")
                try:
                    insp = subprocess.run(
                        ["docker", "inspect", "--format", "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}", container_id],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10
                    )
                except Exception as e:
                    raise RuntimeError(f"Docker inspect failed: {e}")

                ip = (insp.stdout or "").strip()
                if not ip:
                    raise RuntimeError(f"Could not determine IP for container {container_id}. Docker inspect stderr: {insp.stderr}")

                emit_log(f"[debug] Container IP: {ip}")

                # 2) Ensure nmap exists
                nmap_bin = "C:/Program Files (x86)/Nmap/nmap.exe"
                if not nmap_bin:
                    raise RuntimeError("nmap not found on PATH. Install nmap and try again.")

                # 3) Build safe default nmap command (TCP connect scan, service detection, common ports)
                # -Pn : skip host discovery (treat host as up)
                # -sT : TCP connect scan (no raw sockets)
                # -p 1-1024 : common ports (faster); change to '-p-' to scan all ports
                # -sV : service/version detection
                # --open : show only open ports
                cmd = [nmap_bin, "-Pn", "-sT", "-p", "1-1024", "-sV", "--open", ip]

                emit_log(f"[debug] Running: {' '.join(cmd)} (may take a few seconds)")

                try:
                    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=300)
                except subprocess.TimeoutExpired:
                    raise RuntimeError("nmap scan timed out")

                stdout = proc.stdout or ""
                stderr = proc.stderr or ""

                emit_log("[nmap stdout]\n" + (stdout if stdout else "<empty>"))
                if stderr:
                    emit_log("[nmap stderr]\n" + stderr)

                # 4) Save full output to a temp file
                try:
                    tf = tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8")
                    tf.write(stdout + "\n\n--- STDERR ---\n\n" + stderr)
                    tf.close()
                    nmap_report_path = tf.name
                    emit_log(f"[debug] Nmap report saved to: {nmap_report_path}")
                except Exception as e:
                    emit_log(f"[error] Failed to save nmap report: {e}")

                # 5) Parse simple summary of open ports from stdout using regex
                # nmap open port line example: "22/tcp   open  ssh     OpenSSH 8.4"
                open_ports = []
                for line in stdout.splitlines():
                    m = re.match(r'^\s*([0-9]+)/(tcp|udp)\s+open\s+([^\s]+)\s*(.*)', line)
                    if m:
                        port = m.group(1)
                        proto = m.group(2)
                        service = m.group(3)
                        version = m.group(4).strip()
                        open_ports.append({"port": port, "proto": proto, "service": service, "version": version})

                # 6) Build summary dict
                summary = {
                    "target_ip": ip,
                    "open_count": len(open_ports),
                    "open_ports": open_ports
                }

                duration = time.time() - start

                # 7) Show summary dialog on main thread
                def show_summary():
                    self.show_nmap_summary_dialog(container_id, summary, duration, nmap_report_path)
                QTimer_single_shot(show_summary)

            except Exception as exc:
                emit_log(f"[exception] {type(exc).__name__}: {exc}")
                import traceback
                traceback.print_exc()
                # show error dialog on main thread
                def show_err():
                    dlg = QDialog(self)
                    dlg.setWindowTitle("Nmap Scan Error")
                    l = QVBoxLayout(dlg)
                    l.addWidget(QLabel(f"Error running nmap: {exc}"))
                    b = QPushButton("OK")
                    b.clicked.connect(dlg.accept)
                    l.addWidget(b)
                    dlg.exec()
                QTimer_single_shot(show_err)

        Thread(target=worker, daemon=True).start()


    def check_dockerfile_clicked(self):
        """
        Open file picker, analyze Dockerfile, show suggested hardening patch and unified diff,
        allow user to Save (overwrite) or Save As a new file or Cancel.
        """
        # pick file
        fd = QFileDialog(self)
        fd.setFileMode(QFileDialog.FileMode.ExistingFile)
        fd.setNameFilter("Dockerfile (Dockerfile *Dockerfile);;All Files (*)")
        ok = fd.exec()
        if not ok:
            return
        paths = fd.selectedFiles()
        if not paths:
            return
        dockerfile_path = paths[0]

        try:
            orig_text = Path(dockerfile_path).read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to read file: {e}")
            return

        # analyze and generate
        suggestions = analyze_dockerfile(dockerfile_path)
        patched_text, pinned = generate_patch(dockerfile_path)

        # create unified diff
        diff_lines = list(difflib.unified_diff(
            orig_text.splitlines(keepends=False),
            patched_text.splitlines(keepends=False),
            fromfile=f"Original: {dockerfile_path}",
            tofile="Patched (suggested)",
            lineterm=""
        ))
        diff_text = "\n".join(diff_lines) if diff_lines else "(no textual changes suggested)"

        # Build dialog with suggestions and diff side-by-side
        dlg = QDialog(self)
        dlg.setWindowTitle("Dockerfile Hardening — Review Changes")
        dlg.setMinimumSize(900, 600)
        layout = QVBoxLayout(dlg)

        # Suggestions area
        if suggestions:
            layout.addWidget(QLabel("Suggestions:"))
            sug_text = QTextEdit()
            sug_text.setReadOnly(True)
            sug_text.setPlainText("\n".join(f"- {s}" for s in suggestions))
            sug_text.setMaximumHeight(120)
            layout.addWidget(sug_text)
        else:
            layout.addWidget(QLabel("No suggestions — Dockerfile looks OK."))

        # Splitter: left original, right patched (and below a diff view)
        splitter = QSplitter()
        orig_edit = QTextEdit()
        orig_edit.setReadOnly(True)
        orig_edit.setPlainText(orig_text)
        patched_edit = QTextEdit()
        patched_edit.setReadOnly(True)
        patched_edit.setPlainText(patched_text)
        splitter.addWidget(orig_edit)
        splitter.addWidget(patched_edit)
        splitter.setSizes([450, 450])
        layout.addWidget(splitter)

        # Diff view below
        layout.addWidget(QLabel("Unified diff (original → patched):"))
        diff_view = QTextEdit()
        diff_view.setReadOnly(True)
        diff_view.setPlainText(diff_text)
        diff_view.setMinimumHeight(180)
        layout.addWidget(diff_view)

        # Buttons: Save (overwrite), Save As, Cancel
        btn_save = QPushButton("Save (overwrite original)")
        btn_saveas = QPushButton("Save As...")
        btn_cancel = QPushButton("Cancel")

        def do_save_overwrite():
            try:
                Path(dockerfile_path).write_text(patched_text, encoding="utf-8")
                QMessageBox.information(self, "Saved", f"Patched Dockerfile saved to:\n{dockerfile_path}")
                dlg.accept()
            except Exception as e:
                QMessageBox.critical(self, "Save failed", f"Could not save: {e}")

        def do_save_as():
            target, _ = QFileDialog.getSaveFileName(self, "Save patched Dockerfile as", os.path.dirname(dockerfile_path), "Dockerfile (*)")
            if not target:
                return
            try:
                Path(target).write_text(patched_text, encoding="utf-8")
                QMessageBox.information(self, "Saved", f"Patched Dockerfile saved to:\n{target}")
                dlg.accept()
            except Exception as e:
                QMessageBox.critical(self, "Save failed", f"Could not save: {e}")

        btn_save.clicked.connect(do_save_overwrite)
        btn_saveas.clicked.connect(do_save_as)
        btn_cancel.clicked.connect(dlg.reject)

        # layout for buttons
        from PyQt6.QtWidgets import QHBoxLayout
        h = QHBoxLayout()
        h.addWidget(btn_save)
        h.addWidget(btn_saveas)
        h.addWidget(btn_cancel)
        layout.addLayout(h)

        dlg.exec()

    def show_nmap_summary_dialog(self, container_id, summary, duration_seconds, report_path=None):
        """
        Summary UI for nmap results. Shows open ports and a button to view full report.
        """
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Nmap Scan — {container_id[:12]}")
        layout = QVBoxLayout(dlg)

        if "error" in (summary or {}):
            layout.addWidget(QLabel("Scan failed: " + str(summary.get("error"))))
        else:
            layout.addWidget(QLabel(f"Target IP: {summary.get('target_ip')}"))
            layout.addWidget(QLabel(f"Duration: {duration_seconds:.1f} s"))
            layout.addWidget(QLabel(f"Open ports found: {summary.get('open_count', 0)}"))

            if summary.get("open_ports"):
                layout.addWidget(QLabel("Open ports:"))
                for p in summary["open_ports"]:
                    ver = f" — {p['version']}" if p.get('version') else ""
                    layout.addWidget(QLabel(f"{p['port']}/{p['proto']}  {p['service']}{ver}"))

        # Buttons
        btn_view = QPushButton("View full nmap report")
        def open_report():
            if not report_path or not os.path.exists(report_path):
                m = QDialog(self)
                m.setWindowTitle("Report not available")
                ml = QVBoxLayout(m)
                ml.addWidget(QLabel("Full report is not available on disk."))
                b = QPushButton("OK")
                b.clicked.connect(m.accept)
                ml.addWidget(b)
                m.exec()
                return
            try:
                os.startfile(report_path)
            except Exception as e:
                warn = QDialog(self)
                warn.setWindowTitle("Open failed")
                wl = QVBoxLayout(warn)
                wl.addWidget(QLabel(f"Could not open the report: {e}"))
                b = QPushButton("OK")
                b.clicked.connect(warn.accept)
                wl.addWidget(b)
                warn.exec()

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(dlg.accept)

        from PyQt6.QtWidgets import QHBoxLayout
        h = QHBoxLayout()
        h.addWidget(btn_view)
        h.addWidget(btn_close)
        layout.addLayout(h)

        dlg.exec()


    def _handle_dockerbench_result(self, summary, target, duration_seconds, report_path):
        """
        summary: dict with counts {'PASS':n,'WARN':n,'INFO':n,'NOTE':n}
        target: usually 'host' or container id (we'll use 'host' since docker-bench runs against host)
        duration_seconds: float
        report_path: path to the saved full-text report
        """
        try:
            # show a dialog with summary and button to view full report
            dlg = QDialog(self)
            dlg.setWindowTitle("Docker Bench Security — Summary")
            layout = QVBoxLayout(dlg)

            if not isinstance(summary, dict):
                layout.addWidget(QLabel("No summary available. See full report."))
            else:
                layout.addWidget(QLabel(f"Target: {target}"))
                layout.addWidget(QLabel(f"Duration: {duration_seconds:.1f} s"))
                layout.addWidget(QLabel(f"PASS: {summary.get('PASS', 0)}  WARN: {summary.get('WARN', 0)}"))
                layout.addWidget(QLabel(f"INFO: {summary.get('INFO', 0)}  NOTE: {summary.get('NOTE', 0)}"))

                # show top few WARN lines if present (we'll read from the report)
                try:
                    if report_path and os.path.exists(report_path):
                        # try to show the first few WARN lines
                        with open(report_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                        warn_lines = [ln.strip() for ln in lines if ln.strip().startswith('[WARN]')]
                        if warn_lines:
                            layout.addWidget(QLabel("Sample WARNs:"))
                            for wl in warn_lines[:6]:
                                layout.addWidget(QLabel(wl))
                except Exception:
                    pass

            btn_view = QPushButton("View full report")
            def open_report():
                if report_path and os.path.exists(report_path):
                    try:
                        os.startfile(report_path)
                    except Exception as e:
                        m = QDialog(self)
                        m.setWindowTitle("Open failed")
                        ml = QVBoxLayout(m)
                        ml.addWidget(QLabel(f"Could not open: {e}"))
                        b = QPushButton("OK")
                        b.clicked.connect(m.accept)
                        ml.addWidget(b)
                        m.exec()
                else:
                    m = QDialog(self)
                    m.setWindowTitle("Report not available")
                    ml = QVBoxLayout(m)
                    ml.addWidget(QLabel("Full report not available on disk."))
                    b = QPushButton("OK")
                    b.clicked.connect(m.accept)
                    ml.addWidget(b)
                    m.exec()

            btn_close = QPushButton("Close")
            btn_close.clicked.connect(dlg.accept)

            from PyQt6.QtWidgets import QHBoxLayout
            h = QHBoxLayout()
            h.addWidget(btn_view)
            h.addWidget(btn_close)
            layout.addLayout(h)

            dlg.exec()
        except Exception as e:
            print("Failed to show docker bench result dialog:", e)

    def _handle_trivy_log(self, msg: str):
        # always print to terminal
        try:
            print(msg)
        except Exception:
            pass

        # append to currently opened StatsTab logs if available
        try:
            # prefer current stats tab
            for i in range(self.tabs.count()):
                w = self.tabs.widget(i)
                if isinstance(w, StatsTab) and self.tabs.currentIndex() == i:
                    if hasattr(w, "logs_area"):
                        w.logs_area.append(msg)
                        break
        except Exception:
            pass

        # also append to debug window
        try:
            dbg = self.ensure_debug_log_window()
            dbg.append(msg)
        except Exception:
            pass

    def _handle_trivy_summary(self, summary, container_id, duration_seconds, trivy_json_path):
        # show the summary dialog (on main thread; signal already delivered on main thread)
        try:
            self.show_trivy_summary_dialog(container_id, summary, duration_seconds, trivy_json_path)
        except Exception as e:
            print("Failed to show trivy summary dialog:", e)

    def ensure_debug_log_window(self):
        """
        Create (or return) a simple non-modal dialog with a QTextEdit to show debug logs.
        Always returns the QTextEdit instance for appending.
        """
        # reuse if already created
        if getattr(self, "_debug_log_text", None):
            return self._debug_log_text

        dlg = QDialog(self)
        dlg.setWindowTitle("Trivy Debug Log")
        dlg.setModal(False)
        dlg.setMinimumSize(700, 400)
        layout = QVBoxLayout(dlg)
        text = QTextEdit()
        text.setReadOnly(True)
        layout.addWidget(text)
        btn_close = QPushButton("Close")
        btn_clear = QPushButton("Clear")
        def clear_text():
            text.clear()
        btn_clear.clicked.connect(clear_text)
        btn_close.clicked.connect(dlg.close)
        # small horizontal layout for buttons
        from PyQt6.QtWidgets import QHBoxLayout
        h = QHBoxLayout()
        h.addWidget(btn_clear)
        h.addWidget(btn_close)
        layout.addLayout(h)

        self._debug_log_dialog = dlg
        self._debug_log_text = text

        # show it non-blocking on the main thread
        QTimer_single_shot(lambda: dlg.show())
        return text


    def get_selected_container_info(self):
        # Prefer stats tab if open
        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            if isinstance(widget, StatsTab) and self.tabs.currentIndex() == i:
                return widget.container_id, widget.container_name, widget  # ID, image, tab

        # Fallback: container row
        row = self.container_table.currentRow()
        if row >= 0:
            cid = self.container_table.item(row, 0).text()
            name = self.container_table.item(row, 2).text()
            return cid, name, None

        return None, None, None

    def get_selected_container_id(self):
        """
        Return tuple (container_id, stats_tab_or_None).
        Tries (in order):
        1) currently active StatsTab
        2) a helper named get_selected_container_info() if it exists (handles older code)
        3) selected row in the containers table
        """
        # 1) prefer currently open stats tab container
        try:
            for i in range(self.tabs.count()):
                widget = self.tabs.widget(i)
                if isinstance(widget, StatsTab) and self.tabs.currentIndex() == i:
                    return widget.container_id, widget
        except Exception:
            pass

        # 2) if older helper exists, try to use it
        if hasattr(self, "get_selected_container_info"):
            try:
                info = self.get_selected_container_info()
                # accept either (id, name) or just id
                if isinstance(info, tuple) and len(info) > 0:
                    cid = info[0]
                else:
                    cid = info
                cid = (cid or "").strip()
                if cid:
                    # try to find an open StatsTab matching this id
                    for i in range(self.tabs.count()):
                        w = self.tabs.widget(i)
                        if isinstance(w, StatsTab) and getattr(w, "container_id", None) == cid:
                            return cid, w
                    return cid, None
            except Exception:
                pass

        # 3) fallback to selected row in the container table
        try:
            sel = self.container_table.currentRow()
            if sel >= 0:
                cid_item = self.container_table.item(sel, 0)
                if cid_item:
                    container_id = cid_item.text().strip()
                    # try to find matching StatsTab
                    for i in range(self.tabs.count()):
                        w = self.tabs.widget(i)
                        if isinstance(w, StatsTab) and getattr(w, "container_id", None) == container_id:
                            return container_id, w
                    return container_id, None
        except Exception:
            pass

        return None, None
    def dockerbench_clicked(self):
        """
        Run docker/docker-bench-security in background, capture output, summarize, and show dialog.
        Note: this requires Docker daemon permissions and ability to run the bench container.
        """
        import time, traceback

        # Use host as default target
        target = "host"

        # helper to emit logs to UI (via dbench_signals.log)
        def emit_log(s):
            try:
                self.dbench_signals.log.emit(str(s))
            except Exception:
                try: print(s)
                except: pass

        emit_log(f"\n--- Docker Bench run started: {datetime.now().isoformat()} ---\n")

        def worker():
            start = time.time()
            report_path = None
            summary = {"PASS": 0, "WARN": 0, "INFO": 0, "NOTE": 0}
            try:
                # Ensure docker is available
                if not shutil.which("docker"):
                    emit_log("[error] docker CLI not found on PATH.")
                    raise RuntimeError("docker CLI not found")

                # docker-bench command — default official image run
                # NOTE: on Windows some flags like --net host may behave differently on Docker Desktop.
                # Windows Docker Desktop mode — mount the docker socket from host
                cmd = [
                    "docker", "run", "--rm",
                    "-v", "//var/run/docker.sock:/var/run/docker.sock",
                    "docker/docker-bench-security"
                ]

                emit_log(f"[debug] Using Windows-friendly docker-bench command:")
                emit_log(f"[debug] {' '.join(cmd)}")

                try:
                    proc = subprocess.run(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        timeout=1200
                    )
                except subprocess.TimeoutExpired:
                    emit_log("[error] docker-bench timed out.")
                    raise RuntimeError("docker-bench timed out")

                out = proc.stdout or ""
                err = proc.stderr or ""

                emit_log("[docker-bench stdout]\n" + (out if out else "<empty>"))
                emit_log("[docker-bench stderr]\n" + (err if err else "<empty>"))


                # save full report to temp file (text)
                try:
                    tf = tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8")
                    tf.write(out + "\n\n--- STDERR ---\n\n" + err)
                    tf.close()
                    report_path = tf.name
                    emit_log(f"[debug] Docker Bench report saved to: {report_path}")
                except Exception as e:
                    emit_log(f"[error] Failed to save docker-bench report: {e}")

                # parse counts: look for [PASS], [WARN], [INFO], [NOTE] prefixes in output lines
                try:
                    pass_count = out.count("[PASS]")
                    warn_count = out.count("[WARN]")
                    info_count = out.count("[INFO]")
                    note_count = out.count("[NOTE]")
                    summary = {"PASS": pass_count, "WARN": warn_count, "INFO": info_count, "NOTE": note_count}
                    emit_log(f"[summary] PASS={pass_count} WARN={warn_count} INFO={info_count} NOTE={note_count}")
                except Exception as e:
                    emit_log(f"[error] Failed to parse docker-bench summary: {e}")

                duration = time.time() - start
                # emit final result on main thread via signal
                try:
                    self.dbench_signals.result.emit(summary, target, duration, report_path)
                except Exception:
                    # fallback: call handler directly on main thread
                    QTimer_single_shot(lambda: self._handle_dockerbench_result(summary, target, duration, report_path))

            except Exception as exc:
                tb = traceback.format_exc()
                emit_log(f"[exception] {type(exc).__name__}: {exc}\n{tb}")
                # still try to show result dialog with an error
                try:
                    self.dbench_signals.result.emit({"error": str(exc)}, target, 0.0, report_path)
                except Exception:
                    QTimer_single_shot(lambda: self._handle_dockerbench_result({"error": str(exc)}, target, 0.0, report_path))

        Thread(target=worker, daemon=True).start()

    def trivy_scan_clicked(self):
        import shutil, tempfile, traceback, time
        container_id, stats_tab = self.get_selected_container_id()
        if not container_id:
            dlg = QDialog(self)
            dlg.setWindowTitle("Trivy Scan — No container selected")
            layout = QVBoxLayout(dlg)
            layout.addWidget(QLabel("Select a container tab or row first."))
            btn = QPushButton("OK")
            btn.clicked.connect(dlg.accept)
            layout.addWidget(btn)
            dlg.exec()
            return

        # small helper to emit log via signal
        def emit_log(msg):
            try:
                self.trivy_signals.log.emit(msg)
            except Exception:
                # fallback to printing if signal fails
                try: print(msg)
                except Exception: pass

        emit_log(f"\n--- Trivy quick scan started: {datetime.now().isoformat()} ---\n")

        def worker():
            start = time.time()
            trivy_json_path = None
            try:
                # locate trivy
                trivy_path = globals().get("TRIVY_BIN")
                if trivy_path and os.path.exists(trivy_path):
                    emit_log(f"[debug] Using TRIVY_BIN at: {trivy_path}")
                else:
                    found = shutil.which("trivy")
                    if found:
                        trivy_path = found
                        emit_log(f"[debug] Using trivy at PATH: {trivy_path}")
                    else:
                        emit_log("[error] Trivy binary not found. Ensure TRIVY_BIN or trivy on PATH.")
                        raise FileNotFoundError("trivy binary not found")

                # docker inspect to get image
                emit_log(f"[debug] Running docker inspect on container: {container_id}")
                insp = subprocess.run(
                    ["docker", "inspect", "--format", "{{.Config.Image}}", container_id],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15
                )
                emit_log(f"[debug] docker inspect rc={insp.returncode}")
                if insp.stdout:
                    emit_log(f"[debug] docker inspect stdout: {insp.stdout.strip()}")
                if insp.stderr:
                    emit_log(f"[debug] docker inspect stderr: {insp.stderr.strip()}")

                image = (insp.stdout or "").strip()
                if not image:
                    emit_log("[error] Could not determine image from docker inspect; aborting.")
                    raise RuntimeError("Could not determine container image")

                emit_log(f"[debug] Scanning image: {image}")
                cmd = [trivy_path, "image", "--format", "json", image]
                emit_log(f"[debug] Running: {' '.join(cmd)} (may download DB on first run)")

                try:
                    proc = subprocess.run(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=600,
                        text=True
                    )
                except subprocess.TimeoutExpired:
                    emit_log("[error] Trivy scan timed out.")
                    raise RuntimeError("Trivy scan timed out")

                stdout = proc.stdout or ""
                stderr = proc.stderr or ""
                emit_log(f"[debug] trivy exit code: {proc.returncode}")

                # Save JSON if present
                try:
                    if stdout.strip().startswith("{") or stdout.strip().startswith("["):
                        tf = tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w", encoding="utf-8")
                        tf.write(stdout)
                        tf.close()
                        trivy_json_path = tf.name
                        emit_log(f"[debug] Trivy JSON saved to: {trivy_json_path}")
                    elif stderr.strip().startswith("{") or stderr.strip().startswith("["):
                        tf = tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w", encoding="utf-8")
                        tf.write(stderr)
                        tf.close()
                        trivy_json_path = tf.name
                        emit_log(f"[debug] Trivy JSON saved to: {trivy_json_path}")
                except Exception as e:
                    emit_log(f"[error] Failed to save trivy JSON: {e}")

                # emit full stdout/stderr
                emit_log("[trivy stdout]\n" + (stdout if stdout else "<empty>"))
                emit_log("[trivy stderr]\n" + (stderr if stderr else "<empty>"))

                # parse JSON for summary
                raw = None
                if stdout.strip().startswith("{") or stdout.strip().startswith("["):
                    raw = stdout
                elif stderr.strip().startswith("{") or stderr.strip().startswith("["):
                    raw = stderr

                summary = {"total_vulns": 0, "severity_counts": {}, "total_secrets": 0, "top_vulns": []}
                if raw:
                    try:
                        parsed = json.loads(raw)
                        results = parsed.get("Results", []) if isinstance(parsed, dict) else []
                        vuln_list = []
                        for r in results:
                            for v in r.get("Vulnerabilities", []) or []:
                                vuln_list.append(v)
                                sev = (v.get("Severity") or "UNKNOWN").upper()
                                summary["severity_counts"][sev] = summary["severity_counts"].get(sev, 0) + 1
                            secrets = r.get("Secrets", []) or []
                            summary["total_secrets"] += len(secrets)
                            if (r.get("Type") or "").lower() == "secret":
                                summary["total_secrets"] += len(r.get("Matches", []) or [])
                        summary["total_vulns"] = len(vuln_list)
                        vuln_sorted = sorted(vuln_list, key=lambda v: (v.get("Severity") or ""), reverse=True)
                        for v in vuln_sorted[:5]:
                            summary["top_vulns"].append({
                                "id": v.get("VulnerabilityID"),
                                "pkg": v.get("PkgName"),
                                "installed": v.get("InstalledVersion"),
                                "fixed": v.get("FixedVersion"),
                                "severity": v.get("Severity")
                            })
                    except Exception as e:
                        emit_log(f"[error] JSON parse failed: {e}")

                emit_log(f"\n[summary] total_vulns={summary.get('total_vulns')} severities={summary.get('severity_counts')} total_secrets={summary.get('total_secrets')}\n")

                duration = time.time() - start
                # emit summary via signal (delivered on main thread)
                try:
                    self.trivy_signals.summary.emit(summary, container_id, duration, trivy_json_path)
                except Exception:
                    # fallback: call handler directly on main thread
                    try:
                        QTimer_single_shot(lambda: self._handle_trivy_summary(summary, container_id, duration, trivy_json_path))
                    except Exception:
                        pass

            except Exception as exc:
                tb = traceback.format_exc()
                emit_log(f"\n[exception] {type(exc).__name__}: {exc}\n{tb}\n")
                # still emit a summary object with error so UI can show something
                try:
                    err_summary = {"error": str(exc)}
                    self.trivy_signals.summary.emit(err_summary, container_id, 0.0, None)
                except Exception:
                    QTimer_single_shot(lambda: self._handle_trivy_summary({"error": str(exc)}, container_id, 0.0, None))

        Thread(target=worker, daemon=True).start()




    def run_trivy_on_container(self, container_id, timeout=180):
        """
        Runs a Trivy quick scan on the IMAGE behind a running container and returns:
        (summary_dict, raw_json_string_or_None, stdout_text, stderr_text)

        summary = {
            "total_vulns": int,
            "severity_counts": { "LOW": .., "MEDIUM": .., ... },
            "total_secrets": int,
            "top_vulns": [ {id, pkg, installed, fixed, severity}, ... ]
        }
        """

        # 1) Get image name for this container
        try:
            insp = subprocess.run(
                ["docker", "inspect", "--format", "{{.Config.Image}}", container_id],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=15
            )
        except Exception as e:
            raise RuntimeError(f"Failed to inspect container: {e}")

        image = (insp.stdout or "").strip()
        if not image:
            err = (insp.stderr or "").strip()
            raise RuntimeError(f"Could not determine image for container {container_id}. Docker inspect stderr: {err}")

        # 2) Build trivy command: scan the image in JSON mode
        cmd = [TRIVY_BIN, "image", "--format", "json", image]

        try:
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
                text=True
            )
        except FileNotFoundError:
            raise RuntimeError(f"Trivy binary not found at: {TRIVY_BIN}")
        except subprocess.TimeoutExpired:
            raise RuntimeError("Trivy scan timed out")

        stdout = proc.stdout or ""
        stderr = proc.stderr or ""

        # 3) Try to get JSON from stdout or stderr
        raw = None
        s_out = stdout.strip()
        s_err = stderr.strip()

        if s_out.startswith("{") or s_out.startswith("["):
            raw = stdout
        elif s_err.startswith("{") or s_err.startswith("["):
            raw = stderr

        summary = {
            "total_vulns": 0,
            "severity_counts": {},
            "total_secrets": 0,
            "top_vulns": []
        }

        if raw:
            try:
                parsed = json.loads(raw)
            except Exception:
                parsed = None

            if isinstance(parsed, dict):
                results = parsed.get("Results", []) or []
                vuln_list = []

                for r in results:
                    # Vulnerabilities
                    for v in r.get("Vulnerabilities", []) or []:
                        vuln_list.append(v)
                        sev = (v.get("Severity") or "UNKNOWN").upper()
                        summary["severity_counts"][sev] = summary["severity_counts"].get(sev, 0) + 1

                    # Secrets (Trivy secret scanner)
                    secrets = r.get("Secrets", []) or []
                    summary["total_secrets"] += len(secrets)

                    # Some formats: results with Type == "secret" and Matches list
                    if (r.get("Type") or "").lower() == "secret":
                        summary["total_secrets"] += len(r.get("Matches", []) or [])

                summary["total_vulns"] = len(vuln_list)

                # Sort top vulns roughly by severity then id (CRITICAL/HIGH bubble up)
                sev_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "UNKNOWN": 0}
                def sev_key(v):
                    s = (v.get("Severity") or "UNKNOWN").upper()
                    return sev_order.get(s, 0)

                vuln_sorted = sorted(
                    vuln_list,
                    key=lambda v: (sev_key(v), v.get("VulnerabilityID") or ""),
                    reverse=True
                )

                top = []
                for v in vuln_sorted[:10]:
                    top.append({
                        "id": v.get("VulnerabilityID"),
                        "pkg": v.get("PkgName"),
                        "installed": v.get("InstalledVersion"),
                        "fixed": v.get("FixedVersion"),
                        "severity": v.get("Severity")
                    })
                summary["top_vulns"] = top

        else:
            # No JSON output – bubble up error context
            if proc.returncode != 0:
                summary = {
                    "error": f"Trivy exited with code {proc.returncode}. See stderr for details."
                }
            else:
                summary = {
                    "error": "No JSON output from Trivy. stdout/stderr appended to logs."
                }

        return summary, raw, stdout, stderr


    
    
    def show_trivy_summary_dialog(self, container_id, summary, duration_seconds, trivy_json_path=None):
        """
        Robust summary dialog — replaces previous versions.
        Always shows a dialog. Adds a 'View full JSON' button and attempts to open the JSON automatically.
        """
        import os, traceback

        # Build dialog
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Trivy Quick Scan — {container_id[:12]}")
        dlg.setModal(False)  # non-blocking so auto-open can run
        layout = QVBoxLayout(dlg)

        # Header / error handling
        if not isinstance(summary, dict):
            layout.addWidget(QLabel("No summary available (unexpected format). See full report."))
            summary = {}

        if "error" in summary:
            layout.addWidget(QLabel("Scan failed: " + str(summary.get("error"))))
        else:
            total = summary.get("total_vulns", 0)
            sev = summary.get("severity_counts", {})
            critical = sev.get("CRITICAL", 0) + sev.get("Critical", 0)
            high = sev.get("HIGH", 0) + sev.get("High", 0)
            secrets = summary.get("total_secrets", 0)

            layout.addWidget(QLabel(f"Duration: {duration_seconds:.1f} s"))
            layout.addWidget(QLabel(f"Total vulnerabilities: {total}"))
            layout.addWidget(QLabel(f"Critical: {critical}  |  High: {high}"))
            layout.addWidget(QLabel(f"Secrets found: {secrets}"))

            if summary.get("top_vulns"):
                layout.addWidget(QLabel("Top vulns:"))
                for v in summary["top_vulns"][:8]:
                    v_id = v.get("id") or v.get("VulnerabilityID") or "<id>"
                    pkg = v.get("pkg") or v.get("PkgName") or "<pkg>"
                    inst = v.get("installed") or v.get("InstalledVersion") or "-"
                    fixed = v.get("fixed") or v.get("FixedVersion") or "-"
                    sevtxt = v.get("severity") or v.get("Severity") or ""
                    layout.addWidget(QLabel(f"{v_id}  @ {pkg} — {inst} -> {fixed} ({sevtxt})"))

        # Buttons
        btn_view = QPushButton("View full JSON report")
        def open_report():
            if not trivy_json_path or not os.path.exists(trivy_json_path):
                # show small dialog explaining missing file
                m = QDialog(self)
                m.setWindowTitle("Report not available")
                ml = QVBoxLayout(m)
                ml.addWidget(QLabel("Full JSON report is not available on disk."))
                b = QPushButton("OK")
                b.clicked.connect(m.accept)
                ml.addWidget(b)
                m.exec()
                return
            try:
                os.startfile(trivy_json_path)  # windows: open in default app (Notepad, Notepad++, etc.)
            except Exception as e:
                # fallback: show path in dialog
                m = QDialog(self)
                m.setWindowTitle("Could not open file")
                ml = QVBoxLayout(m)
                ml.addWidget(QLabel(f"Could not open file automatically: {e}"))
                ml.addWidget(QLabel(f"Report path: {trivy_json_path}"))
                b = QPushButton("OK")
                b.clicked.connect(m.accept)
                ml.addWidget(b)
                m.exec()

        btn_view.clicked.connect(open_report)

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(dlg.accept)

        # Horizontal layout for buttons
        from PyQt6.QtWidgets import QHBoxLayout
        h = QHBoxLayout()
        h.addWidget(btn_view)
        h.addWidget(btn_close)
        layout.addLayout(h)

        # Show dialog immediately on main thread
        try:
            dlg.show()
        except Exception:
            # last resort: exec (blocking)
            dlg.exec()

        # Try to auto-open the JSON once (non-blocking)
        if trivy_json_path and os.path.exists(trivy_json_path):
            try:
                # small delay then open so dialog appears first
                def _auto_open():
                    try:
                        os.startfile(trivy_json_path)
                    except Exception:
                        pass
                QTimer_single_shot(_auto_open)
            except Exception:
                # swallow any error but log to console
                traceback.print_exc()




    def load_containers(self):
        # Clear the table
        self.container_table.setRowCount(0)

        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.ID}}|{{.Names}}|{{.Image}}|{{.Status}}|{{.Command}}"],
                stdout=subprocess.PIPE,
                text=True,
                check=True
            )
            containers = result.stdout.strip().split("\n")
        except subprocess.CalledProcessError as e:
            containers = []
            print(f"Error fetching containers: {e}")

        # Populate the table with container data
        for i, line in enumerate(containers):
            if line.strip():
                container_data = line.split("|")
                self.container_table.insertRow(i)
                for j, data in enumerate(container_data):
                    self.container_table.setItem(i, j, QTableWidgetItem(data))

    def container_clicked(self, row, column):
        container_id = self.container_table.item(row, 0).text()
        container_name = self.container_table.item(row, 1).text()
        self.open_stats_tab(container_id, container_name)

    def open_stats_tab(self, container_id, container_name):
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == container_name:
                self.tabs.setCurrentIndex(i)
                return

        stats_tab = StatsTab(container_id, container_name, self.active_stats)
        self.tabs.addTab(stats_tab, container_name)
        self.tabs.setCurrentWidget(stats_tab)

    def QTimer_single_shot(callable_fn):
        """
        Schedule callable_fn to run on Qt main thread once (minimal wrapper).
        """
        QTimer.singleShot(10, callable_fn)

    def close_tab(self, index):
        widget = self.tabs.widget(index)
        if isinstance(widget, StatsTab):
            widget.stop_timer()
        self.tabs.removeTab(index)

    def recreate_containers_tab(self):
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == "Containers":
                return

        self.container_list_tab = QWidget()
        self.container_list_layout = QVBoxLayout()
        self.container_list_tab.setLayout(self.container_list_layout)
        self.tabs.addTab(self.container_list_tab, "Containers")
        self.load_containers()

    def recreate_network_tab(self):
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == "Network Connections":
                return
        self.network_tab = NetworkTab()
        self.tabs.addTab(self.network_tab, "Network Connections")
        self.tabs.setCurrentWidget(self.network_tab)

    def on_tab_changed(self, index):
        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            if isinstance(widget, StatsTab):
                if i == index:
                    widget.start_timer()
                else:
                    widget.stop_timer()

    def open_configure_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Configure Stats")
        layout = QFormLayout(dialog)

        checkboxes = {}
        for stat in self.active_stats.keys():
            checkbox = QCheckBox(stat)
            checkbox.setChecked(self.active_stats[stat])
            checkboxes[stat] = checkbox
            layout.addRow(stat, checkbox)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(lambda: self.apply_changes(dialog, checkboxes))
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        dialog.exec()

    def apply_changes(self, dialog, checkboxes):
        for stat, checkbox in checkboxes.items():
            self.active_stats[stat] = checkbox.isChecked()
        dialog.accept()

    def plot_network_graph(self):
        if not self.network_tab:
            return

        # Extract IPs from the network table
        data = []
        for row in range(self.network_tab.network_table.rowCount()):
            timestamp = self.network_tab.network_table.item(row, 0).text()
            source_ip = self.network_tab.network_table.item(row, 1).text()
            dest_ip = self.network_tab.network_table.item(row, 2).text()
            data.append([timestamp, source_ip, dest_ip])

        if not data:
            print("No network data available to plot.")
            return

        # Create a DataFrame
        df = pd.DataFrame(data, columns=["Timestamp", "Source IP", "Destination IP"])

        # Create a graph
        G = nx.Graph()

        # Count connections between each unique IP pair
        connection_counts = df.groupby(['Source IP', 'Destination IP']).size().reset_index(name='Count')

        # Add edges to the graph with connection counts as weights
        for _, row in connection_counts.iterrows():
            G.add_edge(row['Source IP'], row['Destination IP'], weight=row['Count'])

        # Draw the network graph
        plt.figure(figsize=(10, 8))

        # Set edge thickness based on connection frequency
        edges = G.edges(data=True)
        edge_weights = [edge_data['weight'] for _, _, edge_data in edges]

        # Draw the graph with node and edge configurations
        pos = nx.spring_layout(G, k=0.5)  # Layout for visualization
        nx.draw_networkx_nodes(G, pos, node_size=500, node_color="skyblue")
        nx.draw_networkx_edges(G, pos, width=edge_weights, alpha=0.5, edge_color="gray")
        nx.draw_networkx_labels(G, pos, font_size=10, font_family="sans-serif")

        # Add title and show plot
        plt.title("Network Graph of IP Connections")
        plt.axis("off")
        plt.tight_layout()
        plt.show()

    def plot_connection_heatmap(self):
        if not self.network_tab:
            return

        # Extract IPs and timestamps from the network table
        data = []
        for row in range(self.network_tab.network_table.rowCount()):
            timestamp = self.network_tab.network_table.item(row, 0).text()
            source_ip = self.network_tab.network_table.item(row, 1).text()
            dest_ip = self.network_tab.network_table.item(row, 2).text()
            data.append([timestamp, source_ip, dest_ip])

        if not data:
            print("No network data available to plot.")
            return

        # Create a DataFrame
        df = pd.DataFrame(data, columns=["Timestamp", "Source IP", "Destination IP"])

        # Convert the 'Timestamp' column to datetime format
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])

        # Create a unique connection label
        df['Connection'] = df['Source IP'] + " -> " + df['Destination IP']

        # Resample data by minute to get connection counts
        connection_counts = df.groupby(['Connection']).resample('1T', on='Timestamp').size().unstack(fill_value=0)

        if connection_counts.empty:
            print("No connection data available for the heatmap.")
            return

        # Plot heatmap
        plt.figure(figsize=(12, 8))
        sns.heatmap(connection_counts, cmap="YlGnBu", annot=False, cbar=True)

        # Set plot labels and title
        plt.title("Heatmap of IP Connection Counts Over Time")
        plt.xlabel("Time")
        plt.ylabel("IP Connections (Source -> Destination)")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

class StatsTab(QWidget):
    def __init__(self, container_id, container_name, active_stats):
        super().__init__()
        self.container_id = container_id
        self.container_name = container_name
        self.active_stats = active_stats
        self.last_fetch_time = datetime.utcnow() - timedelta(seconds=10)
        self.is_first_fetch = True

        # Variables to store stats over time
        self.stats_data = pd.DataFrame(columns=['Timestamp', 'CPU %', 'Memory %'])

        # UI initialization
        self.init_ui()

        # Worker thread for stats fetching
        self.running = True
        self.thread = Thread(target=self.fetch_stats, daemon=True)
        self.thread.start()
        
        #self.running = True
        #self.thread = Thread(target=self.fetch_logs, daemon=True)
        #self.thread.start()

    def init_ui(self):
        # Create the main layout
        layout = QVBoxLayout()

        # Add a label to show current stats
        self.stats_label = QLabel("Fetching stats...")
        layout.addWidget(self.stats_label)
        
        # Add a text area to display logs
        self.logs_area = QTextEdit()
        self.logs_area.setPlaceholderText("Fetching Logs...")
        self.logs_area.setReadOnly(True)
        layout.addWidget(self.logs_area)
        
        # Add a Matplotlib canvas for the graph
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        self.setLayout(layout)

    def fetch_stats(self):
        while self.running:
            try:
                format_parts = []
                if self.active_stats.get("CPU"):
                    format_parts.append("CPU: {{.CPUPerc}}")
                if self.active_stats.get("Memory"):
                    format_parts.append("Memory: {{.MemPerc}}")
                if self.active_stats.get("Network I/O"):
                    format_parts.append("Network I/O: {{.NetIO}}")
                if self.active_stats.get("Disk I/O"):
                    format_parts.append("Disk I/O: {{.BlockIO}}")

                format_string = " | ".join(format_parts)
                cmd = ["docker", "stats", self.container_id, "--no-stream", "--format", format_string]
                result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True, check=True)
                self.process_stats(result.stdout.strip())
            except subprocess.CalledProcessError as e:
                self.update_stats_label(f"Error fetching stats: {e}")
            time.sleep(2)
            
    def process_stats(self, raw_stats):
        try:
            # Parse the stats
            stats_parts = raw_stats.split(" | ")
            stats_dict = {}
            for part in stats_parts:
                key, value = part.split(": ")
                stats_dict[key.strip()] = value.strip()

            # Extract CPU and Memory usage
            cpu_usage = float(stats_dict.get("CPU", "0%").replace("%", ""))
            memory_usage = float(stats_dict.get("Memory", "0%").replace("%", ""))
            timestamp = datetime.now()

            # Update the DataFrame
            new_row = {'Timestamp': timestamp, 'CPU %': cpu_usage, 'Memory %': memory_usage}
            self.stats_data = pd.concat([self.stats_data, pd.DataFrame([new_row])], ignore_index=True)

            # Update the stats label
            self.update_stats_label(raw_stats)
            self.fetch_logs()
            
            # Update the graph every 10 seconds
            if len(self.stats_data) % 2 == 0:
                self.update_graph()
                self.fetch_logs()

        except Exception as e:
            self.update_stats_label(f"Error processing stats: {e}")
            
    def fetch_logs(self):
            if self.is_first_fetch:
            # First fetch: Get all logs
                cmd = ["docker", "logs", "-t", self.container_id]
                self.is_first_fetch = False
            else:
            # Subsequent fetches: Fetch logs since last time
                since_time = self.last_fetch_time.isoformat() + "Z"
                cmd = ["docker", "logs", "--since", since_time, "-t", self.container_id]

            result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True, check=True)
            self.last_fetch_time = datetime.utcnow()
            new_logs = result.stdout.strip()
            if new_logs:
                self.logs_area.append(new_logs)

    def update_stats_label(self, text):
        self.stats_label.setText(text)

    def update_graph(self):
        try:
            # Clear the previous plot
            self.figure.clear()

            # Add a subplot
            ax = self.figure.add_subplot(111)

            # Plot the CPU and Memory usage
            if not self.stats_data.empty:
                ax.plot(self.stats_data['Timestamp'], self.stats_data['CPU %'], label='CPU Usage (%)', color='blue')
                ax.plot(self.stats_data['Timestamp'], self.stats_data['Memory %'], label='Memory Usage (%)', color='orange')

                # Format the plot
                ax.set_title(f"Resource Usage Over Time for Container: {self.container_name}")
                ax.set_xlabel("Time")
                ax.set_ylabel("Usage (%)")
                ax.legend(loc="upper right")
                ax.grid()

            # Refresh the canvas
            self.canvas.draw()

        except Exception as e:
            print(f"Error updating graph: {e}")

    def start_timer(self):
        if not self.thread.is_alive():  # Check if the thread is already running
            self.running = True
            self.thread = Thread(target=self.fetch_stats, daemon=True)  # Recreate the thread if not alive
            self.thread.start()

    def stop_timer(self):
        self.running = False

class NetworkTab(QWidget):
    def __init__(self):
        super().__init__()

        self.TSHARK_PATH = r"C:\Program Files\Wireshark\tshark.exe"

        # ✅ YOUR EXACT WORKING INTERFACE (WSL + Docker)
        self.windows_interface = "4"

        self.ip_pattern = re.compile(r'(\d+\.\d+\.\d+\.\d+)')
        self.init_ui()

        self.running = True
        self.thread = Thread(target=self.capture_ips, daemon=True)
        self.thread.start()

    def init_ui(self):
        layout = QVBoxLayout()
        self.network_table = QTableWidget()
        self.network_table.setColumnCount(3)
        self.network_table.setHorizontalHeaderLabels(
            ["Timestamp", "Source IP", "Destination IP"]
        )
        self.network_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.network_table)
        self.setLayout(layout)

    def capture_ips(self):
        try:
            print("[DEBUG] Starting tshark on interface 4 (WSL/Docker)")

            process = subprocess.Popen(
                [
                    self.TSHARK_PATH,
                    "-i", self.windows_interface,
                    "-l",
                    "-n",
                    "-f", "ip"
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            while self.running:
                line = process.stdout.readline()
                if not line:
                    continue

                print("[PACKET]", line.strip())  # ✅ LIVE CONFIRMATION

                ips = self.ip_pattern.findall(line)
                if len(ips) >= 2:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.add_network_row(timestamp, ips[0], ips[1])

        except Exception as e:
            print(f"[NetworkTab ERROR]: {e}")

    def add_network_row(self, timestamp, source_ip, dest_ip):
        row = self.network_table.rowCount()
        self.network_table.insertRow(row)
        self.network_table.setItem(row, 0, QTableWidgetItem(timestamp))
        self.network_table.setItem(row, 1, QTableWidgetItem(source_ip))
        self.network_table.setItem(row, 2, QTableWidgetItem(dest_ip))

    def stop_capture(self):
        self.running = False


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ContainerMonitor()
    apply_modern_dark_theme(app)

    window.show()
    sys.exit(app.exec())


