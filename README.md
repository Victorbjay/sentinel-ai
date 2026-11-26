# Sentinel-AI

> **Real-Time Electoral Misinformation & Narrative Monitoring Engine**  
> *Developed for the **#AI4Elections Hackathon**·** Built by Sentinel AI Labs

---

## **What is Sentinel-AI?**

Sentinel-AI is an **election observer platform** that helps accredited fact-checkers spot emerging election misinformation, cluster related narratives, and verify claims against official INEC rules—all in real-time, with **no autonomous decisions**. Every finding is explained, every decision is audited, and every reviewer is in control.

### **For Judges: What Makes This Win?**
- 🌍 **Multilingual from day 1** (English, Pidgin, Hausa, Yoruba, Igbo)
- 🧠 **Semantic clustering** (vectors, not keyword matching)
- 📋 **Official integration** (Electoral Act 2022, INEC regulations)
- 👤 **Human-centered** (observers make final calls, not AI)
- 🔒 **Privacy by design** (NDPA 2023 compliant)
- 📱 **Low-bandwidth UI** (pure HTML, works on slow networks)

---

## 👥 Team
- **Victor Okpe** — Backend & Systems Lead
- **Jezreal Momoh** — AI & Software Engineering  
- **Joy Umofia** — Product & Design

---

## ⚡ Quick Start (2 minutes)

### Start the Platform
```bash
docker compose up -d --build
```

Open **http://localhost:8000** in your browser.

### Load Sample Data
Click the **"Test Platform"** button to load election-related rumors.

### Explore
1. **Left panel:** Submit rumors, search INEC rules, see trending narratives
2. **Right panel:** Review reports in queue
3. **Click any report:** See AI rationale, matched rules, multilingual replies, save your decision

**[→ Full Demo Guide](DEMO.md)**

---

## 🏛️ Problem & Solution

### The Problem
- Viral misinformation spreads faster than manual debunking
- By the time one claim is refuted, the narrative already shaped public perception
- Needs: **early detection**, **semantic clustering**, **verified fact-checking**, **observer transparency**

### Our Solution
**Sentinel-AI** provides:
1. **Early Narrative Clustering** — detects emerging disinformation trends
2. **Vector RAG Verification** — cross-references claims against official INEC regulations
3. **Multilingual Ingestion** — handles Nigerian languages natively
4. **Human-in-the-Loop** — no autonomous declarations; observers decide everything
5. **NDPA 2023 Compliance** — strict privacy protections

---

## 🏗️ Architecture

```
Claim Ingestion
    ↓ (clean, detect language)
Semantic Embedding (FastEmbed 384-dim)
    ↓ (cluster with pgvector)
Narrative Clustering (cosine similarity @0.52)
    ↓ (search against official facts)
Vector RAG Search (INEC rules)
    ↓ (calculate risk score)
Priority Triage
    ↓ (send to)
Human Review Queue (pending_human_review)
    ↓ (observer makes final call)
Immutable Audit Trail
```

### Data Model
- **`claims`** — Ingested posts with embeddings, language, risk_score, status
- **`narratives`** — Clustered narrative centroids with threat_level and velocity
- **`verified_facts`** — INEC regulations, Electoral Act 2022, multilingual FAQs with embeddings
- **`human_reviews`** — Immutable audit trail of observer decisions

### Tech Stack
- **Backend:** Python 3.11, FastAPI (async)
- **Database:** PostgreSQL 16 + pgvector
- **Embeddings:** FastEmbed (all-MiniLM-L6-v2, 384-dim ONNX)
- **NLP:** Multilingual preprocessor, risk scoring
- **Frontend:** Vanilla HTML/CSS/JS (zero dependencies, low-bandwidth)
- **Containerization:** Docker + Docker Compose

---

## 🛡️ Security & Compliance

| Feature | Implementation |
|---------|-----------------|
| **Privacy (NDPA 2023)** | URLs, emails, phone numbers, NIDs scrubbed; hashed reporter tags |
| **No Autonomous Declarations** | System never declares winners or fraud; observers always decide |
| **Explainability** | Every flag includes transparent rationale + matched rules |
| **Auditability** | Complete timestamped trail of all decisions |
| **Reviewer Auth** | X-Reviewer-Key header + access control |
| **No Live System Access** | Isolated from INEC BVAS/IReV/voter register infrastructure |

---

## 📊 Key Features

### 1. Real-Time Monitoring Dashboard
- **KPI Cards:** Reports checked, pending review, trending narratives, urgent alerts
- **Low-bandwidth design:** Works on slow connections

### 2. Multilingual Claim Ingestion
- Paste text from WhatsApp, Twitter, Facebook, Telegram, blogs
- Auto-detects: English, Pidgin, Hausa, Yoruba, Igbo
- Cleans and normalizes text
- Generates semantic embedding
- Calculates risk score
- Groups with related narratives

