import os
import subprocess
import uuid
import asyncio
from typing import Optional

try:
    import edge_tts  # type: ignore
    HAS_EDGE_TTS = True
except (ImportError, ModuleNotFoundError):
    HAS_EDGE_TTS = False

from gtts import gTTS


class VoiceEngine:
    """
    AI Heavy & Booming Cartoon Voice Engine.
    Exclusively features Gian-style deep, heavy, chubby, and comical cartoon characters:
    - Gian (Doraemon's Heavy Cartoon Bully)
    - Motu (Motu Patlu's Chubby Cartoon Food Lover)
    - Kalia Pehelwan (Chhota Bheem's Heavy Pehelwan)
    - Bob The Bulldog (Oggy's Heavy Bulldog Cartoon)
    - Inspector Chingum (Heavy Mustache Dabangg Cop)
    - Iron Giant / Monster (Heavy Cartoon Robot Monster)
    """

    LANG_MALE_VOICES = {
        "mr": "mr-IN-ManoharNeural",   # Rich Marathi Male Neural
        "hi": "hi-IN-MadhurNeural",    # Deep Hindi Male Neural
        "en": "en-IN-PrabhatNeural"    # Resonant Indian English Male Neural
    }

    VOICE_EFFECTS = {
        "gian_classic": {
            "id": "gian_classic",
            "name": "🦍 Gian (डोरेमॉनचा जाड व भारी जियान)",
            "desc": "The iconic deep, heavy, booming bully cartoon voice from Doraemon",
            "tts_rate": "-2%",
            "tts_pitch": "-5Hz",
            "filter": "asetrate=48000*0.84,atempo=1/0.84*0.98,aresample=48000,equalizer=f=120:t=q:w=1.0:g=5,equalizer=f=3000:t=q:w=1.2:g=3,alimiter=limit=0.96"
        },
        "motu_chubby_cartoon": {
            "id": "motu_chubby_cartoon",
            "name": "🍔 Motu (मोटू पतलूचा जाडजूड व खवय्या कार्टून)",
            "desc": "Chubby, heavy belly cartoon character with funny samosa-loving jolly tone",
            "tts_rate": "+0%",
            "tts_pitch": "-3Hz",
            "filter": "asetrate=48000*0.88,atempo=1/0.88*0.99,aresample=48000,equalizer=f=160:t=q:w=1.2:g=4,equalizer=f=3200:t=q:w=1.5:g=3.5,alimiter=limit=0.96"
        },
        "kalia_pehelwan": {
            "id": "kalia_pehelwan",
            "name": "🦁 Kalia Pehelwan (छोटा भीमचा जाड व दबंग कालिया)",
            "desc": "Heavy cartoon wrestling champion with boastful, loud and funny baritone power",
            "tts_rate": "-1%",
            "tts_pitch": "-6Hz",
            "filter": "asetrate=48000*0.80,atempo=1/0.80*0.97,aresample=48000,equalizer=f=100:t=q:w=1.0:g=6,equalizer=f=2600:t=q:w=1.2:g=3.5,alimiter=limit=0.96"
        },
        "oggy_bob_heavy": {
            "id": "oggy_bob_heavy",
            "name": "🐶 Bob The Bulldog (ऑगीचा जाडजूड बॉब कुत्रा कार्टून)",
            "desc": "Super heavy, roaring and funny muscular bulldog cartoon character from Oggy",
            "tts_rate": "-3%",
            "tts_pitch": "-8Hz",
            "filter": "asetrate=48000*0.76,atempo=1/0.76*0.96,aresample=48000,equalizer=f=90:t=q:w=0.9:g=8,equalizer=f=3400:t=q:w=1.2:g=3,alimiter=limit=0.96"
        },
        "chingum_heavy_cop": {
            "id": "chingum_heavy_cop",
            "name": "👮 Inspector Chingum (भारी मिशीवाले दबंग कार्टून इन्स्पेक्टर)",
            "desc": "Heavy-voiced mustache police officer cartoon caricature with roaring comedic punch",
            "tts_rate": "+1%",
            "tts_pitch": "-4Hz",
            "filter": "asetrate=48000*0.86,atempo=1/0.86*0.99,aresample=48000,equalizer=f=180:t=q:w=1.0:g=4,equalizer=f=2800:t=q:w=1.5:g=4,alimiter=limit=0.96"
        },
        "cartoon_iron_giant": {
            "id": "cartoon_iron_giant",
            "name": "🤖 Cartoon Iron Giant (राक्षसी व जाडजूड कार्टून रोबोट)",
            "desc": "Ultra-deep resonant cartoon robot / giant monster with heavy comic bass rumble",
            "tts_rate": "-4%",
            "tts_pitch": "-9Hz",
            "filter": "asetrate=48000*0.74,atempo=1/0.74*0.96,aresample=48000,equalizer=f=80:t=q:w=0.8:g=9,equalizer=f=3500:t=q:w=1.5:g=3,alimiter=limit=0.96"
        }
    }

    LANGUAGES = {
        "mr": "मराठी (Marathi - मनोहर आवाज)",
        "hi": "हिंदी (Hindi - मधुर आवाज)",
        "en": "Indian English (प्रभात आवाज)"
    }

    @classmethod
    async def generate_story_voice(
        cls,
        text: str,
        lang: str = "mr",
        voice_effect: str = "gian_classic",
        output_path: Optional[str] = None
    ) -> str:
        """
        Synthesizes Gian-style heavy cartoon voice with deep pitch, heavy formant, and crystal clarity.
        """
        clean_text = text.strip() if text else ""
        if not clean_text:
            raise ValueError("Story text cannot be empty.")

        if not output_path:
            raise ValueError("output_path is required.")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        raw_tts_path = output_path.replace(".mp3", f"_raw_{uuid.uuid4().hex[:6]}.mp3")

        valid_lang = lang if lang in cls.LANGUAGES else "mr"
        effect = cls.VOICE_EFFECTS.get(voice_effect) or cls.VOICE_EFFECTS["gian_classic"]
        male_voice = cls.LANG_MALE_VOICES.get(valid_lang, "mr-IN-ManoharNeural")
        
        rate = effect.get("tts_rate", "-2%")
        pitch = effect.get("tts_pitch", "-5Hz")

        # 1. Generate High-Definition Base Voice
        generated = False
        if HAS_EDGE_TTS:
            try:
                communicate = edge_tts.Communicate(clean_text, male_voice, rate=rate, pitch=pitch)
                await communicate.save(raw_tts_path)
                if os.path.exists(raw_tts_path) and os.path.getsize(raw_tts_path) > 1000:
                    generated = True
            except Exception as e:
                print(f"Edge-TTS synthesis error, falling back to gTTS: {e}")

        if not generated:
            loop = asyncio.get_event_loop()
            gtts_lang = "mr" if valid_lang == "mr" else ("hi" if valid_lang == "hi" else "en")
            await loop.run_in_executor(
                None,
                lambda: gTTS(text=text.strip(), lang=gtts_lang, slow=False).save(raw_tts_path)
            )

        # 2. Morph into Heavy Gian-Style Character
        filter_chain = effect["filter"]

        cmd = [
            "ffmpeg", "-y",
            "-i", raw_tts_path,
            "-af", filter_chain,
            "-c:a", "libmp3lame",
            "-b:a", "256k",
            "-threads", "0",
            output_path
        ]

        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(None, lambda: subprocess.run(cmd, capture_output=True, check=True))
        finally:
            if os.path.exists(raw_tts_path):
                try:
                    os.remove(raw_tts_path)
                except Exception:
                    pass

        return output_path

    @classmethod
    def apply_funny_effect_to_file(
        cls,
        input_audio_path: str,
        voice_effect: str = "gian_classic",
        output_path: Optional[str] = None
    ) -> str:
        """
        Morph recorded or uploaded audio track into heavy cartoon character.
        """
        if not os.path.exists(input_audio_path):
            raise FileNotFoundError(f"Audio file not found: {input_audio_path}")

        if not output_path:
            output_path = input_audio_path

        effect = cls.VOICE_EFFECTS.get(voice_effect) or cls.VOICE_EFFECTS["gian_classic"]
        filter_chain = effect["filter"]

        temp_dir = os.path.dirname(output_path) or "."
        temp_out = os.path.join(temp_dir, f"temp_{uuid.uuid4().hex[:8]}.mp3")

        cmd = [
            "ffmpeg", "-y",
            "-i", input_audio_path,
            "-af", filter_chain,
            "-c:a", "libmp3lame",
            "-b:a", "256k",
            "-threads", "0",
            temp_out
        ]

        try:
            subprocess.run(cmd, capture_output=True, check=True)
            if os.path.exists(output_path) and os.path.abspath(output_path) != os.path.abspath(temp_out):
                try:
                    os.remove(output_path)
                except Exception:
                    pass
            os.replace(temp_out, output_path)
            return output_path
        finally:
            if os.path.exists(temp_out):
                try:
                    os.remove(temp_out)
                except Exception:
                    pass
