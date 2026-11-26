import pytest
from app.services.nlp.multilingual import clean_and_normalize_text, detect_language, process_claim_text
from app.models.claim import ClaimLanguage
from app.services.rag import generate_mock_or_deterministic_embedding


def test_clean_and_normalize_acronyms():
    raw = "The PU presiding officer said BVAS is slow and IREV is down @pollingofficer_xyz"
    cleaned = clean_and_normalize_text(raw)
    assert "Polling Unit" in cleaned
    assert "Bimodal Voter Accreditation System" in cleaned
    assert "INEC Result Viewing Portal" in cleaned
    assert "@user_anonymized" in cleaned


def test_pidgin_language_detection():
    pidgin_text = "Make una hear wetin dey happen for our PU, dem say result don leak!"
    lang = detect_language(pidgin_text)
    assert lang == ClaimLanguage.PIDGIN


def test_english_language_detection():
    english_text = "The voting process in the polling center commenced at 8:30 AM without incident."
    lang = detect_language(english_text)
    assert lang == ClaimLanguage.ENGLISH


def test_hausa_language_detection():
    hausa_text = "Jami'an zabe sun fara tantance masu kuri'a a akwati daban daban."
    lang = detect_language(hausa_text)
    assert lang == ClaimLanguage.HAUSA


def test_embedding_generation():
    vec1 = generate_mock_or_deterministic_embedding("BVAS machine malfunction in polling unit", 384)
    vec2 = generate_mock_or_deterministic_embedding("BVAS machine malfunction in polling unit", 384)
    assert len(vec1) == 384
    assert vec1 == vec2  # Deterministic check
