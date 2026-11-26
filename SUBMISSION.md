# Sentinel-AI — Hackathon Submission

**Team:** Sentinel AI Labs  
**Track:** Track 1 — AI and Trustworthy Electoral Information  
**Project:** Real-Time Electoral Misinformation & Narrative Monitoring Engine  

---

## 🚀 Executive Summary

Sentinel-AI is a **complete, production-ready platform** for accredited election observers to detect election misinformation in real-time, cluster narratives, verify claims against official INEC rules, and make confident, auditable decisions.

### What You Can Do Right Now

```bash
docker compose up -d --build
```

Then visit **http://localhost:8000** and click **"Test Platform"** to load sample election rumors.

**Time to see it working: 2 minutes**

---

## ✨ Why We Win

### 1. **Multilingual from Day 1**
- English, Pidgin, Hausa, Yoruba, Igbo
- Not an afterthought; built into the core pipeline
- Auto-detects language on ingestion
- Generates ready-to-share replies in all 5 languages

### 2. **Vector Semantics, Not Keywords**
- Clusters "BVAS spoil" = "BVAS broken" = "BVAS don fail"
- Catches narrative variants that keyword systems miss
- pgvector cosine similarity at 0.52 threshold
- 384-dimensional FastEmbed ONNX model (runs locally, no API calls)

### 3. **Official INEC Integration**
- Every claim cross-referenced against:
  - Electoral Act 2022 (complete text)
  - INEC Regulations & Guidelines
  - Multilingual voter FAQs
- Shows % match confidence for each related rule
- Provides authoritative source citation

### 4. **Human-Centric Design**
- **No autonomous declarations** — system never declares winners or fraud
- Observers make all final decisions
- Complete audit trail with timestamps and rationale
- Decision history visible for transparency
- Observer access control (X-Reviewer-Key)

### 5. **Privacy & Compliance**
- NDPA 2023 compliant from the ground up
- Scrubs URLs, emails, phone numbers, NIDs before storage
- Hashes reporter tags (blake2b)
- Never accesses INEC BVAS/IReV/voter register
- Only processes public social signals

### 6. **Low-Bandwidth Accessible**
- Vanilla HTML/CSS/JS (zero heavy frameworks)
- Works on slow connections (critical for field observers)
- No external CDNs or cloud dependencies
- Responsive design for phone/tablet/desktop

### 7. **Production-Ready**
- Docker deployment included
- Async FastAPI (scales horizontally)
- PostgreSQL 16 with pgvector (proven architecture)
- Comprehensive error handling
- Sample data included for demo

---

## 📊 Platform Overview

### **Dashboard**
Real-time KPIs:
- Reports checked
- Pending human review
- Trending narratives detected
- Urgent alerts flagged

### **Left Panel: Ingestion & Search**
1. **Check a Post or Rumor** — Paste any election-related text
2. **Screen Election Media** — Upload screenshots, analyze EXIF + vision
3. **Search Official INEC Facts** — Query "BVAS", "IReV", "2:30 PM", etc.
4. **Trending Narratives** — See what's going viral; click to filter queue

### **Right Panel: Review Queue**
- Filter by status (Needs Review, Debunked, Verified, Misleading)
- Sort by risk or recency
- Each report shows:
  - Risk score
  - Language & platform source
  - Media indicator
  - Review button

### **Review Workflow**
Click "Review & Decide" on any report:
1. **AI Analysis** — Flagging rationale, confidence score
2. **Official Rules** — Matched INEC regulations with % relevance
3. **Multilingual Replies** — Copy-paste fact-checks in 5 languages
4. **Your Decision** — Save verdict + brief rationale
5. **Audit Trail** — All past decisions logged

---

## 🛠️ Technical Highlights

| Component | Implementation | Why It Works |
|-----------|-----------------|--------------|
| **Backend** | FastAPI + asyncpg | Handles 1000s of concurrent requests |
| **Database** | PostgreSQL 16 + pgvector | Native vector similarity; proven scale |
| **Embeddings** | FastEmbed (ONNX) | Runs on-premise; no API latency |
| **NLP** | Multilingual preprocessor | Handles Nigerian language lexicons |
| **Frontend** | Pure HTML/CSS/JS | Low-bandwidth; instant load |
| **Containerization** | Docker Compose | One-command deployment |
| **Security** | X-Reviewer-Key auth + audit logs | Access control + accountability |

### Data Model
```
claims → (embedding, language, risk_score, status)
narratives → (centroid_embedding, volume, velocity, threat_level)
verified_facts → (embedding, topic, official_text, source)
human_reviews → (claim_id, verdict, reviewer, rationale, timestamp)
```

---

## 📈 Real Demo Data

The platform ships with **7 multilingual sample rumors**:
- Pidgin: "Dem say BVAS don spoil for PU 014"
- English: "IReV portal is down so results are invalid"
- Hausa: "Jami'an zabe sun rufe akwati tun karfe 2:30"
- Yoruba: "Awon oludije ti kede ara won..."
- Igbo: "Ndi omempako kwuputa na ha meriri..."

