import hashlib
import re
import unicodedata
from typing import Optional, Tuple
from app.models.claim import ClaimLanguage

# Common Nigerian Pidgin markers & electoral vernacular
PIDGIN_KEYWORDS = {
    "dem", "dey", "wetin", "abi", "shebi", "sef", "wahala", "sha",
    "bvas don", "inec don", "result don", "na lie", "na so", "una",
    "make una", "no be", "comot", "pikin", "kuku", "scatter",
    "vote don", "ballot don", "thug don", "collect money", "go house",
}

HAUSA_KEYWORDS = {
    "zabe", "hukumar", "kuri'a", "kuria", "shugaban", "jami'an", "jamian",
    "akwati", "mutane", "rufe", "karfe", "layi", "sakamakon", "nasara",
}

YORUBA_KEYWORDS = {
    "idibo", "egbe", "awon", "oludije", "abo", "ilu", "apoti",
    "kede", "olubori", "kika", "ibo", "gege", "pari",
}

IGBO_KEYWORDS = {
    "ntuli", "ntuli aka", "vootu", "igbe", "nchikota", "ihe nsonaazu",
    "ochichi", "ndi", "ulo", "akwukwo", "kwusiri", "meriri", "eboro",
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


def _strip_diacritics(text: str) -> str:
    """Strips Unicode combining marks so accented Yoruba/Igbo/Hausa match cleanly."""
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def pseudonymize_author(author_id: Optional[str]) -> Optional[str]:
    """
    NDPA 2023 compliance: if a user or feed supplies an email, phone, or handle
    as author_anonymized_id, hash it into a non-reversible pseudonymous tag.
    """
    if not author_id:
        return None
    cleaned = author_id.strip()
    if not cleaned:
        return None
    if "@" in cleaned or re.search(r"\d{7,}", cleaned):
        digest = hashlib.blake2b(cleaned.encode("utf-8"), digest_size=6).hexdigest()
        return f"anon_{digest}"
    return cleaned[:64]


def clean_and_normalize_text(text: str) -> str:
    """Sanitizes text, redacts PII (NDPA 2023), and standardizes electoral acronyms."""
    if not text:
        return ""

    # Strip URLs, emails, handles, phone numbers, and 11-digit IDs/NINs for privacy
    cleaned = re.sub(r"https?://\S+|www\.\S+", "", text)
    cleaned = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "[EMAIL_REDACTED]", cleaned)
    cleaned = re.sub(r"@[A-Za-z0-9_]+", "@user_anonymized", cleaned)
    cleaned = re.sub(r"\b(?:\+?234|0)[789][01]\d{8}\b", "[PHONE_REDACTED]", cleaned)
    cleaned = re.sub(r"\b\d{11}\b", "[ID_REDACTED]", cleaned)

    # Normalize acronyms
    for pattern, replacement in ABBREVIATIONS.items():
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)

    # Normalize whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _count_lexicon_hits(text_lower: str, words: set, lexicon: set) -> int:
    hits = 0
    for term in lexicon:
        if " " in term:
            if term in text_lower:
                hits += 2  # Multi-word phrase is a strong signal
        elif term in words:
            hits += 1
    return hits


def detect_language(text: str) -> ClaimLanguage:
    """Diacritic-aware language detector specialized for Nigerian regional context."""
    text_lower = _strip_diacritics(text.lower())
    words = set(re.findall(r"\b[\w']+\b", text_lower))

    pidgin_hits = _count_lexicon_hits(text_lower, words, PIDGIN_KEYWORDS)
    if pidgin_hits >= 2 or ("don" in words and ("dem" in words or "una" in words)):
        return ClaimLanguage.PIDGIN

    scores = {
        ClaimLanguage.HAUSA: _count_lexicon_hits(text_lower, words, HAUSA_KEYWORDS),
        ClaimLanguage.YORUBA: _count_lexicon_hits(text_lower, words, YORUBA_KEYWORDS),
        ClaimLanguage.IGBO: _count_lexicon_hits(text_lower, words, IGBO_KEYWORDS),
    }
    best_lang, best_score = max(scores.items(), key=lambda kv: kv[1])
    if best_score >= 2:
        return best_lang

    return ClaimLanguage.ENGLISH


