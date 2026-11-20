import sys
import os
import shutil
import uuid

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from backend.renderer import VlogRenderer
from backend.analyzer import probe_video, generate_thumbnail
from backend.audio_manager import ensure_default_music_tracks

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SAMPLE_DIR = os.path.join(BASE_DIR, "sample_clips")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
THUMBNAIL_DIR = os.path.join(UPLOAD_DIR, "thumbnails")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
MUSIC_DIR = os.path.join(BASE_DIR, "assets", "music")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(THUMBNAIL_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 12 Pure, 100% Video Shots - ONLY Rajgad Fort, Clouds, Bastions, Suvela Machi, Balekilla Summit
# (Zero photos, zero bike/tea clips)
PURE_FORT_SHOTS = [
    {
        "filename": "VID_20261003_060226374.mp4",
        "start": 2.5,
        "end": 4.5,
        "hud": "स्वर्गाहुनी सुंदर...",
        "filter": "sahyadri_heritage"
    },
    {
        "filename": "VID_20261003_063208101.mp4",
        "start": 1.2,
        "end": 3.2,
        "hud": "",
        "filter": "sahyadri_heritage"
    },
    {
        "filename": "VID_20261003_063341762.mp4",
        "start": 1.0,
        "end": 3.0,
        "hud": "सह्याद्रीची स्वर्गीय पहाट 🌅",
        "filter": "sahyadri_heritage"
    },
    {
        "filename": "VID_20261003_071703675.mp4",
        "start": 1.5,
        "end": 3.5,
        "hud": "किल्ले राजगड 🪷",
        "filter": "sahyadri_heritage"
    },
    {
        "filename": "VID_20261003_071753649.mp4",
        "start": 2.0,
        "end": 4.0,
        "hud": "",
        "filter": "sahyadri_heritage"
    },
    {
        "filename": "VID_20261003_072008691.mp4",
        "start": 3.0,
        "end": 5.2,
        "hud": "अभेद्य बुरुज व तटबंदी",
        "filter": "sahyadri_heritage"
    },
    {
        "filename": "VID_20261003_073121917.mp4",
        "start": 2.0,
        "end": 4.0,
        "hud": "सह्याद्रीची अथांग भव्यता",
        "filter": "sahyadri_heritage"
    },
    {
        "filename": "VID_20261003_073320169.mp4",
        "start": 1.0,
        "end": 3.0,
        "hud": "",
        "filter": "sahyadri_heritage"
    },
    {
        "filename": "VID_20261003_084842217.mp4",
        "start": 2.0,
        "end": 4.2,
        "hud": "सुवेळा माची व नेढे 👁️",
        "filter": "sahyadri_heritage"
    },
    {
        "filename": "VID_20261003_094848344.mp4",
        "start": 1.5,
        "end": 3.5,
        "hud": "दुर्गदुर्गेश्वर राजगड 🧗",
        "filter": "sahyadri_heritage"
    },
    {
        "filename": "VID_20261003_095933138.mp4",
        "start": 4.0,
        "end": 6.4,
        "hud": "जय शिवराय! 🚩",
        "filter": "sahyadri_heritage"
    },
    {
        "filename": "VID_20261003_102806787.mp4",
        "start": 2.0,
        "end": 5.0,
        "hud": "राजांचा राजा - राजगड! 🪷⛰️",
        "filter": "sahyadri_heritage"
    }
]

def build_pure_rajgad_reel():
    print("🚀 Assembling PURE RAJGAD FORT 4K Ultra HD Instagram Reel (Videos Only)...")
    ensure_default_music_tracks()

    timeline = []
    for idx, shot in enumerate(PURE_FORT_SHOTS):
        fn = shot["filename"]
        src_path = os.path.join(SAMPLE_DIR, fn)
        if not os.path.exists(src_path):
            print(f"Warning: File {src_path} not found, skipping.")
            continue

        clip_id = f"pure_rajgad_{idx+1:02d}"
        dest_filename = f"{clip_id}_{fn}"
        dest_path = os.path.join(UPLOAD_DIR, dest_filename)
        if not os.path.exists(dest_path):
            shutil.copy2(src_path, dest_path)

        meta = probe_video(dest_path)
        thumb_name = f"thumb_{clip_id}.jpg"
        thumb_path = os.path.join(THUMBNAIL_DIR, thumb_name)
        generate_thumbnail(dest_path, thumb_path, timestamp=shot["start"])

        dur = shot["end"] - shot["start"]
        timeline_item = {
            "id": clip_id,
            "order": idx,
            "file_path": dest_path,
            "filename": fn,
            "start_time": shot["start"],
            "end_time": shot["end"],
            "final_duration": round(dur, 2),
            "speed_multiplier": 1.0,
            "hud_title": shot["hud"],
            "visual_filter": shot.get("filter", "sahyadri_heritage"),
            "mute_original_audio": True,
            "rotation": meta.get("rotation", 0),
            "is_vertical": meta.get("is_vertical", True)
        }
        timeline.append(timeline_item)

    print(f"✅ Prepared {len(timeline)} pure fort video shots (Total Duration: {sum(t['final_duration'] for t in timeline):.1f}s)")

    renderer = VlogRenderer(output_dir=OUTPUT_DIR)
    music_file = os.path.join(MUSIC_DIR, "sahyadri_folk_fusion.mp3")

    def progress_cb(pct, msg):
        print(f"[{pct}%] {msg}")

    output_filename = "rajgad_pure_fort_vertical_4k.mp4"
    rendered_path = renderer.render_vlog(
        timeline=timeline,
        output_filename=output_filename,
        aspect_ratio="9:16",
        resolution="4k",
        music_file=music_file,
        music_volume=1.0,
        voiceover_file=None,
        voiceover_volume=1.0,
        visual_filter="sahyadri_heritage",
        transition_type="fade",
        transition_duration=0.35,
        show_text_overlays=True,
        progress_callback=progress_cb
    )

    print(f"\n🎉 PURE RAJGAD 4K Ultra HD Instagram Reel Created Successfully at:\n{rendered_path}")
    return rendered_path

if __name__ == "__main__":
    build_pure_rajgad_reel()
