import logging
from typing import List, Dict, Any, Optional
import httpx
from app.core.config import settings
from app.models.claim import ClaimLanguage

logger = logging.getLogger(__name__)


def _build_multilingual_clarifications(
    matched_fact: Optional[Dict[str, Any]],
    language: ClaimLanguage,
) -> Dict[str, str]:
    """
    Produces concise, low-bandwidth public clarification drafts in English and
    major Nigerian languages grounded strictly in the matched INEC fact.
    """
    if not matched_fact:
        return {
            "en": (
                "UNVERIFIED CLAIM: Accredited election observers are currently reviewing this report "
                "against official INEC guidelines. Rely only on verified INEC channels."
            ),
            "pcm": (
                "UNVERIFIED TORI: Accredited observers still dey check dis matter with official INEC rule. "
                "No panic, wait for verified INEC update."
            ),
        }

    topic = matched_fact.get("topic", "INEC Guidelines")
    fact_text = matched_fact.get("official_fact", "")
    source = matched_fact.get("official_source", "INEC Official Guidelines")

    clarifications = {
        "en": f"FACT CHECK ({topic}): {fact_text} [Source: {source}]",
        "pcm": (
            f"FACT CHECK ({topic}): Make una know the real law — {fact_text} "
            f"Official source na: {source}."
        ),
        "ha": (
            f"TABBASCIN GASKIYA ({topic}): Hukumar zabe ta INEC ta bayyana cewa: {fact_text} "
            f"[Tushe: {source}]"
        ),
        "yo": (
            f"IFIDANI OTITO ({topic}): Gege bi ilana INEC: {fact_text} "
            f"[Orisun: {source}]"
        ),
        "ig": (
            f"EZIOKWU NKE INEC ({topic}): Dika iwu INEC siri kwuo: {fact_text} "
            f"[Isi mmalite: {source}]"
        ),
    }

    return clarifications


async def _try_gemini_rationale(
    cleaned_text: str,
    matched_facts: List[Dict[str, Any]],
    risk_score: float,
) -> Optional[str]:
    """Optional Gemini API call when GEMINI_API_KEY is configured."""
    if not settings.GEMINI_API_KEY:
        return None

    facts_context = "\n".join(
        f"- [{f.get('topic')}] {f.get('official_fact')} (Source: {f.get('official_source')})"
        for f in matched_facts
    )
    prompt = (
        "You are an impartial electoral fact-checking assistant for Nigeria's #AI4Elections monitor. "
        "Never declare election winners or make legal determinations of fraud. "
        "In 2-3 concise sentences, explain why the following claim is flagged for human review "
        "and how it compares against the verified INEC facts below.\n\n"
        f"Claim: {cleaned_text}\nRisk Score: {risk_score}\nVerified Facts:\n{facts_context}"
    )
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.0-flash:generateContent?key={settings.GEMINI_API_KEY}"
    )
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(
                url,
                json={"contents": [{"parts": [{"text": prompt}]}]},
            )
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts and parts[0].get("text"):
                        return parts[0]["text"].strip()
    except Exception as e:
        logger.warning(f"Gemini rationale generation failed, using grounded fallback: {e}")
    return None


async def generate_explainability_brief(
    cleaned_text: str,
    language: ClaimLanguage,
    risk_score: float,
    matched_facts: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Generates an explainable AI assessment for human fact-checkers:
    - rationale (plain-language explanation grounded in INEC rules)
    - confidence_score (combined vector similarity & risk signal)
    - provenance (list of official INEC sources)
    - multilingual_clarifications (draft public advisories)
    - guardrail_notice (strict HITL reminder)
    """
    top_fact = matched_facts[0] if matched_facts else None
    top_sim = float(top_fact.get("similarity_score") or 0.0) if top_fact else 0.0

    # Confidence reflects how strongly the claim aligns with a known electoral rule & risk pattern
    confidence = round(min(0.98, max(0.25, (top_sim * 0.65) + (risk_score * 0.35))), 2)
    abstention_threshold = 0.48
    should_abstain = confidence < abstention_threshold or top_fact is None

    llm_rationale = await _try_gemini_rationale(cleaned_text, matched_facts, risk_score)
    if llm_rationale:
        rationale = llm_rationale
    elif should_abstain:
        rationale = (
            "No closely matching official INEC rule found. This claim requires manual verification by an accredited "
            "observer to verify against field conditions or authoritative sources."
        )
    else:
        rationale = (
            f"Flagged with risk score {risk_score:.2f} in language '{language.value}'. "
            f"Semantic vector search matched this claim to '{top_fact['topic']}' "
            f"(similarity {top_sim:.2f}). Official rule ({top_fact['official_source']}): "
            f"{top_fact['official_fact']}"
        )

    provenance = [
        {
            "topic": f.get("topic"),
            "official_source": f.get("official_source"),
            "similarity_score": f.get("similarity_score"),
        }
        for f in matched_facts
    ]

    return {
        "rationale": rationale,
        "confidence_score": confidence,
        "should_abstain": should_abstain,
        "abstention_threshold": abstention_threshold,
        "provenance": provenance,
        "multilingual_clarifications": _build_multilingual_clarifications(top_fact, language),
        "guardrail_notice": (
            "HITL Required: Status is pending_human_review. Sentinel-AI never auto-declares "
            "election outcomes or legal fraud determinations."
        ),
    }
