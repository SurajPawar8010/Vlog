import os
import shutil
import tempfile
import glob
import time
from typing import Optional, Dict, Any, List
from pathlib import Path


def get_active_file_paths(project_state: Dict[str, Any]) -> set[str]:
    """
    Collect all absolute file paths currently actively in use by the project
    to ensure they are NEVER deleted during cleanup.
    """
    active_paths = set()

    # Active uploaded clips
    clips = project_state.get("clips", [])
    for clip in clips:
        fp = clip.get("file_path")
        if fp:
            active_paths.add(os.path.abspath(fp).lower())
        thumb = clip.get("thumbnail_url", "")
        if thumb and thumb.startswith("/thumbnails/"):
            thumb_name = thumb.replace("/thumbnails/", "")
            active_paths.add(thumb_name.lower())

    # Active main voiceover
    vo = project_state.get("voiceover")
    if vo and isinstance(vo, dict) and vo.get("file_path"):
        active_paths.add(os.path.abspath(vo["file_path"]).lower())

    # Active timeline clips and per-clip voiceovers
    plan = project_state.get("current_plan")
    if plan and isinstance(plan, dict):
        timeline = plan.get("timeline", [])
        for item in timeline:
            clip_fp = item.get("file_path")
            if clip_fp:
                active_paths.add(os.path.abspath(clip_fp).lower())
            per_clip_vo = item.get("voiceover_file")
            if per_clip_vo:
                active_paths.add(os.path.abspath(per_clip_vo).lower())

    return active_paths


def scan_unnecessary_data(project_state: Dict[str, Any], base_dir: str) -> Dict[str, Any]:
    """
    Scan for unnecessary, orphaned, and temporary files and compute potential savings.
    """
    active_paths = get_active_file_paths(project_state)
    temp_system_dir = tempfile.gettempdir()
    upload_dir = os.path.join(base_dir, "uploads")
    thumbnail_dir = os.path.join(upload_dir, "thumbnails")
    voiceover_dir = os.path.join(upload_dir, "voiceovers")
    output_dir = os.path.join(base_dir, "output")

    cleanable_items: List[Dict[str, Any]] = []
    total_cleanable_bytes = 0

    # 1. Check System Temp Directories (autovlog_render_*, autovlog_preview_*, autovlog_trim_*)
    try:
        for entry in os.scandir(temp_system_dir):
            if entry.name.startswith(("autovlog_render_", "autovlog_preview_", "autovlog_trim_", "autovlog_")):
                size = 0
                try:
                    if entry.is_dir():
                        for root, _, files in os.walk(entry.path):
                            for f in files:
                                size += os.path.getsize(os.path.join(root, f))
                    else:
                        size = entry.stat().st_size
                except Exception:
                    size = 0

                cleanable_items.append({
                    "category": "temp_directory",
                    "path": entry.path,
                    "name": entry.name,
                    "size_bytes": size,
                    "is_dir": entry.is_dir()
                })
                total_cleanable_bytes += size
    except Exception as e:
        print(f"[CleanupScan] Error scanning system temp: {e}")

    # 2. Check Stale Preview Videos in output/ (preview_*.mp4)
    if os.path.exists(output_dir):
        for f in os.listdir(output_dir):
            if f.lower().startswith("preview_") and f.lower().endswith(".mp4"):
                fp = os.path.join(output_dir, f)
                try:
                    sz = os.path.getsize(fp)
                    cleanable_items.append({
                        "category": "preview_video",
                        "path": fp,
                        "name": f,
                        "size_bytes": sz,
                        "is_dir": False
                    })
                    total_cleanable_bytes += sz
                except Exception:
                    pass

    # 3. Check Orphaned Voiceovers in uploads/voiceovers/
    if os.path.exists(voiceover_dir):
        for f in os.listdir(voiceover_dir):
            if f.lower().endswith((".mp3", ".wav", ".webm", ".aac", ".m4a", ".ogg")):
                fp = os.path.join(voiceover_dir, f)
                abs_fp = os.path.abspath(fp).lower()
                if abs_fp not in active_paths:
                    try:
                        sz = os.path.getsize(fp)
                        cleanable_items.append({
                            "category": "orphaned_voiceover",
                            "path": fp,
                            "name": f,
                            "size_bytes": sz,
                            "is_dir": False
                        })
                        total_cleanable_bytes += sz
                    except Exception:
                        pass

    # 4. Check Orphaned Thumbnails in uploads/thumbnails/
    if os.path.exists(thumbnail_dir):
        for f in os.listdir(thumbnail_dir):
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                fp = os.path.join(thumbnail_dir, f)
                # Check if thumbnail matches any active clip thumbnail or clip ID
                is_active = False
                f_lower = f.lower()
                if f_lower in active_paths:
                    is_active = True
                else:
                    for clip in project_state.get("clips", []):
                        clip_id = clip.get("id", "").lower()
                        if clip_id and clip_id in f_lower:
                            is_active = True
                            break

                if not is_active:
                    try:
                        sz = os.path.getsize(fp)
                        cleanable_items.append({
                            "category": "orphaned_thumbnail",
                            "path": fp,
                            "name": f,
                            "size_bytes": sz,
                            "is_dir": False
                        })
                        total_cleanable_bytes += sz
                    except Exception:
                        pass

    # Group counts
    by_category = {}
    for item in cleanable_items:
        cat = item["category"]
        by_category[cat] = by_category.get(cat, 0) + 1

    return {
        "total_cleanable_files": len(cleanable_items),
        "total_cleanable_bytes": total_cleanable_bytes,
        "total_cleanable_mb": round(total_cleanable_bytes / (1024 * 1024), 2),
        "categories": by_category,
        "items": cleanable_items
    }


