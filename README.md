# ⚡ AutoVlog AI Studio (100% Local Engine)

A privacy-focused, automated video editing studio that runs entirely on your local machine. Drop your daily raw work clips, and let the system craft a daily vlog in 9:16 vertical (Reels/Shorts/TikTok) or 16:9 widescreen format.

---

## 🚀 Quick Start (1-Click Launch)

Double-click **`run.bat`** or run:

```bash
python start.py
```

Then open your browser to **`http://localhost:8000`** (it opens automatically!).

---

## 🌟 Key Features

1. **100% Local & Private**: All video probing, silence analysis, and FFmpeg rendering happen directly on your machine.
2. **AI Narrative & Pacing**:
   - **Hook (0–3s)**: Punchy opener cut.
   - **Deep Work Timelapses (3x–6x)**: Automatically speeds up silent work/coding sessions.
   - **Speaking Highlights (1x)**: Preserves voice, clarity, and pacing when talking.
   - **Outro Wrap-up**: Day wrap-up with HUD tags.
3. **Smart Vertical Canvas (9:16)**:
   - Formats horizontal 16:9 clips into vertical 1080x1920 with blurred background styling.
4. **Auto Background Music & Audio Ducking**:
   - Built-in Lo-Fi beats, Upbeat synth, and Minimal ambient tracks.
   - Auto-lowers music volume when speech is present.
5. **Real-time Live Render Progress**:
   - Visual progress bar streamed via Server-Sent Events (SSE).

---

## 📁 Project Structure

```
d:/Vlog/
├── backend/
│   ├── analyzer.py        # Metadata & silence detection via FFprobe
│   ├── story_engine.py    # AI Narrative Arc & timeline planner
│   ├── renderer.py        # FFmpeg master video assembly & audio ducking
│   ├── audio_manager.py   # Procedural BGM music manager
│   └── main.py            # FastAPI REST & SSE backend
├── frontend/
│   ├── index.html         # Modern dark-mode Dashboard UI
│   ├── style.css          # Glassmorphism & responsive styles
│   └── app.js             # Drag-and-drop, SSE listener, live player
├── sample_clips/          # Ready-to-use demo clips for testing
├── uploads/               # Raw ingested video footage
├── output/                # Rendered daily vlogs (MP4)
├── start.py               # Application launcher
└── run.bat                # 1-Click Windows batch launcher
```
