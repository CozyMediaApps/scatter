"""
Widget: System Audio Reactive Wave (loopback/monitor)

Goal:
- Drive an animation from *system output audio* (whatever is playing).

Dependencies:
  pip install sounddevice numpy

OS notes:
- Windows: uses WASAPI loopback if available (best).
- Linux: select a "Monitor of ..." device.
- macOS: requires a virtual device like BlackHole to capture system output.
"""

import math
import queue
import sys
import traceback
from dataclasses import dataclass
from typing import Optional, Tuple, List

import numpy as np
import sounddevice as sd

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QPen
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox
)


@dataclass
class AudioFrame:
    samples: np.ndarray  # mono float32


def _device_name(d) -> str:
    return d.get("name", "Unknown")


def _list_devices() -> List[Tuple[int, str, dict]]:
    devs = sd.query_devices()
    out = []
    for i, d in enumerate(devs):
        out.append((i, _device_name(d), d))
    return out


def _find_windows_wasapi_loopback_device() -> Optional[int]:
    """
    Best-effort: find a device likely to be a WASAPI loopback / stereo mix style.
    sounddevice exposes hostapi details; device names often contain these hints.
    """
    if not sys.platform.startswith("win"):
        return None

    try:
        hostapis = sd.query_hostapis()
        devices = sd.query_devices()
    except Exception:
        return None

    # Identify WASAPI hostapi indices
    wasapi_indices = {i for i, ha in enumerate(hostapis) if "WASAPI" in ha.get("name", "")}

    # Prefer explicit "loopback" / "stereo mix" / "what u hear" inputs on WASAPI
    hints = ("loopback", "stereo mix", "what u hear", "monitor")
    for idx, d in enumerate(devices):
        name = (_device_name(d) or "").lower()
        hostapi = d.get("hostapi")
        if hostapi in wasapi_indices and d.get("max_input_channels", 0) > 0:
            if any(h in name for h in hints):
                return idx

    # Fallback: any WASAPI input device (user can change if needed)
    for idx, d in enumerate(devices):
        hostapi = d.get("hostapi")
        if hostapi in wasapi_indices and d.get("max_input_channels", 0) > 0:
            return idx

    return None


