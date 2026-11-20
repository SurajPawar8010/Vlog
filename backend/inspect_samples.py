import os
import json
from backend.analyzer import probe_video
from PIL import Image

sample_dir = r"d:\Vlog\sample_clips"
files = sorted(os.listdir(sample_dir))

images = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
videos = [f for f in files if f.lower().endswith(('.mp4', '.mov'))]

print(f"=== RAJGAD SAMPLE CLIPS SUMMARY ===")
print(f"Total Files: {len(files)} | High-Res HDR Images: {len(images)} | Video Clips: {len(videos)}")

print("\n--- VIDEO CLIPS CHRONOLOGY ---")
for v in videos:
    fp = os.path.join(sample_dir, v)
    try:
        meta = probe_video(fp)
        w, h, dur = meta['width'], meta['height'], meta['duration']
        vert = meta['is_vertical']
        time_part = v.replace("VID_20261003_", "").replace(".mp4", "")
        # format HH:MM:SS
        if len(time_part) >= 6:
            hh, mm, ss = time_part[:2], time_part[2:4], time_part[4:6]
            formatted_time = f"{hh}:{mm}:{ss}"
        else:
            formatted_time = time_part
        print(f"[{formatted_time}] {v} -> {w}x{h} ({dur}s) | {'Vertical 9:16' if vert else 'Landscape'}")
    except Exception as e:
        print(f"{v}: {e}")

print("\n--- PHOTO SAMPLES (HDR / High-Res) ---")
for im in images[::3]:  # sample every 3rd image
    fp = os.path.join(sample_dir, im)
    try:
        with Image.open(fp) as img:
            time_part = im.replace("IMG_20261003_", "").replace("_HDR.jpg", "").replace(".jpg", "")
            if len(time_part) >= 6:
                hh, mm, ss = time_part[:2], time_part[2:4], time_part[4:6]
                formatted_time = f"{hh}:{mm}:{ss}"
            else:
                formatted_time = time_part
            print(f"[{formatted_time}] {im} -> {img.width}x{img.height} ({img.format})")
    except Exception as e:
        print(f"{im}: {e}")
