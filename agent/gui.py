#!/usr/bin/env python3
"""
Computer Use Agent - GUI Interface.

A simple GUI for running the agent with settings management.
"""

import sys
import os
import json
import threading
from pathlib import Path
from typing import Optional

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QDialog, QFormLayout,
    QSpinBox, QMessageBox, QFrame, QSplitter, QGroupBox,
    QSystemTrayIcon, QMenu, QAction, QInputDialog,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QMetaObject, Q_ARG, Qt as QtCore
from PyQt5.QtGui import QFont, QIcon, QTextCursor, QPixmap

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent import (
    ComputerUseAgent,
    OpenAICompatibleLLM,
    OmniParserClient,
)


# =============================================================================
# Configuration
# =============================================================================

def _get_config_dir() -> Path:
    """Get platform-appropriate config directory."""
    if sys.platform == "win32":
        # Windows: %APPDATA%\ComputerUseAgent
        base = os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")
        return Path(base) / "ComputerUseAgent"
    elif sys.platform == "darwin":
        # macOS: ~/Library/Application Support/ComputerUseAgent
        return Path.home() / "Library" / "Application Support" / "ComputerUseAgent"
    else:
        # Linux: ~/.config/computer_use_agent
        return Path.home() / ".config" / "computer_use_agent"


CONFIG_FILE = _get_config_dir() / "config.json"

DEFAULT_CONFIG = {
    "llm_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "llm_api_key": "",
    "llm_model": "qwen-vl-max",
    "omniparser_url": "",  # Empty = local mode
    "max_steps": 20,
    "screen": 0,  # Screen index (0=primary, 1+=others)
}


def load_config() -> dict:
    """Load configuration from file."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                config = json.load(f)
                # Merge with defaults for any missing keys
                return {**DEFAULT_CONFIG, **config}
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def save_config(config: dict):
    """Save configuration to file."""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


# =============================================================================
# Agent Worker Thread
# =============================================================================

class AgentWorker(QThread):
    """Worker thread for running the agent."""

    log_signal = pyqtSignal(str)  # Emit log messages
    finished_signal = pyqtSignal(bool, str)  # Emit (success, message)
    ask_user_signal = pyqtSignal(str)  # Emit question to ask user
    talk_to_user_signal = pyqtSignal(str)  # Emit message to show user

    def __init__(self, goal: str, config: dict):
        super().__init__()
        self.goal = goal
        self.config = config
        self._stop_flag = False

        # For user interaction
        self._user_response: Optional[str] = None
        self._response_event = threading.Event()

    def stop(self):
        """Request the agent to stop."""
        self._stop_flag = True
        # Unblock any waiting ask_user call
        self._response_event.set()

    def log(self, message: str):
        """Emit a log message."""
        self.log_signal.emit(message)

    def set_user_response(self, response: str):
        """Set the user's response (called from main thread)."""
        self._user_response = response
        self._response_event.set()

    def _ask_user(self, question: str) -> str:
        """Ask user a question and wait for response."""
        self._user_response = None
        self._response_event.clear()
        self.ask_user_signal.emit(question)
        # Wait for response
        self._response_event.wait()
        return self._user_response or ""

    def _talk_to_user(self, message: str):
        """Show a message to the user."""
        self.talk_to_user_signal.emit(message)

    def run(self):
        """Run the agent."""
        try:
            self.log(f"Goal: {self.goal}")
            self.log("-" * 50)

            # Create LLM
            self.log("Initializing LLM...")
            llm = OpenAICompatibleLLM(
                base_url=self.config["llm_url"],
                api_key=self.config["llm_api_key"],
                model=self.config["llm_model"],
            )

            # Create OmniParser client
            omniparser_url = self.config.get("omniparser_url", "").strip()
            if not omniparser_url:
                self.log("Error: OmniParser URL not configured")
                self.finished_signal.emit(False, "OmniParser URL not set")
                return

            self.log(f"Connecting to OmniParser: {omniparser_url}")
            omniparser = OmniParserClient(server_url=omniparser_url)

            if not omniparser.is_available():
                self.log("Error: OmniParser server not available")
                self.finished_signal.emit(False, "OmniParser server unavailable")
                return

            # Create agent
            screen_idx = self.config.get("screen", 0)
            self.log(f"Creating agent (screen={screen_idx})...")
            agent = ComputerUseAgent(
                llm=llm,
                omniparser=omniparser,
                ask_user_callback=self._ask_user,
                talk_to_user_callback=self._talk_to_user,
                screen=screen_idx,
            )

            # Run agent
            max_steps = self.config.get("max_steps", 20)
            self.log(f"Starting (max {max_steps} steps)...")
            self.log("=" * 50)

            agent.reset()

            for step_num in range(max_steps):
                if self._stop_flag:
                    self.log("\n[Stopped by user]")
                    self.finished_signal.emit(False, "Stopped by user")
                    return

                self.log(f"\n--- Step {step_num + 1} ---")

                try:
                    result = agent.step(self.goal)

                    self.log(f"Reason: {result.reason}")
                    self.log(f"Action: {result.action.action_type}")
                    self.log(f"Summary: {result.summary}")

                    if result.done:
                        status = result.action.goal_status or "completed"
                        self.log(f"\n{'=' * 50}")
                        self.log(f"Task {status} after {step_num + 1} steps")
                        self.finished_signal.emit(True, f"Task {status}")
                        return

                except Exception as e:
                    self.log(f"Error: {e}")
                    raise

            self.log(f"\nMax steps ({max_steps}) reached")
            self.finished_signal.emit(False, "Max steps reached")

        except Exception as e:
            self.log(f"\nError: {e}")
            self.finished_signal.emit(False, str(e))


