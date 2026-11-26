# Safety, Privacy and Limitations Statement

## 1. Compliance with hackathon rules
- [x] No live/institutional system accessed or tested
- [x] Only synthetic, public or authorised data
- [x] Nonpartisan; no persuasion or microtargeting
- [x] Human oversight for consequential decisions

## 2. Risk register
| Risk | Who could be harmed | Likelihood | Impact | Mitigation | Residual |
|---|---|---|---|---|---|
| False positive (legitimate report flagged) | Citizens / observers | Medium | Medium | Mandatory `pending_human_review` gate; no auto-blocking or public labeling | Low |
| False negative (missed rumor) | Voters (suppression/panic) | Medium | High | Multilingual lexical rules + semantic clustering + priority triage | Medium |
| Bias against language/group | Hausa/Yoruba/Igbo/Pidgin speakers | Medium | Medium | Diacritic-aware detection + 5-language clarification templates + per-language eval | Medium |
| Privacy breach / re-identification | Reporters / social users | Low | High | Automatic regex redaction of emails/phones/NINs/`@handles` + `blake2b` pseudonymization | Low |
| Misuse by bad actors | Candidates / voters | Low | High | No partisan scoring, no result declaration, immutable `HumanReviewAudit` log | Low |
| Adversarial manipulation | Fact-checkers | Medium | Medium | Typo/acronym normalization + `min_similarity` RAG threshold + abstention | Medium |
| Over-reliance by users | Situation room staff | Medium | High | Prominent Safety Notice + `should_abstain` badge + mandatory human verdict form | Low |

## 3. Privacy and data protection
No personal voter data is collected. Incoming text is scrubbed for URLs, emails, `@mentions`, Nigerian phone numbers, and 11-digit IDs/NINs prior to persistence. Reporter tags containing emails or phone digits are hashed via `blake2b`.

## 4. Known limitations
- `all-MiniLM-L6-v2` embeddings are English-centric; cross-lingual semantic clustering for pure Hausa/Yoruba/Igbo without shared acronyms is limited without a multilingual embedding model or Gemini API translation.
- Image screening (`POST /api/v1/claims/screen-media`) inspects metadata and guides human verification; it does not perform cryptographic C2PA or forensic pixel-level deepfake detection.

## 5. Conditions for further testing
Before any field pilot: independent security audit, reviewer authentication/RBAC on `POST /api/v1/reviews/`, expanded human-annotated Hausa/Yoruba/Igbo test sets, and formal INEC/CSO partner sign-off.

## 6. Statement
"This prototype is not approved for operational electoral deployment." Signed: Victor Okpe (Sentinel AI Labs), 2026-11-26.
