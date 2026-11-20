import os
import subprocess

MUSIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "music"))

TRACKS = {
    "sahyadri_folk_fusion": {
        "id": "sahyadri_folk_fusion",
        "name": "🏔️ Sahyadri Acoustic Folk Fusion (Trek Rhythm & Energy)",
        "freq": 293,
        "filter": "tremolo=f=4.5:d=0.5,equalizer=f=300:t=q:w=1.2:g=4,equalizer=f=2400:t=q:w=1.5:g=3,volume=0.35",
        "vibe": "folk_fusion"
    },
    "rajgad_heritage_flute": {
        "id": "rajgad_heritage_flute",
        "name": "🪷 Rajgad Heavenly Bansuri (Ethereal & Peaceful Sahyadri)",
        "freq": 440,
        "filter": "flanger=delay=6:depth=3,lowpass=f=1200,volume=0.3",
        "vibe": "heritage_flute"
    },
    "lofi_chill": {
        "id": "lofi_chill",
        "name": "☕ Lo-Fi Coding Beats (Chill & Focus)",
        "freq": 220,
        "filter": "tremolo=f=3:d=0.4,lowpass=f=900,volume=0.3",
        "vibe": "chill"
    },
    "upbeat_energy": {
        "id": "upbeat_energy",
        "name": "⚡ Energetic Synth (Fast Reel)",
        "freq": 330,
        "filter": "tremolo=f=6:d=0.6,volume=0.3",
        "vibe": "energetic"
    },
    "minimal_ambient": {
        "id": "minimal_ambient",
        "name": "🌌 Minimal Aesthetic (Calm Workday)",
        "freq": 174,
        "filter": "flanger=delay=8:depth=2,lowpass=f=600,volume=0.25",
        "vibe": "ambient"
    }
}

def ensure_default_music_tracks():
    """Generates clean procedural ambient music tracks if none exist."""
    os.makedirs(MUSIC_DIR, exist_ok=True)
    
    for key, info in TRACKS.items():
        file_path = os.path.join(MUSIC_DIR, f"{key}.mp3")
        if not os.path.exists(file_path):
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", f"sine=frequency={info['freq']}:duration=120",
                "-af", info["filter"],
                "-c:a", "libmp3lame",
                "-b:a", "192k",
                file_path
            ]
            try:
                subprocess.run(cmd, capture_output=True, check=True)
            except Exception as e:
                print(f"Notice: Music generation for {key}: {e}")

def get_available_music():
    ensure_default_music_tracks()
    tracks_list = []
    for k, v in TRACKS.items():
        file_path = os.path.join(MUSIC_DIR, f"{k}.mp3")
        tracks_list.append({
            "id": k,
            "name": v["name"],
            "vibe": v["vibe"],
            "file_path": file_path,
            "exists": os.path.exists(file_path)
        })
    return tracks_list
