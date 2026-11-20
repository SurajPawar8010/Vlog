import os
import subprocess
from backend.analyzer import probe_video

sample_dir = r"d:\Vlog\sample_clips"
video_files = sorted([f for f in os.listdir(sample_dir) if f.lower().endswith(('.mp4', '.mov'))])

print(f"Total video clips available: {len(video_files)}")

for idx, vf in enumerate(video_files):
    fp = os.path.join(sample_dir, vf)
    try:
        meta = probe_video(fp)
        dur = meta["duration"]
        w = meta["width"]
        h = meta["height"]
        vert = meta["is_vertical"]
        time_part = vf.replace("VID_20261003_", "").replace(".mp4", "")
        print(f"[{idx+1:02d}] {vf} ({time_part[:2]}:{time_part[2:4]}) -> {w}x{h}, {dur}s, {'Vert 9:16' if vert else 'Land 16:9'}")
    except Exception as e:
        print(f"[{idx+1:02d}] {vf}: {e}")