# =============================================================================
# Settings Dialog
# =============================================================================

class SettingsDialog(QDialog):
    """Settings dialog for configuring the agent."""

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config.copy()
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Settings")
        self.setMinimumWidth(450)

        layout = QVBoxLayout(self)

        # LLM Settings Group
        llm_group = QGroupBox("LLM Settings")
        llm_layout = QFormLayout()

        self.llm_url_edit = QLineEdit(self.config.get("llm_url", ""))
        self.llm_url_edit.setPlaceholderText("https://api.openai.com/v1")
        llm_layout.addRow("API URL:", self.llm_url_edit)

        self.llm_key_edit = QLineEdit(self.config.get("llm_api_key", ""))
        self.llm_key_edit.setEchoMode(QLineEdit.Password)
        self.llm_key_edit.setPlaceholderText("sk-...")
        llm_layout.addRow("API Key:", self.llm_key_edit)

        self.llm_model_edit = QLineEdit(self.config.get("llm_model", ""))
        self.llm_model_edit.setPlaceholderText("gpt-4o / qwen-vl-max")
        llm_layout.addRow("Model:", self.llm_model_edit)

        llm_group.setLayout(llm_layout)
        layout.addWidget(llm_group)

        # OmniParser Settings Group
        parser_group = QGroupBox("OmniParser Settings")
        parser_layout = QFormLayout()

        self.parser_url_edit = QLineEdit(self.config.get("omniparser_url", ""))
        self.parser_url_edit.setPlaceholderText("http://server:8000 (required)")
        parser_layout.addRow("Server URL:", self.parser_url_edit)

        parser_group.setLayout(parser_layout)
        layout.addWidget(parser_group)

        # Agent Settings Group
        agent_group = QGroupBox("Agent Settings")
        agent_layout = QFormLayout()

        self.max_steps_spin = QSpinBox()
        self.max_steps_spin.setRange(1, 100)
        self.max_steps_spin.setValue(self.config.get("max_steps", 20))
        agent_layout.addRow("Max Steps:", self.max_steps_spin)

        self.screen_spin = QSpinBox()
        self.screen_spin.setRange(0, 16)
        self.screen_spin.setValue(self.config.get("screen", 0))
        self.screen_spin.setToolTip("Screen index: 0=primary, 1+=others")
        agent_layout.addRow("Screen:", self.screen_spin)

        agent_group.setLayout(agent_layout)
        layout.addWidget(agent_group)

        # Buttons
        btn_layout = QHBoxLayout()

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def get_config(self) -> dict:
        """Get the updated configuration."""
        return {
            "llm_url": self.llm_url_edit.text().strip(),
            "llm_api_key": self.llm_key_edit.text().strip(),
            "llm_model": self.llm_model_edit.text().strip(),
            "omniparser_url": self.parser_url_edit.text().strip(),
            "max_steps": self.max_steps_spin.value(),
            "screen": self.screen_spin.value(),
        }


