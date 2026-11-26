import math
from app.services.nlp.multilingual import (
    clean_and_normalize_text,
    detect_language,
    compute_claim_risk_score,
    pseudonymize_author,
)
from app.models.claim import ClaimLanguage
from app.services.embeddings import generate_embedding
from app.services.clustering import _update_running_centroid, _compute_threat_level
from app.services.explainer import generate_explainability_brief
from app.models.narrative import ThreatLevel
import pytest


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


def test_risk_score_pidgin_bvas_rumor():
    raw = "Dem say BVAS don spoil for PU 014 make una go house!"
    cleaned = clean_and_normalize_text(raw)
    score = compute_claim_risk_score(raw, cleaned)
    assert score >= 0.85


def test_embedding_generation():
    vec1 = generate_embedding("BVAS machine malfunction in polling unit")
    vec2 = generate_embedding("BVAS machine malfunction in polling unit")
    assert len(vec1) == 384
    assert vec1 == vec2
    norm = math.sqrt(sum(x * x for x in vec1))
    assert abs(norm - 1.0) < 1e-4


def test_clustering_centroid_and_threat():
    c1 = [1.0, 0.0, 0.0]
    c2 = [0.0, 1.0, 0.0]
    updated = _update_running_centroid(c1, c2, old_count=1)
    assert len(updated) == 3
    assert abs(updated[0] - updated[1]) < 1e-6

    assert _compute_threat_level(1, 0.2) == ThreatLevel.LOW
    assert _compute_threat_level(2, 0.2) == ThreatLevel.MEDIUM
    assert _compute_threat_level(5, 0.2) == ThreatLevel.HIGH
    assert _compute_threat_level(10, 0.2) == ThreatLevel.CRITICAL


@pytest.mark.asyncio
async def test_explainer_multilingual_brief():
    brief = await generate_explainability_brief(
        cleaned_text="Dem say Bimodal Voter Accreditation System don spoil",
        language=ClaimLanguage.PIDGIN,
        risk_score=0.85,
        matched_facts=[
            {
                "topic": "BVAS Accreditation",
                "official_fact": "BVAS is mandatory under Section 47(2).",
                "official_source": "Electoral Act 2022",
                "similarity_score": 0.72,
            }
        ],
    )
    assert brief["confidence_score"] > 0.5
    assert "pcm" in brief["multilingual_clarifications"]
    assert "pending_human_review" in brief["guardrail_notice"]
    assert "ha" in brief["multilingual_clarifications"]
    assert "yo" in brief["multilingual_clarifications"]
    assert "ig" in brief["multilingual_clarifications"]


def test_igbo_language_and_multilingual_risk():
    igbo = "Ndi omempako kwuputa na ha meriri ntuli aka tupu INEC agucha vootu."
    yoruba = "Awon oludije ti kede ara won gege bi olubori ibo ki INEC to pari kika."
    hausa = "Jami'an zabe sun rufe akwati tun karfe 2:30 na rana duk da mutane suna kan layi."
    assert detect_language(igbo) == ClaimLanguage.IGBO
    assert detect_language(yoruba) == ClaimLanguage.YORUBA
    assert detect_language(hausa) == ClaimLanguage.HAUSA
    assert compute_claim_risk_score(igbo, igbo) >= 0.85
    assert compute_claim_risk_score(yoruba, yoruba) >= 0.85
    assert compute_claim_risk_score(hausa, hausa) >= 0.85


def test_pii_redaction_and_pseudonymization():
    raw = "Contact john.doe@example.com or 08012345678 NIN 12345678901"
    cleaned = clean_and_normalize_text(raw)
    assert "[EMAIL_REDACTED]" in cleaned
    assert "[PHONE_REDACTED]" in cleaned
    assert "[ID_REDACTED]" in cleaned
    assert pseudonymize_author("john.doe@example.com").startswith("anon_")