def process_claim_text(raw_text: str) -> Tuple[str, ClaimLanguage]:
    """Processes incoming raw text and returns normalized text + detected language."""
    cleaned = clean_and_normalize_text(raw_text)
    lang = detect_language(raw_text)
    return cleaned, lang


def compute_claim_risk_score(raw_text: str, cleaned_text: str) -> float:
    """
    Computes an electoral misinformation risk score (0.0 to 1.0) across
    English, Nigerian Pidgin, Hausa, Yoruba, and Igbo electoral threat patterns.
    """
    combined = _strip_diacritics(f"{raw_text} {cleaned_text}".lower())

    critical_patterns = [
        # English & Pidgin
        r"\bbvas\b.{0,25}\b(spoil|fail|bypass|hack|not working|rig)\b",
        r"\b(cancel|cancelled|postpone|moved to next week|suspend)\b.{0,30}\b(election|voting|poll|collation|app)\b",
        r"\b(fake|doctored|leaked)\b.{0,20}\b(result|ec8a|irev)\b",
        r"\b(declare|declared|won)\b.{0,25}\b(winner|presiden|governor)\b",
        r"\b(thug|snatch|scatter|violence|shoot)\b.{0,25}\b(ballot|polling|box|pu)\b",
        r"\b(whole process is rigged|entire election is compromised)\b",
        r"\b(cash reward)\b.{0,25}\b(ballot|photo)\b",
        r"\bgo home\b|\bgo house\b|\bstay at home\b|\bno voting\b",
        # Hausa: premature winner, closing polling unit on queue, ballot snatching/rigging
        r"\b(kede|sanar)\b.{0,25}\b(nasara|shugaba|lashe)\b",
        r"\b(rufe|hana)\b.{0,25}\b(akwati|zabe)\b",
        r"\b(sace|kwace)\b.{0,25}\b(akwati|kuri'?a)\b",
        # Yoruba: premature winner declaration, ballot snatching, bvas/voting disruption
        r"\b(kede|so)\b.{0,25}\b(olubori|bori|wole)\b",
        r"\b(ji|gba)\b.{0,25}\b(apoti|idibo)\b",
        # Igbo: premature winner, ballot box snatching, BVAS failure / stopped voting
        r"\b(kwuputa|meriri)\b.{0,25}\b(ntuli|onye mmeri|ochichi)\b",
        r"\b(zuru|napu|kwusiri)\b.{0,25}\b(igbe|vootu|ntuli)\b",
    ]
    medium_patterns = [
        r"\b(irev|portal|server|voting app)\b.{0,20}\b(down|crash|delay|hack|wrong|problem)\b",
        r"\b(pvc|voter card|voter register)\b.{0,20}\b(buy|sell|proxy|online|print|problem)\b",
        r"\b(inec|officer|rec)\b.{0,20}\b(bribe|compromise|bias|late)\b",
        r"\b2:30\b|\bclosing time\b|\block out\b|\bkarfe 2:30\b",
        r"\b(bvas|igbe|apoti|akwati)\b.{0,25}\b(adighi|ko|baje|lalace)\b",
    ]

    score = 0.2
    for pat in critical_patterns:
        if re.search(pat, combined):
            score = max(score, 0.85)
    for pat in medium_patterns:
        if re.search(pat, combined):
            score = max(score, 0.6)

    return round(min(score, 1.0), 2)


def compute_triage_priority(
    risk_score: float,
    spread_score: int = 0,
    synthetic_media_attached: bool = False,
) -> float:
    """
    Track 1A Claim Triage: ranks incoming claims by likely harm, viral spread,
    and presence of synthetic/manipulated media so limited fact-checkers see riskiest first.
    """
    spread_norm = max(0.0, min(1.0, spread_score / 100.0))
    media_boost = 0.12 if synthetic_media_attached else 0.0
    priority = (risk_score * 0.60) + (spread_norm * 0.28) + media_boost
    return round(min(1.0, priority), 3)