def cleanup_unnecessary_data(
    project_state: Dict[str, Any],
    base_dir: str,
    remove_orphaned_clips: bool = False
) -> Dict[str, Any]:
    """
    Automatically & safely remove all temporary directories, preview videos,
    orphaned voiceover tests, and unreferenced thumbnails.
    """
    scan_result = scan_unnecessary_data(project_state, base_dir)
    items_to_clean = scan_result["items"]

    active_paths = get_active_file_paths(project_state)
    upload_dir = os.path.join(base_dir, "uploads")

    # Optional: clean orphaned uploaded raw clips if requested
    if remove_orphaned_clips and os.path.exists(upload_dir):
        for f in os.listdir(upload_dir):
            fp = os.path.join(upload_dir, f)
            if os.path.isfile(fp) and f.lower().endswith((".mp4", ".mov", ".avi", ".mkv", ".webm")):
                if os.path.abspath(fp).lower() not in active_paths:
                    try:
                        sz = os.path.getsize(fp)
                        items_to_clean.append({
                            "category": "orphaned_upload",
                            "path": fp,
                            "name": f,
                            "size_bytes": sz,
                            "is_dir": False
                        })
                    except Exception:
                        pass

    freed_bytes = 0
    removed_count = 0
    errors = []
    category_counts = {}

    for item in items_to_clean:
        path = item["path"]
        cat = item["category"]
        size = item.get("size_bytes", 0)

        # Safety double-check against active paths
        if os.path.abspath(path).lower() in active_paths:
            continue

        try:
            if item.get("is_dir"):
                if os.path.exists(path):
                    shutil.rmtree(path, ignore_errors=True)
                    freed_bytes += size
                    removed_count += 1
                    category_counts[cat] = category_counts.get(cat, 0) + 1
            else:
                if os.path.exists(path):
                    os.remove(path)
                    freed_bytes += size
                    removed_count += 1
                    category_counts[cat] = category_counts.get(cat, 0) + 1
        except Exception as err:
            errors.append(f"Failed to delete {path}: {str(err)}")

    freed_mb = round(freed_bytes / (1024 * 1024), 2)
    print(f"[AutoCleanup] Successfully removed {removed_count} temporary items, freed {freed_mb} MB.")

    return {
        "status": "success",
        "freed_bytes": freed_bytes,
        "freed_mb": freed_mb,
        "files_removed": removed_count,
        "categories_cleaned": category_counts,
        "errors": errors if errors else None
    }


def get_storage_breakdown(project_state: Dict[str, Any], base_dir: str) -> Dict[str, Any]:
    """
    Calculate complete disk usage across all workspace directories and cleanable temp data.
    """
    def dir_size(d: str) -> int:
        if not os.path.exists(d):
            return 0
        total = 0
        for root, _, files in os.walk(d):
            for f in files:
                try:
                    total += os.path.getsize(os.path.join(root, f))
                except Exception:
                    pass
        return total

    upload_dir = os.path.join(base_dir, "uploads")
    thumbnail_dir = os.path.join(upload_dir, "thumbnails")
    voiceover_dir = os.path.join(upload_dir, "voiceovers")
    output_dir = os.path.join(base_dir, "output")
    music_dir = os.path.join(base_dir, "assets", "music")

    # Raw uploads size (excluding subdirectories thumbnails/voiceovers)
    raw_uploads_size = 0
    if os.path.exists(upload_dir):
        for f in os.listdir(upload_dir):
            fp = os.path.join(upload_dir, f)
            if os.path.isfile(fp):
                try:
                    raw_uploads_size += os.path.getsize(fp)
                except Exception:
                    pass

    thumbs_size = dir_size(thumbnail_dir)
    voiceovers_size = dir_size(voiceover_dir)
    outputs_size = dir_size(output_dir)
    music_size = dir_size(music_dir)

    total_storage = raw_uploads_size + thumbs_size + voiceovers_size + outputs_size + music_size
    scan = scan_unnecessary_data(project_state, base_dir)

    return {
        "total_used_mb": round(total_storage / (1024 * 1024), 2),
        "cleanable_mb": scan["total_cleanable_mb"],
        "cleanable_files": scan["total_cleanable_files"],
        "breakdown": {
            "rendered_vlogs_mb": round(outputs_size / (1024 * 1024), 2),
            "raw_video_uploads_mb": round(raw_uploads_size / (1024 * 1024), 2),
            "voiceovers_mb": round(voiceovers_size / (1024 * 1024), 2),
            "thumbnails_mb": round(thumbs_size / (1024 * 1024), 2),
            "music_assets_mb": round(music_size / (1024 * 1024), 2)
        },
        "cleanable_categories": scan["categories"]
    }
