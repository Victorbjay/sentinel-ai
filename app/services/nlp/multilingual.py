import re
from typing import Tuple
from app.models.claim import ClaimLanguage

# Common Nigerian Pidgin markers & electoral vernacular
PIDGIN_KEYWORDS = {
    "dem", "dey", "wetin", "abi", "shebi", "sef", "wahala", "sha",
    "bvas don", "inec don", "result don", "na lie", "na so", "una",
    "make una", "no be", "comot", "pikin", "kuku", "scatter",
    "vote don", "ballot don", "thug don", "collect money"
}

HAUSA_KEYWORDS = {
    "zabe", "hukumar", "kuri'a", "shugaban", "jami'an", "akwati", "mutane"
}

YORUBA_KEYWORDS = {
    "idibo", "egbe", "awon", "oludije", "abo", "ilu", "apoti"
}

IGBO_KEYWORDS = {
    "ntuli", "aka", "ndu", "ochichi", "ndi", "ulo", "akwukwo"
}

# Standard electoral expansions for Nigerian context
ABBREVIATIONS = {
    r"\bPU\b": "Polling Unit",
    r"\bBVAS\b": "Bimodal Voter Accreditation System",
    r"\bIREV\b": "INEC Result Viewing Portal",
    r"\bIReV\b": "INEC Result Viewing Portal",
    r"\bLGA\b": "Local Government Area",
    r"\bREC\b": "Resident Electoral Commissioner",
    r"\bPVC\b": "Permanent Voter Card",
}


def clean_and_normalize_text(text: str) -> str:
    """Sanitizes text, normalizes spaces and standardizes electoral acronyms."""
    if not text:
        return ""
    
    # Strip URL and phone numbers / mentions for privacy (NDPA compliance)
    cleaned = re.sub(r"https?://\S+|www\.\S+", "", text)
    cleaned = re.sub(r"@[A-Za-z0-9_]+", "@user_anonymized", cleaned)
    cleaned = re.sub(r"\b(?:\+?234|0)[789][01]\d{8}\b", "[PHONE_REDACTED]", cleaned)

    # Normalize acronyms
    for pattern, replacement in ABBREVIATIONS.items():
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)

    # Normalize whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def detect_language(text: str) -> ClaimLanguage:
    """Lightweight rule-based language detector specialized for Nigerian regional context."""
    text_lower = text.lower()
    words = set(re.findall(r"\b\w+\b", text_lower))

    # Check Nigerian Pidgin
    pidgin_matches = sum(1 for phrase in PIDGIN_KEYWORDS if phrase in text_lower or phrase in words)
    if pidgin_matches >= 2 or ("don" in words and "dem" in words):
        return ClaimLanguage.PIDGIN

    # Check Hausa
    if any(k in words for k in HAUSA_KEYWORDS):
        return ClaimLanguage.HAUSA

    # Check Yoruba
    if any(k in words for k in YORUBA_KEYWORDS):
        return ClaimLanguage.YORUBA

    # Check Igbo
    if any(k in words for k in IGBO_KEYWORDS):
        return ClaimLanguage.IGBO

    return ClaimLanguage.ENGLISH


def process_claim_text(raw_text: str) -> Tuple[str, ClaimLanguage]:
    """Processes incoming raw text and returns normalized text + detected language."""
    cleaned = clean_and_normalize_text(raw_text)
    lang = detect_language(raw_text)
    return cleaned, lang
