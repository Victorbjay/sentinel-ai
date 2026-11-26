# Datasheet: Sentinel-AI Datasets

1. **Motivation:** Used to seed authoritative Nigerian electoral rules and evaluate Track 1 claim triage, clustering, and multilingual fact-checking without touching live voter or institutional data.
2. **Composition:**
   - `data/seeds/inec_verified_facts.json`: 5 curated INEC Electoral Act 2022 & Regulations rules (`topic`, `claim_summary`, `official_fact`, `official_source`, `source_url`).
   - `data/official/voter_info_faq_multilingual.csv`: 20 official `#AI4Elections` synthetic/public voter FAQs in `en`, `pcm_draft`, `ha`, `yo`, `ig`, with `answer_en`.
   - `data/official/misinformation_claims_synthetic.jsonl`: 300 official `#AI4Elections` synthetic claims (`claim_id`, `text`, `label`, `language`, `channel`, `synthetic_media_attached`, `spread_score`).
   - **Personal data:** None. All claims are 100% synthetic.
3. **Collection process:** Provided by Rise Networks `#AI4Elections` Hackathon starter repository (`Rise-Networks-AI-Labs/-AI4Elections-Hackathon`) and public INEC 2022 Regulations & Electoral Act 2022 text.
4. **Preprocessing:** Acronym expansion (`PU`, `BVAS`, `IReV`, `PVC`, `LGA`), Unicode diacritic normalization, and PII regex scrubbing.
5. **Uses:** Benchmarking claim triage, semantic clustering, and RAG retrieval. Must not be used to train partisan classifiers or profile real individuals.
6. **Distribution:** CC BY 4.0 (documentation and synthetic data) via `github.com/Victorbjay/sentinel-ai`.
7. **Maintenance:** Maintained by Sentinel AI Labs; re-seeded idempotently via `scripts/seed_db.py`.
8. **Known limitations and biases:** `misinformation_claims_synthetic.jsonl` primarily covers `en` and `pcm`; `ha`, `yo`, and `ig` claims are covered in `voter_info_faq_multilingual.csv` and custom unit tests.