# =============================================================================
# Agent Message Dialog
# =============================================================================

class AgentMessageDialog(QDialog):
    """Dialog for showing messages from the agent."""

    def __init__(self, message: str, parent=None):
        super().__init__(parent)
        self.setup_ui(message)

    def setup_ui(self, message: str):
        self.setWindowTitle("Agent Message")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # Message label
        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setFont(QFont("Sans", 11))
        msg_label.setStyleSheet("padding: 10px;")
        layout.addWidget(msg_label)

        # OK button
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setMinimumHeight(30)
        layout.addWidget(ok_btn)


# =============================================================================
# Log Viewer Dialog
# =============================================================================

class LogViewerDialog(QDialog):
    """Dialog for viewing execution logs."""

    def __init__(self, log_text: str, parent=None):
        super().__init__(parent)
        self.setup_ui(log_text)

    def setup_ui(self, log_text: str):
        self.setWindowTitle("Execution Log")
        self.resize(600, 500)

        layout = QVBoxLayout(self)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setFont(QFont("Monospace", 10))
        self.text_edit.setText(log_text)
        layout.addWidget(self.text_edit)

        # Buttons
        btn_layout = QHBoxLayout()

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(lambda: self.text_edit.clear())

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)

        btn_layout.addWidget(clear_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)


# =============================================================================
# Main Window
# =============================================================================

