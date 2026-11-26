# Methodology: Sentinel-AI

## 1. Architecture & Pipeline
1. **Privacy-First Ingestion & Multilingual Normalization (`app/services/nlp/multilingual.py`):**
   - Redacts URLs, emails, `@handles`, Nigerian phone numbers, and 11-digit IDs/NINs (NDPA 2023 compliance).
   - Expands Nigerian electoral acronyms (`PU`, `BVAS`, `IReV`, `PVC`, `LGA`, `REC`).
   - Detects language across English (`en`), Nigerian Pidgin (`pcm`), Hausa (`ha`), Yoruba (`yo`), and Igbo (`ig`) using diacritic-stripped lexical scoring.
2. **Track 1A Claim Triage:**
   - Computes risk score (`0.0–1.0`) across multilingual electoral threat patterns and combines it with viral `spread_score` and `synthetic_media_attached` to rank the riskiest claims first.
3. **Track 1B Real-Time Semantic Clustering (`app/services/clustering.py`):**
   - Encodes normalized claims into 384-dimensional L2-normalized vectors using ONNX `fastembed` (`sentence-transformers/all-MiniLM-L6-v2`).
   - Matches against active `NarrativeCluster` centroids in PostgreSQL `pgvector` (`cosine_distance <= 0.48`), incrementally updating cluster centroids, volume, velocity (`/hr`), and threat level.
4. **Vector RAG & Explainability (`app/services/rag.py`, `app/services/explainer.py`):**
   - Queries 25 seeded authoritative INEC guidelines and multilingual voter FAQs in `pgvector` (`min_similarity = 0.25`).
   - Applies confidence-based abstention (`confidence < 0.48`) to defer uncertain claims to human fact-checkers, and generates 5-language clarification drafts (with optional Gemini 2.0 Flash enhancement).
5. **Track 1D Synthetic Media Screening (`app/services/media_screening.py`):**
   - Inspects uploaded image headers/EXIF metadata (and optional Gemini Vision cues) and outputs a guided verification checklist without making automated fake/real verdicts.

## 2. Evaluation Method
Evaluated via `scripts/evaluate.py` on the official 300-claim synthetic benchmark (`data/official/misinformation_claims_synthetic.jsonl`), measuring per-language precision/recall/F1, abstention rate on `unverifiable` claims, cluster compression ratio, and typo robustness.
