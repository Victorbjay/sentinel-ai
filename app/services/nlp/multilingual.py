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


def compute_claim_risk_score(raw_text: str, cleaned_text: str) -> float:
    """
    Computes an initial electoral misinformation risk score (0.0 to 1.0)
    by checking both raw vernacular text and normalized text for high-severity
    electoral disruption narratives.
    """
    combined = f"{raw_text} {cleaned_text}".lower()

    critical_patterns = [
        r"\bbvas\b.{0,25}\b(spoil|fail|bypass|hack|not working|rig)\b",
        r"\b(cancel|postpone|suspend)\b.{0,25}\b(election|voting|poll)\b",
        r"\b(fake|doctored|leaked)\b.{0,20}\b(result|ec8a|irev)\b",
        r"\b(declare|declared|won)\b.{0,25}\b(winner|presiden|governor)\b",
        r"\b(thug|snatch|scatter|violence|shoot)\b.{0,25}\b(ballot|polling|box|pu)\b",
        r"\bgo home\b|\bgo house\b|\bno voting\b",
    ]
    medium_patterns = [
        r"\b(irev|portal|server)\b.{0,20}\b(down|crash|delay)\b",
        r"\b(pvc|voter card)\b.{0,20}\b(buy|sell|proxy|online)\b",
        r"\b(inec|officer|rec)\b.{0,20}\b(bribe|compromise|bias|late)\b",
        r"\b2:30\b|\bclosing time\b|\block out\b",
    ]

    score = 0.2
    for pat in critical_patterns:
        if re.search(pat, combined):
            score = max(score, 0.85)
    for pat in medium_patterns:
        if re.search(pat, combined):
            score = max(score, 0.6)

    return round(min(score, 1.0), 2)
