import os
import subprocess
from backend.analyzer import probe_video

sample_dir = r"d:\Vlog\sample_clips"
thumb_inspect_dir = r"d:\Vlog\output\inspect_frames"
os.makedirs(thumb_inspect_dir, exist_ok=True)

video_files = sorted([f for f in os.listdir(sample_dir) if f.lower().endswith(('.mp4', '.mov'))])

print("Extracting representative frames from videos to verify content...")

for vf in video_files:
    fp = os.path.join(sample_dir, vf)
    meta = probe_video(fp)
    dur = meta["duration"]
    time_seek = min(2.0, dur / 2.0)
    out_img = os.path.join(thumb_inspect_dir, f"{vf}.jpg")
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(time_seek),
        "-i", fp,
        "-vframes", "1",
        "-vf", "scale=360:-1",
        "-q:v", "4",
        out_img
    ]
    subprocess.run(cmd, capture_output=True)

print(f"Extracted frames for {len(video_files)} videos into {thumb_inspect_dir}")
