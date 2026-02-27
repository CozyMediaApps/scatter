# 🎵 System Audio Reactive Wave Widget

An animated, audio-reactive waveform widget for the **Scatter
Dashboard**.

This widget captures **system output audio** (whatever is currently
playing on your computer) and renders a smooth, animated waveform that
reacts in real time.

------------------------------------------------------------------------

## ✨ Features

-   Real-time waveform animation
-   RMS energy detection
-   Basic FFT spectrum shaping
-   Automatic WASAPI loopback detection (Windows)
-   60 FPS rendering via `QTimer`
-   Dark, minimal dashboard styling
-   Fully self-contained PySide6 widget

------------------------------------------------------------------------

## 📦 Requirements

Install required packages:

``` bash
pip install sounddevice numpy
```

Requires: - PySide6 - A valid audio input device capable of capturing
system output

------------------------------------------------------------------------

## 🖥 OS Setup Guide

### 🪟 Windows

-   Works with WASAPI loopback
-   May auto-detect "Stereo Mix" or similar device
-   If not visible, enable Stereo Mix in Sound settings

### 🐧 Linux

Select an input device named:

    Monitor of <your audio output>

Example:

    Monitor of Built-in Audio Analog Stereo

### 🍎 macOS

macOS does not provide built-in system audio loopback.

You must install a virtual device such as: - BlackHole (recommended) -
Loopback - Soundflower

Setup: 1. Install BlackHole (2ch) 2. Create a Multi-Output Device
(Built-in Output + BlackHole) 3. Set system output to that device 4.
Select BlackHole in the widget dropdown

------------------------------------------------------------------------

## 🚀 How It Works

1.  Enumerates available audio input devices.
2.  Captures audio via `sounddevice.InputStream`.
3.  Computes:
    -   RMS energy
    -   FFT spectrum
4.  Smooths values over time.
5.  Renders animated waveform via `QPainter`.

Audio capture runs in a callback thread and does not block the UI.

------------------------------------------------------------------------

## 🎛 Controls

-   **Device Dropdown** --- Select loopback / monitor input
-   **Start** --- Begin capturing audio
-   **Stop** --- Stop capture

------------------------------------------------------------------------

## ⚠ Troubleshooting

**No devices listed** - Ensure your system exposes a recording input -
On macOS, install BlackHole - On Windows, enable Stereo Mix

**No animation** - Ensure audio is playing - Verify correct device is
selected

**Audio glitches** - Reduce CPU load - Adjust blocksize (advanced users)

------------------------------------------------------------------------

## 🏷 Widget Entry Point

``` python
def create_widget(parent=None):
    return SystemAudioWave(parent)
```

Compatible with Scatter Dashboard's widget grid system.