### 3. Semantic Narrative Clustering
- Vectors, not keywords (catches variants like "BVAS spoil" = "BVAS broken")
- Real-time velocity and volume tracking
- Click to filter reports by narrative theme

### 4. Vector RAG: Search Official INEC Facts
- Query: "BVAS", "IReV", "2:30 PM", "PVC", etc.
- Returns: Matched Electoral Act sections + regulations + FAQs
- Confidence score for each match

### 5. Election Media Screening
- Upload screenshots and flyers
- EXIF metadata extraction
- Vision-based content analysis
- Verification checklist generation

### 6. Human-in-the-Loop Review Workflow
- **For each report:** See AI reasoning, matched rules, risk metrics
- **Ready-to-share replies:** Fact-checks in 5 languages, copy buttons
- **Make a decision:** False / Misleading / True / Unsure
- **Audit trail:** All decisions timestamped with rationale

---

## 🎯 Example Workflows

### Scenario 1: BVAS Machine Rumor (Pidgin)
```
📝 Input: "Dem say BVAS don spoil for PU 014 Eti-Osa, make una go house!"

✅ Detected: Pidgin
⚠️ Risk Score: 65% (plausible technical claim)
📋 Matched Rule: "BVAS Accreditation" (Electoral Act 2022, Section 47)
  → "BVAS machines are programmed with read-only firmware deployed before election..."

💬 Ready-to-Share Reply (Pidgin):
  "BVAS don secure well-well. Dem program am before election with protections..."

👤 Observer Decides:
  → ❌ Debunk (or mark as Misleading/Verify)
  → "BVAS tested before each election; backup procedures exist per Regulation 15"
  → Decision saved to audit trail
```

### Scenario 2: Queue Cutoff Misinformation (Hausa)
```
📝 Input: "Jami'an zabe sun rufe akwati tun karfe 2:30 duk da mutane suna layi."
   (Election officials close the box at 2:30 even though people are still in line)

✅ Detected: Hausa
⚠️ Risk Score: 45% (partially accurate—needs nuance)
📋 Matched Rule: "Voting Hours & Queue" (Regulation 32)
  → "Any voter present in queue at 2:30 PM must be allowed to vote until last person in line has voted."

👤 Observer Decides:
  → ⚠️ Misleading (the claim omits that queue voters still vote)
  → "Per Regulation 32, voters in queue at 2:30 PM must vote. Poll officials cannot lock box until all queue voters cast votes."
```

---

## 🚀 Deployment

### **Docker (Recommended)**
```bash
docker compose up -d --build
```

### **Local (Development)**
```bash
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### **Environment Variables** (`.env`)
```env
DATABASE_URL=postgresql+asyncpg://sentinel:sentinel_secure_pass@db:5432/sentinel_db
REVIEWER_API_KEY=sentinel-observer-2026
GEMINI_API_KEY=your-key-here  # Optional for media vision
ENVIRONMENT=production
DEBUG=False
```

### **API Endpoints**
- `POST /api/v1/claims/` — Ingest a claim
- `GET /api/v1/claims/stats` — Dashboard metrics
- `GET /api/v1/narratives/` — List trending narratives
- `POST /api/v1/facts/search` — Vector search INEC rules
- `POST /api/v1/reviews/` — Save reviewer decision
- `POST /api/v1/simulate/run` — Load demo data
- `GET /docs` — Swagger UI

---

## 📚 Documentation

- **[DEMO.md](DEMO.md)** — Interactive walkthrough for judges (5 min)
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** — Technical deep-dive
- **[Swagger UI](http://localhost:8000/docs)** — Live API docs (after `docker compose up`)

---

## 🏆 Why Sentinel-AI Wins

| Criterion | What We Built |
|-----------|----------------|
| **Addresses Brief** | Real-time misinformation detection + human-verified fact-checking |
| **Multilingual** | 5 Nigerian languages natively (not English-only) |
| **Vector AI** | Semantic clustering catches narrative variants |
| **Official Integration** | Every claim cross-referenced against Electoral Act 2022 + INEC guidelines |
| **Responsible AI** | No autonomous decisions; observers always in control |
| **Privacy** | NDPA 2023 compliant; no personal data stored |
| **Accessible** | Low-bandwidth UI; works on slow networks |
| **Production-Ready** | Docker deployment, audit trails, error handling |

---

## 📄 License

Apache 2.0 — Built for the #AI4Elections Hackathon

---

## 🙏 Acknowledgments

- **Rise Networks** — Hackathon host
- **INEC** — Electoral Act 2022, Regulations, official datasets
- **Community** — Multilingual FAQ and misinformation examples

---

**Questions?** See [DEMO.md](DEMO.md) or check the [API Docs](http://localhost:8000/docs)
