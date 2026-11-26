# Sentinel-AI Demo Guide

## Quick Start (2 minutes)

### 1. Start the Platform
```bash
docker compose up -d --build
```

The system will be ready at **http://localhost:8000**

### 2. Load Sample Data
Once the page loads, click **"Test Platform"** button in the header to load real election-related rumors.

### 3. Explore the Dashboard

#### **Key Metrics (top)**
- **Reports Checked:** Total claims processed
- **Pending Review:** Reports awaiting fact-checker decisions
- **Trending Narratives:** Clustered discussion themes detected
- **Urgent Alerts:** High-threat narratives flagged for action

---

## Platform Features Tour

### **Left Panel: Claim Ingestion & Search**

#### 1️⃣ Check a Post or Rumor
- Paste any election-related text (WhatsApp, Twitter, Facebook, etc.)
- Supports: English, Pidgin, Hausa, Yoruba, Igbo
- Try a sample by clicking the sample chips
- **What happens:** 
  - Text is cleaned and language-detected
  - Semantic embedding generated (384-dim vector)
  - Matched against INEC official rules
  - Grouped with similar narratives or creates new trend
  - Risk score calculated (0-100%)
  - Assigned to human review queue

#### 2️⃣ Screen Election Media
- Upload a screenshot or election flyer
- Extracts EXIF metadata
- Performs content analysis (Gemini Vision)
- Generates verification checklist

#### 3️⃣ Search Official INEC Facts
- Query the vector-embedded INEC rules database
- E.g., search: "BVAS", "IReV", "2:30 PM", "PVC"
- Shows % match score for each rule
- Lists official source (Electoral Act 2022, Regulations, etc.)

#### 4️⃣ Trending Narratives
- Real-time clusters of similar election rumors
- Shows threat level (critical/high/medium/low)
- Click any to filter the queue by that narrative
- Displays velocity (reports/hour) and volume

### **Right Panel: Reports Waiting for Review**

#### Filter & Sort
- **Sort By:** Riskiest first (default) or Most Recent
- **Status Filter:** All, Needs Review, Debunked, Verified, Misleading

#### Claim Card Shows
- **Status badge:** Pending Review, Debunked, Verified, etc.
- **Language & Platform:** How/where it came from
- **Media indicator:** 📷 if image attached
- **Risk Score:** Priority percentage
- **Review Button:** Opens detailed analysis

---

## Fact-Checker Review Workflow

### Open a Report
Click **"Review & Decide"** on any claim card in the queue.

### Analysis Modal Shows
1. **What was reported:** The original text
2. **Why flagged:** AI-generated rationale (confidence %)
3. **Official INEC Rules Found:** 
   - Matched facts from regulatory database
   - Similarity score for each match
   - Full rule text and official source
4. **Ready-to-Share Replies:**
   - Fact-check responses in multiple languages
   - Copy buttons for direct posting

### Save Your Decision
1. Enter your name
2. Choose verdict:
   - ❌ **False Rumor** – completely debunked
   - ⚠️ **Misleading** – half-true, lacks context
   - ✅ **Confirmed True** – verified as accurate
   - ❓ **Not Sure Yet** – needs more info
3. Enter observer API key: `sentinel-observer-2026` (default demo)
4. Brief rationale (reference INEC rules or field checks)
5. Click **"Save Decision"** → stored in audit trail

### Audit Trail
Past decisions persist on each claim with reviewer name, verdict, and rationale.

---

## Technical Architecture

### Data Flow
```
Claim Ingestion
    ↓
Multilingual Cleaning (Pidgin/Hausa/Yoruba/Igbo Lexicon)
    ↓
Semantic Embedding (FastEmbed 384-dim)
    ↓
Narrative Clustering (pgvector cosine similarity @0.52 threshold)
    ↓
Vector RAG Search (match against INEC facts)
    ↓
Risk Scoring (content + spread + media signals)
    ↓
Human-in-the-Loop Review Gate (pending_human_review)
    ↓
Fact-Checker Decision (audit trail immutable)
```

### Security & Compliance
- **NDPA 2023:** PII scrubbing before database persistence
- **No Autonomous Decisions:** System never declares winners or fraud
- **Explainability:** Every flag includes transparency rationale
- **Reviewer Auth:** X-Reviewer-Key header + audit logging
- **Confidence-based Abstention:** Low-confidence claims flagged for manual check