class SystemAudioWave(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setMinimumHeight(220)
        self.setStyleSheet("""
            QWidget { background: #0b1220; border-radius: 10px; color: #e5e7eb; }
            QLabel#title { font-size: 15px; font-weight: 800; }
            QLabel#subtle { color: rgba(229,231,235,0.75); }
            QPushButton {
                background: #1f2937;
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 8px;
                padding: 6px 10px;
                font-weight: 700;
                color: #e5e7eb;
            }
            QPushButton:hover { background: #273449; }
            QPushButton:disabled { color: rgba(229,231,235,0.45); background: #111827; }
            QComboBox {
                background: #111827;
                border: 1px solid rgba(255,255,255,0.10);
                border-radius: 8px;
                padding: 6px 8px;
                color: #e5e7eb;
            }
        """)

        self._q: "queue.Queue[AudioFrame]" = queue.Queue(maxsize=30)
        self._stream = None

        # Visual state
        self._phase = 0.0
        self._energy = 0.0
        self._spectrum = np.zeros(64, dtype=np.float32)

        # UI
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        top = QHBoxLayout()
        title = QLabel("System Audio Wave")
        title.setObjectName("title")
        top.addWidget(title)
        top.addStretch(1)

        self.device_combo = QComboBox()
        self._devices = _list_devices()

        # Populate only devices that *can* provide input channels (monitor/loopback devices are "inputs")
        self._input_candidates = []
        for idx, name, d in self._devices:
            if d.get("max_input_channels", 0) > 0:
                self._input_candidates.append((idx, name))
                self.device_combo.addItem(name, idx)

        top.addWidget(self.device_combo)

        self.start_btn = QPushButton("Start")
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        top.addWidget(self.start_btn)
        top.addWidget(self.stop_btn)

        root.addLayout(top)

        hint = QLabel(
            "Select a loopback/monitor input for system audio. "
            "Windows often works automatically; macOS needs BlackHole; Linux uses “Monitor of …”."
        )
        hint.setObjectName("subtle")
        hint.setWordWrap(True)
        root.addWidget(hint)

        self._timer = QTimer(self)
        self._timer.setInterval(16)  # ~60fps
        self._timer.timeout.connect(self._tick)

        self.start_btn.clicked.connect(self._start)
        self.stop_btn.clicked.connect(self._stop)

        # Best-effort default selection
        default_idx = _find_windows_wasapi_loopback_device()
        if default_idx is not None:
            # Find it in the combo items
            for i in range(self.device_combo.count()):
                if self.device_combo.itemData(i) == default_idx:
                    self.device_combo.setCurrentIndex(i)
                    break

    def _start(self):
        if self._stream is not None:
            return

        if self.device_combo.count() == 0:
            print("System Audio Wave: No input devices found. You may need a monitor/loopback device.")
            return

        device_index = int(self.device_combo.currentData())
        print(f"System Audio Wave: starting capture on device {device_index}")

        samplerate = 44100
        blocksize = 1024

        def callback(indata, frames, time_info, status):
            if status:
                # log only briefly
                print(f"System Audio Wave stream status: {status}")

            mono = indata.mean(axis=1).astype(np.float32, copy=False)
            try:
                self._q.put_nowait(AudioFrame(samples=mono))
            except queue.Full:
                pass

        try:
            self._stream = sd.InputStream(
                device=device_index,
                channels=2,
                samplerate=samplerate,
                blocksize=blocksize,
                dtype="float32",
                callback=callback,
            )
            self._stream.start()
        except Exception as e:
            print("System Audio Wave: failed to start stream:")
            print(f"{e}\n{traceback.format_exc()}")
            self._stream = None
            return

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.device_combo.setEnabled(False)
        self._timer.start()

    def _stop(self):
        self._timer.stop()
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception as e:
                print(f"System Audio Wave: error stopping stream: {e}")
        self._stream = None

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.device_combo.setEnabled(True)

    def _tick(self):
        latest = None
        while True:
            try:
                latest = self._q.get_nowait()
            except queue.Empty:
                break

        if latest is not None:
            x = latest.samples

            # RMS energy
            rms = float(np.sqrt(np.mean(x * x) + 1e-9))
            self._energy = 0.86 * self._energy + 0.14 * rms

            # Spectrum
            fft = np.fft.rfft(x * np.hanning(len(x)))
            mag = np.abs(fft).astype(np.float32)[:64]
            if mag.max() > 0:
                mag = mag / mag.max()
            self._spectrum = 0.82 * self._spectrum + 0.18 * mag

            self._phase += 0.10 + self._energy * 2.2

        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        w = rect.width()
        h = rect.height()

        top_pad = 70
        y_mid = top_pad + (h - top_pad) * 0.55
        amp = (h - top_pad) * (0.10 + min(self._energy * 3.8, 0.60))

        pen = QPen(Qt.white)
        pen.setWidthF(2.3)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)

        pts = []
        n = 150
        for i in range(n):
            t = i / (n - 1)
            x = 12 + t * (w - 24)

            spec_i = int(t * (len(self._spectrum) - 1))
            bump = float(self._spectrum[spec_i])

            y = y_mid + math.sin(self._phase + t * 10.5) * amp * (0.50 + 0.85 * bump)
            pts.append((x, y))

        for i in range(len(pts) - 1):
            p.drawLine(int(pts[i][0]), int(pts[i][1]), int(pts[i + 1][0]), int(pts[i + 1][1]))

        # Level bar
        level = min(self._energy * 3.2, 1.0)
        bar_w = max(2, int((w - 24) * level))
        p.setPen(Qt.NoPen)
        p.setBrush(Qt.white)
        p.drawRoundedRect(12, h - 18, bar_w, 6, 3, 3)

        p.end()


def create_widget(parent=None):
    return SystemAudioWave(parent)