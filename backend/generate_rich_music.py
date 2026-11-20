import os
import subprocess

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MUSIC_DIR = os.path.join(BASE_DIR, "assets", "music")
os.makedirs(MUSIC_DIR, exist_ok=True)

def generate_rich_sahyadri_music():
    out_path = os.path.join(MUSIC_DIR, "sahyadri_folk_fusion.mp3")
    
    # 30-second rich multi-layered folk fusion music track (Bansuri flute chords + Dhol percussion beat + acoustic swell)
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=60", # Melody A4
        "-f", "lavfi", "-i", "sine=frequency=554.37:duration=60", # Harmony C#5
        "-f", "lavfi", "-i", "sine=frequency=659.25:duration=60", # Harmony E5
        "-f", "lavfi", "-i", "sine=frequency=110:duration=60", # Bass A2
        "-f", "lavfi", "-i", "anoisesrc=d=60:c=pink:r=48000:a=0.3", # Rhythm texture
        "-filter_complex",
        # Layer 1: Bansuri Flute Harmonic Lead with Vibrato & Reverb
        "[0:a][1:a][2:a]amix=inputs=3:normalize=0,vibrato=f=5.5:d=0.35,flanger=delay=8:depth=3,equalizer=f=880:t=q:w=1.0:g=4[lead];"
        # Layer 2: Rhythmic Dhol Bass Pulse at 92 BPM (tremolo 3.07Hz = ~184 quarter pulses)
        "[3:a]tremolo=f=3.07:d=0.9,equalizer=f=75:t=q:w=1.0:g=8,volume=1.8[bass_dhol];"
        # Layer 3: Acoustic Rhythm Strum Percussion
        "[4:a]bandpass=f=2400:w=1200,tremolo=f=6.14:d=0.85,volume=0.9[shaker];"
        # Master Mix & Loudness Boost
        "[lead][bass_dhol][shaker]amix=inputs=3:normalize=0,loudnorm=I=-14:TP=-1.0:LRA=10[master]",
        "-map", "[master]",
        "-t", "60",
        "-c:a", "libmp3lame",
        "-b:a", "320k",
        out_path
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    print(f"✅ Generated Rich Sahyadri Folk Fusion Soundtrack at: {out_path}")

if __name__ == "__main__":
    generate_rich_sahyadri_music()
