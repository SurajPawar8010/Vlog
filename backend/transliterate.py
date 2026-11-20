import re
import requests
from typing import Optional

# In-memory cache for fast repeated word/sentence transliteration
TRANSLITERATION_CACHE: dict[str, str] = {}

# Offline phonetic fallback dictionary for common Marathi/Hindi conversational words
OFFLINE_PHONETIC_DICT_MR = {
    "aaj": "आज",
    "aaji": "आजी",
    "aamhi": "आम्ही",
    "aani": "आणि",
    "ani": "आणि",
    "ata": "आता",
    "aata": "आता",
    "ahe": "आहे",
    "aahe": "आहे",
    "ahet": "आहेत",
    "aahet": "आहेत",
    "office": "ऑफिस",
    "office la": "ऑफिसला",
    "officela": "ऑफिसला",
    "mi": "मी",
    "mee": "मी",
    "la": "ला",
    "lavakar": "लवकर",
    "lavkar": "लवकर",
    "gelo": "गेलो",
    "geli": "गेली",
    "gele": "गेले",
    "kasa": "कसा",
    "kashi": "कशी",
    "kase": "कसे",
    "kay": "काय",
    "kahi": "काही",
    "kharach": "खरंच",
    "khup": "खूप",
    "khoop": "खूप",
    "changla": "चांगला",
    "changli": "चांगली",
    "changle": "चांगले",
    "divas": "दिवस",
    "sakali": "सकाळी",
    "sandhyakali": "संध्याकाळी",
    "ratra": "रात्र",
    "ratri": "रात्री",
    "kam": "काम",
    "kaam": "काम",
    "chalu": "चालू",
    "hota": "होता",
    "hoti": "होती",
    "hote": "होते",
    "zal": "झालं",
    "jhala": "झाला",
    "jhali": "झाली",
    "jhale": "झाले",
    "ghari": "घरी",
    "ghar": "घर",
    "chaha": "चहा",
    "nasta": "नाश्ता",
    "jevan": "जेवण",
    "jevlo": "जेवलो",
    "coding": "कोडिंग",
    "video": "व्हिडिओ",
    "vlog": "व्लॉग",
    "reel": "रील",
    "workout": "वर्कआउट",
    "gym": "जिम",
    "laptop": "लॅपटॉप",
    "project": "प्रोजेक्ट",
    "task": "टास्क",
    "client": "क्लायंट",
    "meeting": "मीटिंग",
    "call": "कॉल",
    "boss": "बॉस",
    "mitra": "मित्र",
    "dost": "दोस्त",
    "por": "पोरं",
    "bhai": "भाई",
    "bhava": "भावा",
    "ekdam": "एकदम",
    "bhari": "भारी",
    "mast": "मस्त",
    "kadak": "कडक",
    "dhamaal": "धमाल",
    "shiklo": "शिकलो",
    "pahije": "पाहिजे",
    "karaycha": "करायचं",
    "kela": "केला",
    "keli": "केली",
    "kele": "केले",
    "bagha": "बघा",
    "bghitla": "बघितलं",
    "sangto": "सांगतो",
    "sangitla": "सांगितलं",
    "nusta": "नुसता",
    "nusti": "नुसती",
    "raada": "राडा",
    "rada": "राडा"
}

def transliterate_text(text: str, target_lang: str = "mr") -> str:
    """
    Transliterate Roman/Hinglish/Marathinglish text into Devanagari script.
    e.g. "Aaj mi office la lavakar gelo" -> "आज मी ऑफिसला लवकर गेलो"
    """
    if not text or not text.strip():
        return text

    cache_key = f"{target_lang}:{text.strip()}"
    if cache_key in TRANSLITERATION_CACHE:
        return TRANSLITERATION_CACHE[cache_key]

    # Clean target language code
    lang_code = "mr" if target_lang.lower().startswith("mr") else ("hi" if target_lang.lower().startswith("hi") else "mr")
    itc_code = f"{lang_code}-t-i0-und"

    # Break text preserving paragraphs, newlines, and trailing spaces
    lines = text.split("\n")
    transliterated_lines = []

    for line in lines:
        if not line.strip():
            transliterated_lines.append(line)
            continue

        try:
            # Query Google Input Tools Transliteration API (fast, free, accurate)
            url = f"https://inputtools.google.com/request?text={requests.utils.quote(line)}&itc={itc_code}&num=1&cp=0&cs=1&ie=utf-8&oe=utf-8&app=demopage"
            resp = requests.get(url, timeout=3.5)
            
            if resp.status_code == 200:
                data = resp.json()
                if data and len(data) >= 2 and data[0] == "SUCCESS":
                    tokens_data = data[1]
                    converted_words = []
                    for item in tokens_data:
                        orig_word = item[0]
                        matched_words = item[1]
                        if matched_words and len(matched_words) > 0:
                            converted_words.append(matched_words[0])
                        else:
                            converted_words.append(orig_word)
                    
                    transliterated_line = " ".join(converted_words)
                    # Fix spacing before common punctuation
                    transliterated_line = re.sub(r'\s+([,.\?!;:])', r'\1', transliterated_line)
                    transliterated_lines.append(transliterated_line)
                    continue
        except Exception as e:
            # Fallback to local rule dictionary
            pass

        # Offline local dictionary fallback token by token
        words = re.findall(r"[\w']+|[.,!?;:]|\s+", line)
        out_tokens = []
        for w in words:
            clean_lower = w.strip().lower()
            if clean_lower in OFFLINE_PHONETIC_DICT_MR:
                out_tokens.append(OFFLINE_PHONETIC_DICT_MR[clean_lower])
            else:
                out_tokens.append(w)
        transliterated_lines.append("".join(out_tokens))

    result = "\n".join(transliterated_lines)
    TRANSLITERATION_CACHE[cache_key] = result
    return result