Each demonstrates:
- Language detection
- Risk scoring
- Vector embedding
- Narrative clustering
- INEC rule matching
- Multilingual reply generation

---

## 🏆 Differentiators vs. Generic AI Tools

| Generic AI Tool | Sentinel-AI |
|---|---|
| English-only | 5 Nigerian languages |
| Keyword matching | Semantic vectors (pgvector) |
| Generic LLM responses | Official INEC regulations cited |
| Autonomous declarations | Human observer decides everything |
| Privacy concerns | NDPA 2023 compliant from day 1 |
| Requires cloud APIs | Runs fully on-premise |
| Complex setup | Docker Compose, 2-minute start |

---

## 📋 Deliverables Checklist

✅ **Code**
- Complete FastAPI backend (async, production-ready)
- Multilingual NLP pipeline
- Vector embedding & clustering (pgvector)
- Human-in-the-loop review system
- Audit logging & access control

✅ **Data**
- INEC verified facts database (seeds/inec_verified_facts.json)
- Multilingual voter FAQs (official/voter_info_faq_multilingual.csv)
- Synthetic test dataset (official/misinformation_claims_synthetic.jsonl)

✅ **Frontend**
- Professional, modern UI (redesigned for hackathon)
- Responsive design (mobile/tablet/desktop)
- Low-bandwidth compatible
- Accessibility-compliant (ARIA labels, keyboard navigation)

✅ **Documentation**
- README.md — Overview & quick start
- DEMO.md — Interactive walkthrough for judges
- docs/ARCHITECTURE.md — Technical deep-dive
- API Swagger UI (auto-generated)
- Inline code comments

✅ **Deployment**
- Docker + Docker Compose configuration
- .env.example with all required variables
- Healthcheck endpoints
- Database initialization scripts

✅ **Testing**
- Sample data loader (seed_db.py)
- Evaluation script (evaluate.py)
- End-to-end workflow verified

---

## 🎯 Why This Matters

**Problem:** Viral election misinformation spreads faster than manual fact-checking can respond. By the time one claim is debunked, the narrative has already influenced public confidence in elections.

**Solution:** Sentinel-AI enables:
- **Early Detection** — Spot emerging narratives before they go viral
- **Fast Verification** — Cross-reference against official rules instantly
- **Observer Empowerment** — Give field teams AI assistance + full decision control
- **Transparency** — Every decision audited, every rule cited, every reasoning explained
- **Accessibility** — Works on slow connections in remote polling units

**Impact:** Accredited election observers can focus on what matters—making informed, well-documented decisions—instead of manually searching regulations or worrying about privacy compliance.

---

## 🚀 For Judges

### 1. See It Working (2 min)
```bash
docker compose up -d --build
# Wait for "✅ All Tests Passed"
# Open http://localhost:8000
# Click "Test Platform"
```

### 2. Explore Key Workflows
- Submit a Pidgin rumor about BVAS
- Search "IReV" in the official facts
- Click a trending narrative to filter
- Review a report and save a decision

### 3. Check the Code
- Backend: `app/services/` — NLP, embeddings, clustering, RAG, explainability
- Frontend: `app/static/index.html` — Modern UI design system
- Models: `app/models/` — Data schemas with validation
- Database: Inspect with `psql localhost:5432 -U sentinel -d sentinel_db`

### 4. Read the Docs
- **Quick:** [DEMO.md](DEMO.md) — 5 min walkthrough
- **Deep:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — System design
- **API:** [http://localhost:8000/docs](http://localhost:8000/docs) — Swagger UI

---

## 📞 Support

**Questions during presentation?**
- System running but dashboard won't load? Check `docker logs sentinel_api`
- API errors? See Swagger UI error messages
- Want to test with custom data? See DEMO.md → "API Endpoints"

**Live Demo Notes:**
- Sample data is pre-loaded
- Clicking "Reset & Start Fresh" clears demo data (but keeps INEC rules)
- Observer key for decisions: `sentinel-observer-2026`
- API rate-limited only by PostgreSQL connections

---

## 🏁 Summary

**Sentinel-AI is a complete, winning solution because:**

1. ✅ Addresses the exact problem (election misinformation at scale)
2. ✅ Multilingual (5 Nigerian languages)
3. ✅ Technically sound (vectors, RAG, clustering)
4. ✅ Responsible AI (humans decide, not AI)
5. ✅ Compliant (NDPA 2023, Electoral Act)
6. ✅ Accessible (low-bandwidth, works in field)
7. ✅ Production-ready (Docker, logging, audit trails)
8. ✅ Demonstration-ready (sample data, modern UI, demo guide)

**You can see it working in 2 minutes. You can understand it in 10 minutes. You can deploy it in 1 minute.**

---

**Built for #AI4Elections**  
Victor Okpe · Jezreal Momoh · Joy Umofia  
🇳🇬 Enabling Transparent, Secure, Multilingual Election Monitoring
