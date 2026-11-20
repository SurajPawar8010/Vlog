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

# 14 Curated Highlight Shots (Chronological Story: Night Climb -> Golden Sunrise -> Padmavati -> Suvela Machi -> Balekilla Summit)
SELECTED_SHOTS = [
    {
        "filename": "VID_20261003_023644627.mp4",
        "start": 1.0,
        "end": 3.0,
        "hud": "मध्यरात्री २:३० वाजता... राजगडाची वाट",
        "trans": "fade"
    },
    {
        "filename": "VID_20261003_034215705.mp4",
        "start": 0.5,
        "end": 2.5,
        "hud": "दाट अंधार आणि गार वारा",
        "trans": "fade"
    },
    {
        "filename": "IMG_20261003_060145386_HDR.jpg",
        "start": 0.0,
        "end": 2.0,
        "hud": "पहाटेची सोनेरी किरणे...",
        "trans": "zoomin"
    },
    {
        "filename": "VID_20261003_060226374.mp4",
        "start": 2.0,
        "end": 4.2,
        "hud": "सह्याद्रीची स्वर्गीय पहाट 🌅",
        "trans": "fade"
    },
    {
        "filename": "IMG_20261003_061314215_HDR.jpg",
        "start": 0.0,
        "end": 2.0,
        "hud": "स्वर्गाहुनी सुंदर राजगड 🪷",
        "trans": "fade"
    },
    {
        "filename": "VID_20261003_063208101.mp4",
        "start": 1.0,
        "end": 3.0,
        "hud": "ढगांच्या चादरीवर गडकोट",
        "trans": "zoomin"
    },
    {
        "filename": "VID_20261003_071703675.mp4",
        "start": 1.0,
        "end": 3.0,
        "hud": "किल्ले राजगड - राजांचा राजा!",
        "trans": "fade"
    },
    {
        "filename": "VID_20261003_072008691.mp4",
        "start": 2.0,
        "end": 4.0,
        "hud": "अभेद्य बुरुज व तटबंदी",
        "trans": "fade"
    },
    {
        "filename": "IMG_20261003_072504215_HDR.jpg",
        "start": 0.0,
        "end": 2.0,
        "hud": "पद्मावती माची ⛰️",
        "trans": "zoomin"
    },
    {
        "filename": "VID_20261003_073121917.mp4",
        "start": 1.5,
        "end": 3.5,
        "hud": "सह्याद्रीची अथांग भव्यता",
        "trans": "fade"
    },
    {
        "filename": "VID_20261003_084842217.mp4",
        "start": 2.0,
        "end": 4.0,
        "hud": "सुवेळा माची व नेढे 👁️",
        "trans": "fade"
    },
    {
        "filename": "IMG_20261003_085718275_HDR.jpg",
        "start": 0.0,
        "end": 2.0,
        "hud": "बालेकिल्ल्याची चढाई 🧗",
        "trans": "zoomin"
    },
    {
        "filename": "VID_20261003_095933138.mp4",
        "start": 3.0,
        "end": 5.2,
        "hud": "जय शिवराय! 🚩",
        "trans": "fadewhite"
    },
    {
        "filename": "IMG_20261003_102831528_HDR.jpg",
        "start": 0.0,
        "end": 2.2,
        "hud": "राजियांचा राजगड 🪷⛰️",
        "trans": "fade"
    }
]

def build_rajgad_reel():
    print("🚀 Starting Rajgad Viral Reel Assembly...")
    ensure_default_music_tracks()

    timeline = []
    for idx, shot in enumerate(SELECTED_SHOTS):
        fn = shot["filename"]
        src_path = os.path.join(SAMPLE_DIR, fn)
        if not os.path.exists(src_path):
            print(f"Warning: File {src_path} not found, skipping.")
            continue

        # Copy to uploads for project reference
        clip_id = f"rajgad_{idx+1:02d}"
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
            "visual_filter": "sahyadri_heritage",
            "mute_original_audio": True,
            "rotation": meta.get("rotation", 0),
            "is_vertical": meta.get("is_vertical", True)
        }
        timeline.append(timeline_item)

    print(f"✅ Prepared {len(timeline)} synched clips (Total duration: {sum(t['final_duration'] for t in timeline):.1f}s)")

    renderer = VlogRenderer(output_dir=OUTPUT_DIR)
    music_file = os.path.join(MUSIC_DIR, "sahyadri_folk_fusion.mp3")

    def progress_cb(pct, msg):
        print(f"[{pct}%] {msg}")

    output_filename = "rajgad_fort_viral_reel_4k.mp4"
    rendered_path = renderer.render_vlog(
        timeline=timeline,
        output_filename=output_filename,
        aspect_ratio="9:16",
        resolution="4k",
        music_file=music_file,
        music_volume=0.45,
        voiceover_file=None,
        voiceover_volume=1.0,
        visual_filter="sahyadri_heritage",
        transition_type="fade",
        transition_duration=0.35,
        show_text_overlays=True,
        progress_callback=progress_cb
    )

    print(f"\n🎉 Master 4K Ultra HD Instagram Reel Created Successfully at:\n{rendered_path}")
    return rendered_path

if __name__ == "__main__":
    build_rajgad_reel()
