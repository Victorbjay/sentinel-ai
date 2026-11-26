# Problem Statement: Sentinel-AI

- **Track:** Track 1 — AI and Trustworthy Electoral Information (#AI4Elections Hackathon)
- **Team:** Sentinel AI Labs (Victor Okpe, Jezreal Momoh, Joy Umofia)

## Target Users
1. **Accredited Fact-Checkers & Election Situation Rooms** (e.g., INEC information desks, Yiaga Africa, Dubawa, CDD) overwhelmed by duplicate viral rumors on election day.
2. **Field Observers & CSOs** needing fast, plain-language verification grounded in the Electoral Act 2022 and INEC Regulations.
3. **Nigerian Voters** across English, Nigerian Pidgin, Hausa, Yoruba, and Igbo who need timely, accessible clarifications before voter-suppression rumors spread.

## Core Pain Point
On election day, a single false narrative (e.g., *"BVAS is broken at PU 014, go home"* or *"IReV failure invalidates polling unit results"*) mutates into hundreds of posts across WhatsApp, X, Facebook, and Telegram in multiple Nigerian languages. Manual, single-claim fact-checking is too slow: by the time one post is debunked in English, the underlying narrative has already caused voter panic or suppression.

## Sentinel-AI Solution
Sentinel-AI triages incoming public/synthetic reports by harm and viral spread, clusters semantically similar rumors in real time via `pgvector`, cross-references them against official INEC rules, drafts multilingual clarifications, and enforces strict human-in-the-loop review before any alert is approved.
