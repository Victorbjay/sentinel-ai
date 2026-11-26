# Evaluation Report: Sentinel-AI (#AI4Elections Track 1)

1. **Objective and success criteria:** Evaluate Sentinel-AI on Track 1A (Claim Triage), Track 1B (Semantic Claim Clustering & Matching), and Track 1C/1D (Abstention & Provenance) using per-language precision/recall, abstention rate on unverifiable claims, simulated reviewer time saved via clustering, and typo robustness.
2. **Test data:** Official `#AI4Elections` synthetic dataset (`data/official/misinformation_claims_synthetic.jsonl`, **n = 300** synthetic Nigerian election claims across `en` and `pcm` channels). Zero live or personal voter data used.
3. **Baselines:** Simple keyword baseline vs. Sentinel-AI's normalized multilingual pattern + `fastembed` (`all-MiniLM-L6-v2`) semantic vector clustering + `pgvector` RAG pipeline.
4. **Results (Triage Risk Flagging, threshold >= 0.50):**

| Slice | n | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| Overall (excluding unverifiable) | 248 | 1.000 | 0.804 | 0.891 |
| Language: `en` | 161 | 1.000 | 0.793 | 0.884 |
| Language: `pcm` | 87 | 1.000 | 0.825 | 0.904 |

5. **Human-in-the-loop impact:**
   - **Cluster compression:** 300 raw claims collapsed into **9 narrative clusters** (**97.0% reduction** in duplicate items for fact-checkers to triage).
   - **Abstention on `unverifiable` claims:** 52/52 (**100.0%**) deferred below critical auto-flag threshold for human verification.
6. **Robustness:** **27/30 (90.0%)** consistent triage decisions under simulated spelling typos. Average processing latency: **8.13 ms/claim**.
7. **Usability/accessibility:** Low-bandwidth vanilla HTML/CSS/JS Observer Console (`/`), semantic landmarks, `<dialog>` modal, `aria-live` status regions, plain-English labels, one-click public reply copy buttons.
8. **Failure cases:** Short ambiguous claims lacking explicit electoral keywords (e.g., *"I heard something is wrong with the new voting app"*) fall below automated threshold and intentionally abstain to human review.
9. **Reproducibility:**
   ```bash
   docker compose exec -T -e PYTHONPATH=/app api python scripts/evaluate.py
   ```
10. **Conclusion and next steps:** Sentinel-AI achieves strong precision and high cluster compression on synthetic Nigerian election claims while safely abstaining on ambiguous reports. Next steps before field pilot: human-annotated evaluation on Hausa, Yoruba, and Igbo field messages and live Gemini Vision testing on synthetic EC8A images.
