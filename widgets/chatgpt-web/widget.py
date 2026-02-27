"""
Widget: ChatGPT Web Embed

Requires:
  - PySide6-WebEngine
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl


CHATGPT_URL = "https://chat.openai.com/"  # or "https://chatgpt.com/"


def create_widget(parent=None):
    w = QWidget(parent)
    w.setStyleSheet("""
        QWidget { background: #0b1220; border-radius: 10px; }
        QPushButton {
            background: #1f2937;
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 8px;
            padding: 6px 10px;
            font-weight: 600;
            color: #e5e7eb;
        }
        QPushButton:hover { background: #273449; }
    """)

    root = QVBoxLayout(w)
    root.setContentsMargins(8, 8, 8, 8)
    root.setSpacing(8)

    # Small toolbar (compact)
    bar = QHBoxLayout()
    back_btn = QPushButton("←")
    fwd_btn = QPushButton("→")
    reload_btn = QPushButton("↻")
    home_btn = QPushButton("Home")

    bar.addWidget(back_btn)
    bar.addWidget(fwd_btn)
    bar.addWidget(reload_btn)
    bar.addStretch(1)
    bar.addWidget(home_btn)

    root.addLayout(bar)

    view = QWebEngineView(w)
    view.setUrl(QUrl(CHATGPT_URL))
    root.addWidget(view, 1)

    # Wiring
    back_btn.clicked.connect(view.back)
    fwd_btn.clicked.connect(view.forward)
    reload_btn.clicked.connect(view.reload)
    home_btn.clicked.connect(lambda: view.setUrl(QUrl(CHATGPT_URL)))

    return w