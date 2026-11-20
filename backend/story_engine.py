import os
from datetime import datetime
from typing import Optional

class StoryEngine:
    """
    Intelligent Narrative & Pacing Engine for Daily Work Vlogs.
    Structures all uploaded clips into an engaging daily story arc with
    customizable original audio modes and clip orientation controls.
    """

    PRESETS = {
        "fast_reel": {
            "name": "⚡ Fast-Paced Reel (30-60s)",
            "target_duration": 45,
            "max_clip_duration": 5.0,
            "timelapse_speed": 6.0,
            "hook_duration": 3.0,
            "transition": "cut",
            "vibe": "Energetic, punchy, fast cuts"
        },
        "productive_vlog": {
            "name": "💻 Productive Workday (60-90s)",
            "target_duration": 75,
            "max_clip_duration": 8.0,
            "timelapse_speed": 4.0,
            "hook_duration": 4.0,
            "transition": "crossfade",
            "vibe": "Focused, motivating, clear story chapters"
        },
        "cinematic_lofi": {
            "name": "☕ Cinematic Lo-Fi (60-120s)",
            "target_duration": 90,
            "max_clip_duration": 12.0,
            "timelapse_speed": 3.0,
            "hook_duration": 4.5,
            "transition": "fadeblack",
            "vibe": "Aesthetic, chill, cozy ambient"
        }
    }

    CHAPTER_TITLES = [
        "🌅 09:00 AM • Morning Kickoff",
        "☕ Workspace & Daily Focus",
        "⚡ Deep Work & Coding Flow",
        "🚀 Crushing the Big Milestone",
        "🛠️ Debugging & Polishing",
        "✨ Final Demo & Day Wrap-Up"
    ]

    @classmethod
    def generate_story_plan(
        cls,
        clips: list[dict],
        preset_key: str = "fast_reel",
        audio_mode: str = "mute_all",  # mute_all, smart_speech, keep_all
        aspect_ratio: str = "9:16",
        target_voice_duration: Optional[float] = None
    ) -> dict:
        """
        Analyze uploaded clips and generate a structured story timeline.
        If target_voice_duration is provided, automatically calibrates clip speeds
        and durations so the total video runtime matches the voiceover audio duration 100%!
        """
        if not clips:
            return {"timeline": [], "estimated_total_duration": 0, "preset": preset_key, "summary": "No clips provided"}

        preset = cls.PRESETS.get(preset_key, cls.PRESETS["fast_reel"])

        # Keep the exact clip sequence (supports custom manual user reordering)
        sorted_clips = list(clips)
        total_clips = len(sorted_clips)

        # Check if Voiceover-Driven Auto-Pacing Mode is Active
        is_voice_sync = bool(target_voice_duration and target_voice_duration > 2.0)

        # Allocate target durations per clip if voice sync is active
        target_clip_durs = {}
        if is_voice_sync:
            T_target = float(target_voice_duration)
            if total_clips == 1:
                target_clip_durs[0] = T_target
            elif total_clips == 2:
                target_clip_durs[0] = round(T_target * 0.5, 2)
                target_clip_durs[1] = round(T_target * 0.5, 2)
            else:
                hook_d = min(3.5, round(T_target * 0.14, 2))
                outro_d = min(3.5, round(T_target * 0.14, 2))
                rem_time = max(1.0, T_target - (hook_d + outro_d))
                middle_indices = list(range(1, total_clips - 1))
                mid_raw_sum = sum(float(sorted_clips[i].get("duration", 5.0)) for i in middle_indices) or (len(middle_indices) * 5.0)

                target_clip_durs[0] = hook_d
                target_clip_durs[total_clips - 1] = outro_d

                for mi in middle_indices:
                    raw_d = float(sorted_clips[mi].get("duration", 5.0))
                    portion = raw_d / mid_raw_sum if mid_raw_sum > 0 else (1.0 / len(middle_indices))
                    target_clip_durs[mi] = round(rem_time * portion, 2)

                # Fix tiny floating rounding difference on middle clip
                allocated_sum = sum(target_clip_durs.values())
                diff = round(T_target - allocated_sum, 2)
                if abs(diff) > 0.01:
                    target_clip_durs[middle_indices[0]] = round(target_clip_durs[middle_indices[0]] + diff, 2)

        timeline = []

        for idx, clip in enumerate(sorted_clips):
            raw_duration = float(clip.get("duration", 5.0))
            is_silent = clip.get("is_silent", True)
            has_audio = clip.get("has_audio", False)
            filename = os.path.basename(clip.get("file_path", f"Clip {idx+1}"))
            user_rotation = int(clip.get("rotation", 0))

            # Determine Story Role
            if idx == 0:
                role = "HOOK"
                role_label = "⚡ Hook (Dynamic Opener)"
                hud_title = "DAILY LOG // START"
            elif idx == total_clips - 1 and total_clips > 2:
                role = "OUTRO"
                role_label = "🌙 Outro (Day Wrap-Up)"
                hud_title = "WRAPPING UP // SIGN OFF"
            elif not is_silent and has_audio:
                role = "HIGHLIGHT"
                role_label = "🎙️ Speaking Highlight"
                hud_title = f"UPDATE // {filename[:15]}"
            else:
                role = "TIMELAPSE"
                role_label = "⏩ Deep Work Timelapse"
                hud_title = f"FOCUS MODE"

            # If this clip already has an attached per-clip voiceover, respect its duration and speed
            has_clip_vo = bool(clip.get("voiceover_duration") and clip.get("voiceover_duration", 0) > 0.3)
            if has_clip_vo:
                vo_dur = float(clip["voiceover_duration"])
                speed = max(0.25, min(16.0, round(raw_duration / vo_dur, 2)))
                cut_duration = round(raw_duration / speed, 2)
            elif is_voice_sync and idx in target_clip_durs:
                desired_dur = max(0.5, target_clip_durs[idx])
                calc_speed = max(0.25, min(16.0, round(raw_duration / desired_dur, 2)))
                speed = calc_speed
                cut_duration = round(raw_duration / speed, 2)
                if role == "TIMELAPSE":
                    hud_title = f"FOCUS // {speed}X SPEED"
            else:
                if role == "HOOK":
                    speed = 1.0
                    cut_duration = min(raw_duration, preset["hook_duration"])
                elif role == "OUTRO":
                    speed = 1.0
                    cut_duration = min(raw_duration, 4.0)
                elif role == "HIGHLIGHT":
                    speed = 1.0
                    cut_duration = min(raw_duration, preset["max_clip_duration"])
                else:
                    speed = preset["timelapse_speed"]
                    calculated_duration = raw_duration / speed
                    if calculated_duration > preset["max_clip_duration"]:
                        raw_duration = preset["max_clip_duration"] * speed
                        calculated_duration = preset["max_clip_duration"]
                    cut_duration = calculated_duration
                    hud_title = f"FOCUS MODE // {int(speed)}X SPEED"

            # Determine audio mute status based on audio_mode
            if audio_mode == "mute_all":
                mute_clip_audio = True
            elif audio_mode == "keep_all":
                mute_clip_audio = False
            else:  # smart_speech
                mute_clip_audio = (role == "TIMELAPSE" or is_silent or not has_audio)

            # Assign chapter title
            title_index = min(idx, len(cls.CHAPTER_TITLES) - 1)
            chapter_title = cls.CHAPTER_TITLES[title_index]

            timeline_item = {
                "id": clip.get("id", f"clip_{idx}"),
                "file_path": clip.get("file_path"),
                "filename": filename,
                "thumbnail_url": clip.get("thumbnail_url", ""),
                "order": idx,
                "role": role,
                "role_label": role_label,
                "speed_multiplier": speed,
                "start_time": 0.0,
                "end_time": round(min(raw_duration, clip.get("duration", 5.0)), 2),
                "final_duration": round(cut_duration, 2),
                "is_silent": is_silent,
                "hud_title": hud_title,
                "chapter_title": chapter_title,
                "mute_original_audio": mute_clip_audio,
                "rotation": user_rotation,
                "is_vertical": clip.get("is_vertical", False),
                "aspect_ratio": aspect_ratio,
                "voiceover_file": clip.get("voiceover_file"),
                "voiceover_url": clip.get("voiceover_url"),
                "voiceover_text": clip.get("voiceover_text", ""),
                "voiceover_lang": clip.get("voiceover_lang", "mr"),
                "voiceover_effect": clip.get("voiceover_effect", "gian_classic"),
                "voiceover_duration": clip.get("voiceover_duration", 0.0)
            }
            timeline.append(timeline_item)

        est_total = sum(item["final_duration"] for item in timeline)

        audio_mode_desc = (
            "100% Original Audio Muted (Soundtrack Only)" if audio_mode == "mute_all"
            else "Smart Speech Filtering & Denoising" if audio_mode == "smart_speech"
            else "Original Audio Preserved"
        )

        if is_voice_sync:
            story_summary = (
                f"🎯 Voiceover-Synchronized Pacing: Calibrated {len(timeline)} clips to match your "
                f"~{round(target_voice_duration, 1)}s voiceover audio perfectly! (Video runtime: ~{round(est_total, 1)}s)"
            )
        else:
            story_summary = (
                f"Crafted a {len(timeline)}-scene daily story arc in '{preset['name']}' style. "
                f"Total estimated runtime: ~{round(est_total, 1)}s. "
                f"Audio Mode: {audio_mode_desc}. Applied {preset['timelapse_speed']}x speed ramping on silent desk work."
            )

        return {
            "preset": preset_key,
            "audio_mode": audio_mode,
            "preset_info": preset,
            "timeline": timeline,
            "estimated_total_duration": round(est_total, 1),
            "story_summary": story_summary,
            "target_voice_duration": target_voice_duration if is_voice_sync else None
        }