### Technology Stack
- **Backend:** FastAPI (Python 3.11+)
- **Database:** PostgreSQL 16 + pgvector extension
- **Embeddings:** FastEmbed (all-MiniLM-L6-v2, 384-dim ONNX)
- **NLP:** Multilingual text cleaning + risk scoring
- **Frontend:** Vanilla HTML/CSS/JS (zero dependencies, low-bandwidth)
- **Containerization:** Docker + Docker Compose
- **LLM Integration:** Optional Gemini Vision for media analysis

---

## Example Scenarios

### Scenario 1: BVAS Machine Rumor
**Input:** "Dem say BVAS don spoil for PU 014 Eti-Osa, make una go house!"
- **Detected Language:** Pidgin
- **Risk Score:** 65% (plausible technical claim)
- **Matched Rule:** "BVAS Accreditation" (Section 47, Electoral Act)
- **Suggested Reply:** [Ready-to-share fact-check in Pidgin]

### Scenario 2: Queue Cutoff Misinformation
**Input:** "Jami'an zabe sun rufe akwati tun karfe 2:30 duk da mutane suna layi."
- **Detected Language:** Hausa
- **Risk Score:** 45% (partially accurate—voters in queue get to vote after 2:30)
- **Matched Rule:** "Voting Hours & Queue" (Regulation 32)
- **Verdict Options:** Misleading (voters in queue still vote) or Confirm True (depends on framing)

### Scenario 3: IReV Portal Rumor
**Input:** "IReV portal is down so polling unit Form EC8A results are invalid."
- **Detected Language:** English
- **Risk Score:** 72% (threatens legitimacy)
- **Matched Rule:** "IReV Portal" + "Result Transmission" (Section 60, Electoral Act)
- **Analysis:** False—IReV is 24/7 public portal; results legality depends on physical EC8A forms, not portal uptime

---

## For Hackathon Judges

### Key Differentiators
1. **Multilingual from Day 1:** 5 Nigerian languages, not just English
2. **Vector Semantics:** Clusters related narratives; won't miss variants ("BVAS spoil" = "BVAS broken")
3. **Official Integration:** Every flag cross-references Electoral Act 2022 and INEC regulations
4. **Low-Bandwidth Ready:** Pure HTML frontend works on slow connections
5. **Explainability:** Every decision shows the why (rule matched, confidence, source)
6. **Human-Centric:** No autonomous declarations; reviewers have full audit trail and decision history
7. **NDPA Compliant:** Privacy by design—no personal data stored

### Winning Vision
Sentinel-AI enables accredited election observers to **spot misinformation trends early**, **cross-reference claims against official rules**, and **make confident, well-documented decisions**—all while protecting voter privacy and respecting the finality of human review.

---

## API Endpoints (Developer Reference)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/api/v1/claims/` | Ingest a claim |
| `GET` | `/api/v1/claims/stats` | Dashboard KPIs |
| `GET` | `/api/v1/narratives/` | List trending narratives |
| `POST` | `/api/v1/facts/search` | Vector search INEC rules |
| `POST` | `/api/v1/reviews/` | Save reviewer decision |
| `POST` | `/api/v1/simulate/run` | Load demo data |
| `POST` | `/api/v1/simulate/reset` | Clear demo data |
| `GET` | `/docs` | Swagger UI (FastAPI auto-docs) |

---

## Troubleshooting

**Q: Dashboard won't load?**  
A: Check Docker containers: `docker ps | grep sentinel`. Ensure port 8000 is not in use.

**Q: "Database connection error"?**  
A: Wait for PostgreSQL healthcheck. First startup takes ~30 seconds. Check logs: `docker logs sentinel_api`

**Q: "GEMINI_API_KEY not set"?**  
A: Media screening falls back to basic EXIF. Vision analysis is optional. Set `GEMINI_API_KEY` in `.env` to enable.

**Q: Can I deploy to production?**  
A: See `docs/ARCHITECTURE.md` for security hardening. This is a **hackathon demo**—not for live election monitoring without auditing.

---

## Next Steps for Real-World Use

1. **Extend Seed Data:** Add more verified INEC facts and multilingual FAQs
2. **Integrate Live Feeds:** Connect to Twitter API, WhatsApp Business API, etc.
3. **Custom Thresholds:** Tune confidence and clustering thresholds per region
4. **Mobile App:** Wrap the frontend for accredited observer app distribution
5. **Multi-Team Collaboration:** Add observer team management and review assignments
6. **Real-Time Alerts:** WebSocket notifications for high-threat narratives
7. **Audit Export:** Generate reviewer decision reports for INEC records

---

**Built for #AI4Elections Hackathon**  
Victor Okpe · Jezreal Momoh · Joy Umofia  
Privacy-Safe (NDPA 2023) · Transparent · Human-Centered