class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.worker: Optional[AgentWorker] = None
        self.log_text = ""
        self.setup_ui()
        self.setup_tray()

    def setup_ui(self):
        self.setWindowTitle("Computer Use Agent")
        self.setMinimumSize(400, 200)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # Title
        title = QLabel("Computer Use Agent")
        title.setFont(QFont("Sans", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Input section
        input_label = QLabel("Enter your goal:")
        layout.addWidget(input_label)

        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("e.g., Open Firefox and search for Python tutorials")
        self.input_edit.returnPressed.connect(self.start_agent)
        layout.addWidget(self.input_edit)

        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: gray;")
        layout.addWidget(self.status_label)

        # Buttons
        btn_layout = QHBoxLayout()

        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self.start_agent)
        self.start_btn.setMinimumHeight(35)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_agent)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setMinimumHeight(35)

        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)

        layout.addLayout(btn_layout)

        # Bottom buttons
        bottom_layout = QHBoxLayout()

        settings_btn = QPushButton("Settings")
        settings_btn.clicked.connect(self.show_settings)

        log_btn = QPushButton("View Log")
        log_btn.clicked.connect(self.show_log)

        bottom_layout.addWidget(settings_btn)
        bottom_layout.addWidget(log_btn)

        layout.addLayout(bottom_layout)

        # Stretch to push everything up
        layout.addStretch()

    def setup_tray(self):
        """Setup system tray icon."""
        # Create a simple icon (blue square)
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.blue)

        self.tray_icon = QSystemTrayIcon(QIcon(pixmap), self)
        self.tray_icon.setToolTip("Computer Use Agent")

        # Tray menu
        tray_menu = QMenu()

        show_action = QAction("Show Window", self)
        show_action.triggered.connect(self.show_window)
        tray_menu.addAction(show_action)

        self.tray_stop_action = QAction("Stop Agent", self)
        self.tray_stop_action.triggered.connect(self.stop_agent)
        self.tray_stop_action.setEnabled(False)
        tray_menu.addAction(self.tray_stop_action)

        tray_menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

    def show_window(self):
        """Show and activate the main window."""
        self.show()
        self.activateWindow()
        self.raise_()

    def on_tray_activated(self, reason):
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window()

    def quit_app(self):
        """Quit the application."""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(2000)
        self.tray_icon.hide()
        QApplication.quit()

    def start_agent(self):
        """Start the agent."""
        goal = self.input_edit.text().strip()
        if not goal:
            QMessageBox.warning(self, "Warning", "Please enter a goal.")
            return

        # Check config
        if not self.config.get("llm_api_key"):
            QMessageBox.warning(self, "Warning", "Please set LLM API key in Settings.")
            self.show_settings()
            return

        if not self.config.get("omniparser_url"):
            QMessageBox.warning(self, "Warning", "Please set OmniParser URL in Settings.")
            self.show_settings()
            return

        # Clear log
        self.log_text = ""

        # Update UI
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.input_edit.setEnabled(False)
        self.status_label.setText("Running...")
        self.status_label.setStyleSheet("color: blue;")

        # Hide window to avoid interfering with screenshots
        self.hide()

        # Update tray
        self.tray_stop_action.setEnabled(True)
        self.tray_icon.setToolTip("Computer Use Agent - Running...")

        # Start worker
        self.worker = AgentWorker(goal, self.config)
        self.worker.log_signal.connect(self.on_log)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.ask_user_signal.connect(self.on_ask_user)
        self.worker.talk_to_user_signal.connect(self.on_talk_to_user)
        self.worker.start()

    def stop_agent(self):
        """Stop the agent."""
        if self.worker:
            self.worker.stop()
            self.status_label.setText("Stopping...")

    def on_log(self, message: str):
        """Handle log messages."""
        self.log_text += message + "\n"
        print(message)  # Also print to console

    def on_ask_user(self, question: str):
        """Handle ask_user from agent - show input dialog."""
        # Show window temporarily for user interaction
        self.show()
        self.activateWindow()
        self.raise_()

        response, ok = QInputDialog.getText(
            self,
            "Agent Question",
            question,
            QLineEdit.Normal,
            ""
        )

        if ok:
            self.log_text += f"Agent asked: {question}\n"
            self.log_text += f"User response: {response}\n"
        else:
            response = ""
            self.log_text += f"Agent asked: {question}\n"
            self.log_text += "User cancelled\n"

        # Hide window again and send response
        self.hide()
        if self.worker:
            self.worker.set_user_response(response)

    def on_talk_to_user(self, message: str):
        """Handle talk_to_user from agent - show message dialog."""
        # Show window temporarily for user interaction
        self.show()
        self.activateWindow()
        self.raise_()

        self.log_text += f"Agent message: {message}\n"

        dialog = AgentMessageDialog(message, self)
        dialog.exec_()

        # Hide window again
        self.hide()

    def on_finished(self, success: bool, message: str):
        """Handle agent completion."""
        # Show window again
        self.show()
        self.activateWindow()
        self.raise_()

        # Update tray
        self.tray_stop_action.setEnabled(False)
        self.tray_icon.setToolTip("Computer Use Agent")

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.input_edit.setEnabled(True)

        if success:
            self.status_label.setText(f"Done: {message}")
            self.status_label.setStyleSheet("color: green;")
        else:
            self.status_label.setText(f"Stopped: {message}")
            self.status_label.setStyleSheet("color: orange;")

        self.worker = None

    def show_settings(self):
        """Show settings dialog."""
        dialog = SettingsDialog(self.config, self)
        if dialog.exec_() == QDialog.Accepted:
            self.config = dialog.get_config()
            save_config(self.config)

    def show_log(self):
        """Show log viewer."""
        dialog = LogViewerDialog(self.log_text or "(No logs yet)", self)
        dialog.exec_()

    def closeEvent(self, event):
        """Handle window close."""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self, "Confirm Exit",
                "Agent is running. Stop and exit?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.worker.stop()
                self.worker.wait(3000)
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


# =============================================================================
# Entry Point
# =============================================================================

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
