import subprocess
import json
import os
from datetime import datetime

def probe_video(file_path: str) -> dict:
    """Extract deep metadata, rotation, and audio levels from video or photo."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Video or photo file not found: {file_path}")

    # Handle image files (JPG, PNG, WEBP, etc.)
    if file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.heic')):
        try:
            from PIL import Image
            with Image.open(file_path) as im:
                w, h = im.size
                return {
                    "duration": 3.0,
                    "width": w,
                    "height": h,
                    "raw_width": w,
                    "raw_height": h,
                    "rotation": 0,
                    "fps": 30.0,
                    "has_audio": False,
                    "is_vertical": h > w,
                    "is_image": True,
                    "creation_time": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                    "mean_volume": -99.0,
                    "is_silent": True
                }
        except Exception as e:
            print(f"Error opening image {file_path}: {e}")

    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        file_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
    except Exception as e:
        print(f"Error probing video {file_path}: {e}")
        return {
            "duration": 0,
            "width": 1920,
            "height": 1080,
            "fps": 30.0,
            "rotation": 0,
            "has_audio": False,
            "is_vertical": False,
            "creation_time": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
            "mean_volume": -99.0,
            "is_silent": True
        }

    format_info = data.get("format", {})
    streams = data.get("streams", [])
    
    video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

    duration = float(format_info.get("duration", 0.0))
    if duration == 0.0 and video_stream:
        duration = float(video_stream.get("duration", 0.0))

    raw_width = int(video_stream.get("width", 1920)) if video_stream else 1920
    raw_height = int(video_stream.get("height", 1080)) if video_stream else 1080
    
    # Extract rotation metadata (from stream tags or displaymatrix side data)
    rotation = 0
    if video_stream:
        vtags = video_stream.get("tags", {})
        if "rotate" in vtags:
            try:
                rotation = int(float(vtags["rotate"])) % 360
            except Exception:
                pass
        
        side_data = video_stream.get("side_data_list", [])
        for sd in side_data:
            if "rotation" in sd:
                try:
                    rotation = int(float(sd["rotation"])) % 360
                except Exception:
                    pass

    # If rotated 90 or 270 degrees, effective width and height are flipped
    if rotation in [90, 270, -90, -270]:
        width, height = raw_height, raw_width
    else:
        width, height = raw_width, raw_height

    # Calculate FPS
    fps = 30.0
    if video_stream and "r_frame_rate" in video_stream:
        try:
            num, den = video_stream["r_frame_rate"].split("/")
            if float(den) > 0:
                fps = float(num) / float(den)
        except Exception:
            fps = 30.0

    # Extract creation time
    tags = format_info.get("tags", {})
    creation_time = tags.get("creation_time") or tags.get("date")
    if not creation_time:
        creation_time = datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()

    has_audio = audio_stream is not None
    is_vertical = height > width

    # Detect audio volume/silence
    mean_volume, is_silent = detect_audio_activity(file_path, has_audio)

    return {
        "duration": round(duration, 2),
        "width": width,
        "height": height,
        "raw_width": raw_width,
        "raw_height": raw_height,
        "rotation": rotation,
        "fps": round(fps, 2),
        "has_audio": has_audio,
        "is_vertical": is_vertical,
        "creation_time": creation_time,
        "mean_volume": mean_volume,
        "is_silent": is_silent
    }

def detect_audio_activity(file_path: str, has_audio: bool) -> tuple[float, bool]:
    """Determine if clip has active speech/sound or is mostly silent in ~0.05s."""
    if not has_audio:
        return (-99.0, True)

    cmd = [
        "ffmpeg",
        "-y",
        "-vn",
        "-sn",
        "-i", file_path,
        "-t", "10",
        "-af", "volumedetect",
        "-f", "null",
        "-"
    ]

    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        output = res.stderr
        mean_vol = -99.0
        for line in output.splitlines():
            if "mean_volume:" in line:
                parts = line.split("mean_volume:")
                if len(parts) > 1:
                    mean_vol = float(parts[1].replace("dB", "").strip())
        
        is_silent = mean_vol < -38.0
        return (mean_vol, is_silent)
    except Exception as e:
        print(f"Error detecting volume: {e}")
        return (-50.0, True)

def generate_thumbnail(file_path: str, output_thumb_path: str, timestamp: float = 1.0) -> bool:
    """Extract a representative thumbnail frame from video or photo with fast keyframe seek."""
    os.makedirs(os.path.dirname(output_thumb_path), exist_ok=True)

    # Fast direct thumbnail for images
    if file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.heic')):
        try:
            from PIL import Image
            with Image.open(file_path) as im:
                im = im.convert("RGB")
                im.thumbnail((480, 480))
                im.save(output_thumb_path, "JPEG", quality=85)
                return True
        except Exception as e:
            print(f"Image thumbnail error for {file_path}: {e}")

    cmd = [
        "ffmpeg",
        "-y",
        "-ss", str(timestamp),
        "-i", file_path,
        "-vframes", "1",
        "-vf", "scale=480:-1:flags=fast_bilinear",
        "-q:v", "3",
        "-threads", "0",
        output_thumb_path
    ]
    try:
        subprocess.run(cmd, capture_output=True, check=True)
        return True
    except Exception:
        try:
            cmd[2] = "0.0"
            subprocess.run(cmd, capture_output=True, check=True)
            return True
        except Exception as e:
            print(f"Thumbnail error: {e}")
            return False

def probe_audio(file_path: str) -> dict:
    """Extract exact duration and sample rate from audio file using ffprobe."""
    if not os.path.exists(file_path):
        return {"duration": 0.0}

    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        file_path
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        fmt = data.get("format", {})
        dur = float(fmt.get("duration", 0.0))
        return {"duration": round(dur, 2)}
    except Exception as e:
        print(f"probe_audio error: {e}")
        return {"duration": 0.0}

