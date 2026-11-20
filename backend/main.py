import os
import shutil
import uuid
import asyncio
import json
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.analyzer import probe_video, generate_thumbnail, probe_audio
from backend.story_engine import StoryEngine
from backend.renderer import VlogRenderer
from backend.audio_manager import get_available_music, ensure_default_music_tracks
from backend.voice_engine import VoiceEngine
from backend.instagram_poster import instagram_poster
from backend.transliterate import transliterate_text
from backend.youtube_uploader import youtube_uploader
from backend.cleanup import cleanup_unnecessary_data, scan_unnecessary_data, get_storage_breakdown

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
THUMBNAIL_DIR = os.path.join(UPLOAD_DIR, "thumbnails")
VOICEOVER_DIR = os.path.join(UPLOAD_DIR, "voiceovers")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
MUSIC_DIR = os.path.join(BASE_DIR, "assets", "music")

DATA_DIR = os.path.join(BASE_DIR, "data")
STATE_FILE = os.path.join(DATA_DIR, "project_state.json")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(THUMBNAIL_DIR, exist_ok=True)
os.makedirs(VOICEOVER_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(FRONTEND_DIR, exist_ok=True)
os.makedirs(MUSIC_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

app = FastAPI(title="AutoVlog Studio - Local AI Daily Vlog Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

project_state = {
    "clips": [],
    "voiceover": None,
    "current_plan": None,
    "render_job": {
        "status": "idle",
        "progress": 0,
        "message": "",
        "output_file": None,
        "output_url": None,
        "error": None
    }
}

def save_state_to_disk():
    """Safeguard all user-feeded data, timeline, scripts and clips to disk."""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "clips": project_state["clips"],
                "voiceover": project_state.get("voiceover"),
                "current_plan": project_state.get("current_plan")
            }, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Warning: Could not save state to disk: {e}")

def load_state_from_disk():
    """Recover all user clips, timeline and voiceover data on startup."""
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                if saved.get("clips"):
                    valid_clips = [c for c in saved["clips"] if os.path.exists(c.get("file_path", ""))]
                    project_state["clips"] = valid_clips
                if saved.get("voiceover"):
                    project_state["voiceover"] = saved["voiceover"]
                if saved.get("current_plan"):
                    project_state["current_plan"] = saved["current_plan"]
        
        # If clips are still empty, auto-discover existing uploaded files
        if not project_state["clips"] and os.path.exists(UPLOAD_DIR):
            discovered = []
            valid_exts = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".jpg", ".jpeg", ".png"}
            for fn in sorted(os.listdir(UPLOAD_DIR)):
                fp = os.path.join(UPLOAD_DIR, fn)
                if os.path.isfile(fp) and Path(fn).suffix.lower() in valid_exts:
                    clip_id = fn.split("_")[0] if "_" in fn else str(uuid.uuid4())[:8]
                    orig_name = "_".join(fn.split("_")[1:]) if "_" in fn else fn
                    thumb_name = f"thumb_{clip_id}.jpg"
                    thumb_path = os.path.join(THUMBNAIL_DIR, thumb_name)
                    if not os.path.exists(thumb_path):
                        generate_thumbnail(fp, thumb_path, timestamp=1.0)
                    meta = probe_video(fp)
                    discovered.append({
                        "id": clip_id,
                        "filename": orig_name,
                        "saved_filename": fn,
                        "file_path": fp,
                        "video_url": f"/uploads/{fn}",
                        "thumbnail_url": f"/thumbnails/{thumb_name}",
                        "rotation": meta.get("rotation", 0),
                        **meta
                    })
            if discovered:
                project_state["clips"] = discovered
                save_state_to_disk()
    except Exception as e:
        print(f"Warning: Error loading saved state: {e}")

@app.get("/outputs/{filename}")
async def stream_output_video(filename: str, request: Request):
    """High-performance HTTP 206 Partial Content range streaming for instant video playback."""
    file_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Video file not found")

    file_size = os.path.getsize(file_path)
    range_header = request.headers.get("range")

    if not range_header:
        return FileResponse(
            file_path,
            media_type="video/mp4",
            headers={"Accept-Ranges": "bytes"}
        )

    try:
        range_str = range_header.replace("bytes=", "").strip()
        parts = range_str.split("-")
        start = int(parts[0]) if parts[0] else 0
        end = int(parts[1]) if len(parts) > 1 and parts[1] else file_size - 1
    except Exception:
        start = 0
        end = file_size - 1

    start = max(0, start)
    end = min(file_size - 1, end)
    content_length = (end - start) + 1
    chunk_size = 1024 * 1024 * 2  # 2MB chunks

    def iter_file():
        with open(file_path, "rb") as f:
            f.seek(start)
            remaining = content_length
            while remaining > 0:
                chunk = f.read(min(chunk_size, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
                yield chunk

    headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(content_length),
        "Content-Type": "video/mp4",
        "Cache-Control": "public, max-age=3600"
    }
    return StreamingResponse(iter_file(), status_code=206, headers=headers)

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
app.mount("/thumbnails", StaticFiles(directory=THUMBNAIL_DIR), name="thumbnails")
app.mount("/voiceovers", StaticFiles(directory=VOICEOVER_DIR), name="voiceovers")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

renderer = VlogRenderer(output_dir=OUTPUT_DIR)

@app.on_event("startup")
async def startup_event():
    ensure_default_music_tracks()
    load_state_from_disk()

@app.get("/")
def serve_index():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "AutoVlog Studio Backend Running."}

@app.get("/api/status")
def get_status():
    return {
        "status": "online",
        "clips_count": len(project_state["clips"]),
        "current_voiceover": project_state.get("voiceover"),
        "music_tracks": get_available_music(),
        "presets": StoryEngine.PRESETS,
        "filters": VlogRenderer.FILTERS,
        "transitions": VlogRenderer.TRANSITIONS,
        "voice_effects": VoiceEngine.VOICE_EFFECTS,
        "voice_languages": VoiceEngine.LANGUAGES
    }

@app.get("/api/clips")
def list_clips():
    return project_state["clips"]

@app.post("/api/upload")
async def upload_videos(files: list[UploadFile] = File(...)):
    """Upload one or multiple raw video clips."""
    new_clips = []
    
    for file in files:
        clip_id = str(uuid.uuid4())[:8]
        file_ext = Path(file.filename).suffix or ".mp4"
        saved_filename = f"{clip_id}_{file.filename}"
        saved_path = os.path.join(UPLOAD_DIR, saved_filename)
        
        with open(saved_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        meta = probe_video(saved_path)
        
        thumb_name = f"thumb_{clip_id}.jpg"
        thumb_path = os.path.join(THUMBNAIL_DIR, thumb_name)
        generate_thumbnail(saved_path, thumb_path, timestamp=1.0)
        
        clip_data = {
            "id": clip_id,
            "filename": file.filename,
            "saved_filename": saved_filename,
            "file_path": saved_path,
            "video_url": f"/uploads/{saved_filename}",
            "thumbnail_url": f"/thumbnails/{thumb_name}",
            "rotation": meta.get("rotation", 0),
            **meta
        }
        
        project_state["clips"].append(clip_data)
        new_clips.append(clip_data)
        
    save_state_to_disk()
    return {"status": "success", "uploaded": len(new_clips), "clips": project_state["clips"]}

@app.post("/api/clips/{clip_id}/rotate")
def rotate_clip(clip_id: str):
    """Rotate a clip 90 degrees clockwise."""
    clip = next((c for c in project_state["clips"] if c["id"] == clip_id), None)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    
    current_rot = clip.get("rotation", 0)
    new_rot = (current_rot + 90) % 360
    clip["rotation"] = new_rot
    
    if new_rot in [90, 270]:
        clip["is_vertical"] = clip["width"] > clip["height"]
    else:
        clip["is_vertical"] = clip["height"] > clip["width"]

    save_state_to_disk()
    return {"status": "success", "clip_id": clip_id, "rotation": new_rot, "is_vertical": clip["is_vertical"]}

@app.delete("/api/clips/{clip_id}")
def delete_clip(clip_id: str):
    """Delete a clip from the project and timeline."""
    clip = next((c for c in project_state["clips"] if c["id"] == clip_id), None)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    
    project_state["clips"] = [c for c in project_state["clips"] if c["id"] != clip_id]
    
    # Remove clip video file
    try:
        if os.path.exists(clip["file_path"]):
            os.remove(clip["file_path"])
    except Exception:
        pass

    # Remove thumbnail
    thumb_path = os.path.join(THUMBNAIL_DIR, f"thumb_{clip_id}.jpg")
    if os.path.exists(thumb_path):
        try:
            os.remove(thumb_path)
        except Exception:
            pass

    # Remove any per-clip voiceover files
    if os.path.exists(VOICEOVER_DIR):
        for f in os.listdir(VOICEOVER_DIR):
            if clip_id in f:
                try:
                    os.remove(os.path.join(VOICEOVER_DIR, f))
                except Exception:
                    pass

    if project_state.get("current_plan") and project_state["current_plan"].get("timeline"):
        project_state["current_plan"]["timeline"] = [
            itm for itm in project_state["current_plan"]["timeline"] if itm.get("id") != clip_id
        ]
        for i, itm in enumerate(project_state["current_plan"]["timeline"]):
            itm["order"] = i
        total_secs = sum(itm.get("final_duration", 0) for itm in project_state["current_plan"]["timeline"])
        project_state["current_plan"]["estimated_total_duration"] = round(total_secs, 1)
        
    save_state_to_disk()
    return {"status": "success", "remaining": len(project_state["clips"]), "plan": project_state.get("current_plan")}

@app.post("/api/clips/{clip_id}/replace")
async def replace_single_clip(clip_id: str, file: UploadFile = File(...)):
    """Replace an existing clip's video file while preserving script, voice, order, and position."""
    clip = next((c for c in project_state["clips"] if c["id"] == clip_id), None)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    # Remove old file if exists
    old_fp = clip.get("file_path")
    if old_fp and os.path.exists(old_fp):
        try:
            os.remove(old_fp)
        except Exception:
            pass

    ext = Path(file.filename).suffix.lower()
    new_fn = f"{uuid.uuid4().hex[:8]}{ext}"
    new_fp = os.path.join(UPLOAD_DIR, new_fn)
    with open(new_fp, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    meta = probe_video(new_fp)
    thumb_name = f"thumb_{uuid.uuid4().hex[:8]}.jpg"
    thumb_path = os.path.join(THUMBNAIL_DIR, thumb_name)
    generate_thumbnail(new_fp, thumb_path, timestamp=1.0)

    clip["filename"] = file.filename
    clip["file_path"] = new_fp
    clip["thumbnail_url"] = f"/thumbnails/{thumb_name}"
    clip["duration"] = meta["duration"]
    clip["width"] = meta["width"]
    clip["height"] = meta["height"]
    clip["fps"] = meta["fps"]
    clip["rotation"] = meta["rotation"]
    clip["has_audio"] = meta["has_audio"]
    clip["is_vertical"] = meta["is_vertical"]

    # Re-calculate speed if voiceover exists
    vo_dur = clip.get("voiceover_duration", 0.0)
    raw_dur = float(meta["duration"])
    if vo_dur > 0.2:
        speed_mult = max(0.25, min(16.0, round(raw_dur / vo_dur, 2)))
    else:
        speed_mult = clip.get("speed_multiplier", 1.0)
    clip["speed_multiplier"] = speed_mult
    clip["final_duration"] = round(raw_dur / speed_mult, 2)
    clip["end_time"] = raw_dur

    # Update current_plan timeline item
    if project_state.get("current_plan") and project_state["current_plan"].get("timeline"):
        for itm in project_state["current_plan"]["timeline"]:
            if itm.get("id") == clip_id:
                itm["filename"] = file.filename
                itm["file_path"] = new_fp
                itm["thumbnail_url"] = f"/thumbnails/{thumb_name}"
                itm["duration"] = meta["duration"]
                itm["raw_duration"] = meta["duration"]
                itm["rotation"] = meta["rotation"]
                itm["is_vertical"] = meta["is_vertical"]
                itm["speed_multiplier"] = speed_mult
                itm["final_duration"] = clip["final_duration"]
                itm["start_time"] = 0.0
                itm["end_time"] = raw_dur

    save_state_to_disk()
    return {"status": "success", "clip": clip, "plan": project_state.get("current_plan")}

@app.post("/api/clips/clear")
def clear_all_clips():
    """Clear all uploaded clips and reset project timeline."""
    for clip in project_state["clips"]:
        try:
            if os.path.exists(clip.get("file_path", "")):
                os.remove(clip["file_path"])
        except Exception:
            pass
    project_state["clips"] = []
    project_state["current_plan"] = None
    save_state_to_disk()
    return {"status": "success", "remaining": 0}

@app.post("/api/clips/reorder")
def reorder_clips(data: dict):
    """
    Persist custom clip reordering across project state and story timeline.
    """
    clip_ids = data.get("clip_ids", [])
    if clip_ids:
        clip_map = {c["id"]: c for c in project_state["clips"]}
        reordered = [clip_map[cid] for cid in clip_ids if cid in clip_map]
        for c in project_state["clips"]:
            if c not in reordered:
                reordered.append(c)
        project_state["clips"] = reordered

    if "timeline" in data and data["timeline"]:
        if not project_state.get("current_plan"):
            project_state["current_plan"] = {}
        project_state["current_plan"]["timeline"] = data["timeline"]
        total_secs = sum(item.get("final_duration", 0) for item in data["timeline"])
        project_state["current_plan"]["estimated_total_duration"] = round(total_secs, 1)

    save_state_to_disk()
    return {"status": "success", "clips": project_state["clips"], "plan": project_state.get("current_plan")}

@app.post("/api/clips/{clip_id}/voiceover")
async def generate_clip_voiceover(clip_id: str, data: dict):
    """
    Generate independent TTS voiceover for an individual clip and auto-scale that clip's speed to match the audio duration.
    """
    clip = next((c for c in project_state["clips"] if c["id"] == clip_id), None)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    text = data.get("text", "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Voiceover text for clip is required.")

    lang = data.get("lang", "mr")
    voice_effect = data.get("voice_effect", "gian_classic")

    saved_filename = f"clip_{clip_id}_{uuid.uuid4().hex[:6]}.mp3"
    saved_path = os.path.join(VOICEOVER_DIR, saved_filename)

    try:
        await VoiceEngine.generate_story_voice(
            text=text,
            lang=lang,
            voice_effect=voice_effect,
            output_path=saved_path
        )

        audio_meta = probe_audio(saved_path)
        audio_dur = audio_meta.get("duration", 0.0)
        raw_duration = float(clip.get("duration", 5.0))
        
        # Calculate auto-scaled video speed
        if audio_dur > 0.2:
            speed_mult = max(0.25, min(16.0, round(raw_duration / audio_dur, 2)))
        else:
            speed_mult = 1.0
        final_dur = round(raw_duration / speed_mult, 2)

        # Update clip properties
        clip["voiceover_file"] = saved_path
        clip["voiceover_url"] = f"/voiceovers/{saved_filename}?t={uuid.uuid4().hex[:6]}"
        clip["voiceover_text"] = text
        clip["voiceover_lang"] = lang
        clip["voiceover_effect"] = voice_effect
        clip["voiceover_duration"] = audio_dur
        clip["speed_multiplier"] = speed_mult
        clip["final_duration"] = final_dur

        # If current plan exists, update the timeline item as well
        if project_state.get("current_plan") and project_state["current_plan"].get("timeline"):
            for item in project_state["current_plan"]["timeline"]:
                if item.get("id") == clip_id:
                    item["voiceover_file"] = saved_path
                    item["voiceover_url"] = clip["voiceover_url"]
                    item["voiceover_text"] = text
                    item["voiceover_lang"] = lang
                    item["voiceover_effect"] = voice_effect
                    item["voiceover_duration"] = audio_dur
                    item["speed_multiplier"] = speed_mult
                    item["final_duration"] = final_dur
                    break

            total_secs = sum(item.get("final_duration", 0) for item in project_state["current_plan"]["timeline"])
            project_state["current_plan"]["estimated_total_duration"] = round(total_secs, 1)

        save_state_to_disk()
        return {
            "status": "success",
            "clip": clip,
            "plan": project_state.get("current_plan")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/clips/{clip_id}/voiceover")
def delete_clip_voiceover(clip_id: str):
    """
    Remove voiceover audio from a specific clip and reset its speed.
    """
    clip = next((c for c in project_state["clips"] if c["id"] == clip_id), None)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    old_file = clip.get("voiceover_file")
    if old_file and os.path.exists(old_file):
        try:
            os.remove(old_file)
        except Exception:
            pass

    clip["voiceover_file"] = None
    clip["voiceover_url"] = None
    clip["voiceover_text"] = ""
    clip["voiceover_duration"] = 0.0

    if project_state.get("current_plan") and project_state["current_plan"].get("timeline"):
        for item in project_state["current_plan"]["timeline"]:
            if item.get("id") == clip_id:
                item["voiceover_file"] = None
                item["voiceover_url"] = None
                item["voiceover_text"] = ""
                item["voiceover_duration"] = 0.0
                break

        total_secs = sum(item.get("final_duration", 0) for item in project_state["current_plan"]["timeline"])
        project_state["current_plan"]["estimated_total_duration"] = round(total_secs, 1)

    save_state_to_disk()
    return {"status": "success", "clip": clip, "plan": project_state.get("current_plan")}

@app.post("/api/plan")
def generate_story_plan(data: dict):
    """
    Generate or regenerate the story arc plan based on uploaded clips, preset, and audio mode.
    If a voiceover track is active, automatically scales video clip speeds to match the exact audio duration!
    """
    preset_key = data.get("preset", "fast_reel")
    audio_mode = data.get("audio_mode", "mute_all")
    aspect_ratio = data.get("aspect_ratio", "9:16")
    sync_voice = bool(data.get("sync_with_voiceover", True))

    target_audio_dur = None
    if sync_voice and project_state.get("voiceover") and os.path.exists(project_state["voiceover"].get("file_path", "")):
        audio_info = probe_audio(project_state["voiceover"]["file_path"])
        if audio_info.get("duration", 0) > 2.0:
            target_audio_dur = audio_info["duration"]
            project_state["voiceover"]["duration"] = target_audio_dur

    plan = StoryEngine.generate_story_plan(
        project_state["clips"],
        preset_key=preset_key,
        audio_mode=audio_mode,
        aspect_ratio=aspect_ratio,
        target_voice_duration=target_audio_dur
    )
    project_state["current_plan"] = plan
    save_state_to_disk()
    return plan

@app.post("/api/preview")
async def generate_quick_preview(data: dict):
    """
    Generate a rapid 3-second live preview demonstrating the selected beauty glow filter and transition.
    """
    if not project_state["clips"]:
        raise HTTPException(status_code=400, detail="Please upload at least one video clip to preview.")

    aspect_ratio = data.get("aspect_ratio", "9:16")
    visual_filter = data.get("visual_filter", "beauty_glow")
    transition_type = data.get("transition_type", "fade")
    show_text = bool(data.get("show_text_overlays", False))

    loop = asyncio.get_event_loop()
    try:
        preview_url = await loop.run_in_executor(
            None,
            lambda: renderer.render_quick_preview(
                clips=project_state["clips"],
                aspect_ratio=aspect_ratio,
                visual_filter=visual_filter,
                transition_type=transition_type,
                show_text_overlays=show_text
            )
        )
        return {"status": "success", "preview_url": preview_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/voiceover/upload")
async def upload_voiceover(file: UploadFile = File(...)):
    """Upload recorded mic audio or custom voiceover audio file and auto-sync video speed."""
    ext = Path(file.filename).suffix or ".webm"
    if not ext or ext.lower() not in [".mp3", ".wav", ".m4a", ".aac", ".ogg", ".webm"]:
        ext = ".webm"
    
    saved_filename = f"voice_{uuid.uuid4().hex[:8]}{ext}"
    saved_path = os.path.join(VOICEOVER_DIR, saved_filename)

    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    audio_meta = probe_audio(saved_path)
    audio_dur = audio_meta.get("duration", 0.0)

    project_state["voiceover"] = {
        "filename": file.filename,
        "saved_filename": saved_filename,
        "file_path": saved_path,
        "audio_url": f"/voiceovers/{saved_filename}",
        "duration": audio_dur
    }

    # Auto-calibrate video timeline speeds to match voiceover duration!
    plan = None
    if project_state["clips"]:
        plan = StoryEngine.generate_story_plan(
            project_state["clips"],
            target_voice_duration=audio_dur if audio_dur > 2.0 else None
        )
        project_state["current_plan"] = plan

    return {"status": "success", "voiceover": project_state["voiceover"], "plan": plan}

@app.post("/api/voiceover/generate-tts")
async def generate_voiceover_tts(data: dict):
    """
    Convert written story text in Marathi, Hindi, or English to audio and auto-match video clip speeds.
    """
    text = data.get("text", "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Story text is required.")

    lang = data.get("lang", "mr")
    voice_effect = data.get("voice_effect", "gian_classic")

    saved_filename = f"tts_{uuid.uuid4().hex[:8]}.mp3"
    saved_path = os.path.join(VOICEOVER_DIR, saved_filename)

    try:
        await VoiceEngine.generate_story_voice(
            text=text,
            lang=lang,
            voice_effect=voice_effect,
            output_path=saved_path
        )

        audio_meta = probe_audio(saved_path)
        audio_dur = audio_meta.get("duration", 0.0)
        char_name = VoiceEngine.VOICE_EFFECTS.get(voice_effect, {}).get("name", "Heavy Cartoon Voice")

        project_state["voiceover"] = {
            "filename": f"{char_name}.mp3",
            "saved_filename": saved_filename,
            "file_path": saved_path,
            "audio_url": f"/voiceovers/{saved_filename}",
            "text": text,
            "lang": lang,
            "voice_effect": voice_effect,
            "duration": audio_dur
        }

        # Auto-calibrate video timeline speeds to match voiceover duration!
        plan = None
        if project_state["clips"]:
            plan = StoryEngine.generate_story_plan(
                project_state["clips"],
                target_voice_duration=audio_dur if audio_dur > 2.0 else None
            )
            project_state["current_plan"] = plan

        return {"status": "success", "voiceover": project_state["voiceover"], "plan": plan}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/voiceover/apply-effect")
async def apply_effect_to_voiceover(data: dict):
    """
    Apply a cartoon voice character filter or regenerate voice for the selected cartoon.
    """
    if not project_state.get("voiceover") or not os.path.exists(project_state["voiceover"]["file_path"]):
        raise HTTPException(status_code=400, detail="No voiceover track available to apply effects to.")

    voice_effect = data.get("voice_effect", "gian_classic")
    current_vo = project_state["voiceover"]

    # If this voiceover was generated from story text, re-generate freshly using the cartoon's dedicated base model!
    if current_vo.get("text"):
        try:
            saved_filename = f"tts_{uuid.uuid4().hex[:8]}.mp3"
            saved_path = os.path.join(VOICEOVER_DIR, saved_filename)
            await VoiceEngine.generate_story_voice(
                text=current_vo["text"],
                lang=current_vo.get("lang", "mr"),
                voice_effect=voice_effect,
                output_path=saved_path
            )
            audio_meta = probe_audio(saved_path)
            audio_dur = audio_meta.get("duration", 0.0)
            char_name = VoiceEngine.VOICE_EFFECTS.get(voice_effect, {}).get("name", "Cartoon Voice")

            project_state["voiceover"] = {
                "filename": f"{char_name}.mp3",
                "saved_filename": saved_filename,
                "file_path": saved_path,
                "audio_url": f"/voiceovers/{saved_filename}",
                "text": current_vo["text"],
                "lang": current_vo.get("lang", "mr"),
                "voice_effect": voice_effect,
                "duration": audio_dur
            }

            plan = None
            if project_state["clips"]:
                plan = StoryEngine.generate_story_plan(
                    project_state["clips"],
                    target_voice_duration=audio_dur if audio_dur > 2.0 else None
                )
                project_state["current_plan"] = plan

            return {"status": "success", "voiceover": project_state["voiceover"], "plan": plan}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        # User uploaded / mic recorded file -> apply acoustic cartoon filter
        current_path = current_vo["file_path"]
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(
                None,
                lambda: VoiceEngine.apply_funny_effect_to_file(
                    input_audio_path=current_path,
                    voice_effect=voice_effect
                )
            )
            audio_meta = probe_audio(current_path)
            audio_dur = audio_meta.get("duration", 0.0)
            project_state["voiceover"]["duration"] = audio_dur
            project_state["voiceover"]["voice_effect"] = voice_effect
            project_state["voiceover"]["audio_url"] = f"/voiceovers/{project_state['voiceover']['saved_filename']}?t={uuid.uuid4().hex[:6]}"
            return {"status": "success", "voiceover": project_state["voiceover"]}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/voiceover")
def delete_voiceover():
    """Remove current voiceover track."""
    vo = project_state.get("voiceover")
    if vo and os.path.exists(vo.get("file_path", "")):
        try:
            os.remove(vo["file_path"])
        except Exception:
            pass
    project_state["voiceover"] = None
    return {"status": "success"}

@app.post("/api/render")
async def start_render(data: dict):
    """
    Trigger the Studio Render process.
    """
    if project_state["render_job"]["status"] == "rendering":
        raise HTTPException(status_code=400, detail="A render job is already in progress.")

    timeline = data.get("timeline")
    if not timeline:
        if not project_state["current_plan"]:
            raise HTTPException(status_code=400, detail="No timeline plan available.")
        timeline = project_state["current_plan"]["timeline"]

    aspect_ratio = data.get("aspect_ratio", "9:16")
    resolution = data.get("resolution", "4k")
    music_id = data.get("music_id", "lofi_chill")
    music_volume = float(data.get("music_volume", 0.25))
    voiceover_volume = float(data.get("voiceover_volume", 1.0))
    visual_filter = data.get("visual_filter", "beauty_glow")
    transition_type = data.get("transition_type", "fade")
    transition_duration = float(data.get("transition_duration", 0.5))
    show_text_overlays = bool(data.get("show_text_overlays", False))
    auto_rotate_v2h = bool(data.get("auto_rotate_v2h", False))

    music_path = os.path.join(MUSIC_DIR, f"{music_id}.mp3")
    if not os.path.exists(music_path):
        music_path = None

    voiceover_path = None
    if project_state.get("voiceover") and os.path.exists(project_state["voiceover"]["file_path"]):
        voiceover_path = project_state["voiceover"]["file_path"]

    output_filename = f"daily_vlog_{uuid.uuid4().hex[:6]}.mp4"

    project_state["render_job"] = {
        "status": "rendering",
        "progress": 0,
        "message": f"Starting 4K Studio Render pipeline...",
        "output_file": None,
        "output_url": None,
        "error": None
    }

    asyncio.create_task(
        run_render_task(
            timeline=timeline,
            output_filename=output_filename,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            music_path=music_path,
            music_volume=music_volume,
            voiceover_path=voiceover_path,
            voiceover_volume=voiceover_volume,
            visual_filter=visual_filter,
            transition_type=transition_type,
            transition_duration=transition_duration,
            show_text_overlays=show_text_overlays,
            auto_rotate_v2h=auto_rotate_v2h
        )
    )

    return {"status": "started", "output_filename": output_filename}

async def run_render_task(
    timeline,
    output_filename,
    aspect_ratio,
    resolution,
    music_path,
    music_volume,
    voiceover_path,
    voiceover_volume,
    visual_filter,
    transition_type,
    transition_duration,
    show_text_overlays,
    auto_rotate_v2h
):
    def progress_cb(pct: int, msg: str):
        project_state["render_job"]["progress"] = pct
        project_state["render_job"]["message"] = msg

    try:
        loop = asyncio.get_event_loop()
        output_path = await loop.run_in_executor(
            None,
            lambda: renderer.render_vlog(
                timeline=timeline,
                output_filename=output_filename,
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                music_file=music_path,
                music_volume=music_volume,
                voiceover_file=voiceover_path,
                voiceover_volume=voiceover_volume,
                visual_filter=visual_filter,
                transition_type=transition_type,
                transition_duration=transition_duration,
                show_text_overlays=show_text_overlays,
                auto_rotate_vertical_to_horizontal=auto_rotate_v2h,
                progress_callback=progress_cb
            )
        )
        # Automatically clean up unnecessary temporary data, orphaned voice tests & render artifacts
        cleanup_res = cleanup_unnecessary_data(project_state=project_state, base_dir=BASE_DIR)
        freed_mb = cleanup_res.get("freed_mb", 0)
        freed_count = cleanup_res.get("files_removed", 0)
        cleanup_msg = f" 🧹 Auto-cleaned {freed_count} temp files ({freed_mb} MB freed)." if freed_count > 0 else ""

        project_state["render_job"]["status"] = "completed"
        project_state["render_job"]["progress"] = 100
        project_state["render_job"]["message"] = f"Render complete! Daily vlog is ready.{cleanup_msg}"
        project_state["render_job"]["output_file"] = output_filename
        project_state["render_job"]["output_url"] = f"/outputs/{output_filename}"
        project_state["render_job"]["cleanup_summary"] = cleanup_res

    except Exception as e:
        import traceback
        traceback.print_exc()
        project_state["render_job"]["status"] = "error"
        project_state["render_job"]["error"] = str(e)
        project_state["render_job"]["message"] = f"Render failed: {str(e)}"

@app.get("/api/render/status")
def get_render_status():
    return project_state["render_job"]

@app.get("/api/render/stream")
async def render_progress_stream():
    """SSE Stream for real-time progress updates in the UI."""
    async def event_generator():
        while True:
            job = project_state["render_job"]
            yield f"data: {json.dumps(job)}\n\n"
            if job["status"] in ["completed", "error"]:
                break
            await asyncio.sleep(0.4)
    return StreamingResponse(event_generator(), media_type="text/event-stream")

# --- Instagram Auto-Poster Endpoints ---

@app.get("/api/instagram/status")
def get_instagram_status():
    """Check Instagram connection status."""
    return instagram_poster.get_status()

@app.post("/api/instagram/login")
async def login_instagram(data: dict):
    """Log in to Instagram via username/password or direct session ID."""
    raw_user = data.get("username")
    username = raw_user.strip() if isinstance(raw_user, str) else ""
    password = data.get("password") or ""
    code = data.get("verification_code") or None
    raw_session = data.get("sessionid")
    sessionid = raw_session.strip() if isinstance(raw_session, str) else ""

    if not sessionid and (not username or not password):
        raise HTTPException(status_code=400, detail="Please provide your username & password or Instagram Session ID.")

    loop = asyncio.get_event_loop()
    try:
        res = await loop.run_in_executor(
            None,
            lambda: instagram_poster.login(
                username=username or None,
                password=password or None,
                verification_code=code,
                sessionid=sessionid or None
            )
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/instagram/logout")
def logout_instagram():
    """Log out and remove saved session."""
    return instagram_poster.logout()

@app.post("/api/instagram/post-reel")
async def post_reel_to_instagram(data: dict):
    """Post the rendered vlog video directly as an Instagram Reel."""
    if not instagram_poster.logged_in:
        raise HTTPException(status_code=401, detail="Instagram account is not connected. Please connect your account first.")

    filename = data.get("filename")
    if not filename:
        if project_state["render_job"].get("output_file"):
            filename = project_state["render_job"]["output_file"]
        elif os.path.exists(OUTPUT_DIR):
            rendered_files = [
                f for f in os.listdir(OUTPUT_DIR)
                if f.lower().endswith(".mp4") and not f.startswith("preview_")
            ]
            if rendered_files:
                rendered_files.sort(
                    key=lambda f: os.path.getmtime(os.path.join(OUTPUT_DIR, f)),
                    reverse=True
                )
                filename = rendered_files[0]

    if not filename:
        raise HTTPException(status_code=400, detail="No rendered video file available to post. Please render your vlog first.")

    video_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail=f"Video file not found: {filename}")

    caption = data.get("caption", "").strip()

    loop = asyncio.get_event_loop()
    try:
        res = await loop.run_in_executor(
            None,
            lambda: instagram_poster.post_reel(video_path=video_path, caption=caption)
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Speech-to-Text & Transliteration Endpoints ---

@app.post("/api/transliterate")
def api_transliterate(payload: dict):
    """
    Transliterate Roman/English Marathi/Hindi text into Devanagari script.
    e.g. "Aaj mi office la lavakar gelo" -> "आज मी ऑफिसला लवकर गेलो"
    """
    text = payload.get("text", "")
    lang = payload.get("lang", "mr")
    transliterated = transliterate_text(text, target_lang=lang)
    return {
        "status": "success",
        "original": text,
        "transliterated": transliterated,
        "lang": lang
    }

# --- YouTube Studio 1-Click Upload & Metadata Endpoints ---

@app.get("/api/youtube/status")
def get_youtube_status():
    """Get YouTube channel connection status."""
    return youtube_uploader.get_status()

@app.post("/api/youtube/connect")
def connect_youtube(payload: dict):
    """Save YouTube channel connection session."""
    channel_name = payload.get("channel_name", "My YouTube Channel")
    api_key = payload.get("api_key")
    return youtube_uploader.connect_channel(channel_name=channel_name, api_key=api_key)

@app.post("/api/youtube/logout")
def logout_youtube():
    """Disconnect YouTube channel."""
    success = youtube_uploader.disconnect_channel()
    return {"status": "success", "disconnected": success}

@app.post("/api/youtube/generate-metadata")
def generate_youtube_metadata(payload: dict):
    """Auto-generate optimized SEO title, description, hashtags & timeline chapters for YouTube."""
    story = payload.get("story_text", "")
    is_8k = payload.get("is_8k", False)
    is_4k = payload.get("is_4k", True)
    timeline = project_state.get("current_plan", {}).get("timeline", []) if project_state.get("current_plan") else []
    return youtube_uploader.generate_smart_metadata(
        story_text=story,
        timeline=timeline,
        is_8k=is_8k,
        is_4k=is_4k
    )

@app.post("/api/youtube/post-video")
def post_video_to_youtube(payload: dict):
    """Publish rendered vlog directly to YouTube."""
    filename = payload.get("filename")
    title = payload.get("title", "Daily Work Vlog").strip()
    desc = payload.get("description", "").strip()
    tags_str = payload.get("tags", "")
    privacy = payload.get("privacy", "public").lower()

    if isinstance(tags_str, str):
        tags = [t.strip() for t in tags_str.split(",") if t.strip()]
    else:
        tags = tags_str or []

    # Auto-fallback to newest rendered file if none provided
    if not filename:
        output_files = [f for f in os.listdir(OUTPUT_DIR) if f.lower().endswith(".mp4") and not f.startswith("preview_")]
        if not output_files:
            raise HTTPException(status_code=400, detail="No rendered video file available to post. Please render your vlog first.")
        output_files.sort(key=lambda f: os.path.getmtime(os.path.join(OUTPUT_DIR, f)), reverse=True)
        filename = output_files[0]

    video_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail=f"Output video '{filename}' not found.")

    try:
        res = youtube_uploader.upload_video(
            video_path=video_path,
            title=title,
            description=desc,
            tags=tags,
            privacy_status=privacy
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Output Videos Gallery Endpoints ---

@app.get("/api/outputs")
def list_output_videos():
    """List all previously rendered vlog output videos with metadata."""
    if not os.path.exists(OUTPUT_DIR):
        return []

    files = []
    for f in os.listdir(OUTPUT_DIR):
        if f.lower().endswith(".mp4") and not f.startswith("preview_"):
            full_p = os.path.join(OUTPUT_DIR, f)
            try:
                stat = os.stat(full_p)
                size_mb = round(stat.st_size / (1024 * 1024), 2)
                mtime = stat.st_mtime
                created_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")

                # Probe video quickly
                try:
                    meta = probe_video(full_p)
                    width = meta.get("width", 0)
                    height = meta.get("height", 0)
                    dur = round(meta.get("duration", 0.0), 1)
                except Exception:
                    width = 0
                    height = 0
                    dur = 0.0

                is_8k = (width >= 4000 or height >= 4000)
                is_4k = not is_8k and (width >= 2160 or height >= 2160)
                
                if is_8k:
                    res_tag = f"8K Ultra Cinematic ({width}x{height})" if width and height else "8K Ultra Cinematic"
                elif is_4k:
                    res_tag = f"4K Ultra HD ({width}x{height})" if width and height else "4K Ultra HD"
                elif width and height:
                    res_tag = f"Full HD ({width}x{height})"
                else:
                    res_tag = "HD Video"

                files.append({
                    "filename": f,
                    "url": f"/outputs/{f}",
                    "size_mb": size_mb,
                    "duration": dur,
                    "width": width,
                    "height": height,
                    "is_8k": is_8k,
                    "is_4k": is_4k,
                    "resolution_label": res_tag,
                    "created_at": created_str,
                    "mtime": mtime
                })
            except Exception as e:
                print(f"Error reading output video {f}: {e}")

    # Sort newest first
    files.sort(key=lambda x: x["mtime"], reverse=True)
    return files

@app.delete("/api/outputs/{filename}")
def delete_output_video(filename: str):
    """Delete a rendered vlog video from the output gallery."""
    safe_fn = os.path.basename(filename)
    target_path = os.path.join(OUTPUT_DIR, safe_fn)
    if os.path.exists(target_path):
        try:
            os.remove(target_path)
            return {"status": "success", "message": f"Deleted {safe_fn}"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    raise HTTPException(status_code=404, detail="File not found")

# --- Storage & Data Cleanup Endpoints ---

@app.get("/api/cleanup/stats")
def get_cleanup_storage_stats():
    """Get complete storage breakdown and scan for cleanable temporary files."""
    return get_storage_breakdown(project_state=project_state, base_dir=BASE_DIR)

@app.post("/api/cleanup")
def perform_manual_cleanup(payload: dict = None):
    """
    Manually purge temporary video rendering caches, stale quick previews,
    unreferenced voiceovers and thumbnails.
    """
    clean_clips = bool(payload.get("remove_orphaned_clips", False)) if payload else False
    res = cleanup_unnecessary_data(project_state=project_state, base_dir=BASE_DIR, remove_orphaned_clips=clean_clips)
    return res


