# System Architecture: Sentinel-AI

## 1. High-Level Architecture

```mermaid
flowchart TB
    subgraph Clients["Clients & Channels"]
        UI["Low-Bandwidth Observer Console (/)"]
        API_CLIENTS["Tipline Bots / Partner Feeds (/api/v1)"]
    end

    subgraph FastAPI["FastAPI Async Backend (Python 3.11)"]
        INGEST["Ingestion & PII Scrubber\n(multilingual.py)"]
        TRIAGE["Track 1A Priority Triage\n(risk + spread + media)"]
        EMBED["ONNX Semantic Embeddings\n(fastembed all-MiniLM-L6-v2, 384-d)"]
        CLUSTER["Track 1B Narrative Clustering\n(clustering.py)"]
        RAG["Vector RAG & Abstention\n(rag.py + explainer.py)"]
        MEDIA["Track 1D Media Screener\n(Pillow EXIF + Gemini Vision)"]
        AUTH["Reviewer RBAC\n(X-Reviewer-Key)"]
    end

    subgraph Storage["PostgreSQL 16 + pgvector"]
        CLAIMS[("claims\n(embedding vector(384))")]
        NARRATIVES[("narratives\n(centroid_embedding vector(384))")]
        FACTS[("verified_facts\n(embedding vector(384))")]
        REVIEWS[("human_reviews\n(Immutable Audit Log)")]
    end

    UI --> FastAPI
    API_CLIENTS --> FastAPI
    INGEST --> TRIAGE --> EMBED
    EMBED --> CLUSTER --> NARRATIVES
    EMBED --> RAG --> FACTS
    CLUSTER --> CLAIMS
    UI --> MEDIA
    AUTH --> REVIEWS
```

## 2. Data Model & Storage Boundaries
- **`claims`:** Stores redacted text, detected language (`en`, `pcm`, `ha`, `yo`, `ig`), `risk_score`, `spread_score`, `synthetic_media_attached`, `triage_priority`, 384-dim `embedding`, and `status` (always initialized as `pending_human_review`).
- **`narratives`:** Stores `NarrativeCluster` centroids (`centroid_embedding`), `volume_count`, `velocity_score`, and escalated `threat_level`.
- **`verified_facts`:** Stores authoritative INEC Electoral Act 2022 rules and `#AI4Elections` multilingual voter FAQs with 384-dim `embedding`.
- **`human_reviews`:** Immutable audit trail of accredited reviewer decisions protected by `X-Reviewer-Key`.

## 3. Security, Privacy & Responsible AI Boundaries
- **NDPA 2023:** URLs, emails, `@handles`, phone numbers, and 11-digit IDs/NINs are scrubbed before database persistence; reporter tags containing emails/digits are hashed via `blake2b`.
- **Human-in-the-Loop:** No automated result declaration, no automated public labeling, and confidence-based abstention (`confidence < 0.48`) defers uncertain claims to human observers.
- **No Live System Access:** Strictly isolated from live INEC BVAS/IReV/voter register infrastructure.
