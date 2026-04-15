<div align="center">

# RetroFit

### AI-Powered Ad → Landing Page Personalization Engine

**Close the gap between what your ad promises and what your page delivers.**

[![Live Demo](https://img.shields.io/badge/Live_Demo-Visit_Now-000000?style=for-the-badge&logo=google-cloud&logoColor=white)](https://retrofit-frontend-411746695116.asia-south1.run.app)
[![API Docs](https://img.shields.io/badge/API_Docs-Swagger-85EA2D?style=for-the-badge&logo=swagger&logoColor=black)](https://retrofit-backend-411746695116.asia-south1.run.app/docs)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)]()
[![Next.js](https://img.shields.io/badge/Next.js-16-000000?style=flat-square&logo=next.js&logoColor=white)]()
[![GCP](https://img.shields.io/badge/GCP-Cloud_Run-4285F4?style=flat-square&logo=google-cloud&logoColor=white)]()

</div>

---

## The Problem

Most landing pages are generic. They exist before any specific ad campaign, so they can't reflect the offer, tone, or urgency of a particular ad. That gap between what the ad promises and what the page delivers kills conversions.

**RetroFit closes that gap automatically.** Give it an ad creative and a landing page URL — it surgically rewrites the hero section to match the ad, improving message match and conversion rate without touching the rest of the page.

> **Key constraint:** The output is the _existing page enhanced_ — not a new page. Every modification is a targeted CSS-selector operation on the real DOM, preserving the site's design, scripts, and structure.

---

## How It Works

```
                    ┌── Ad Analyzer (Flash) ──┐
 User Input ───────┤                          ├──► CRO Strategist (Pro)
 (Ad + URL)        └── Page Scraper ──────────┘          │
                                                    Copywriter (Pro)
                                                         │
                                                  Code Modifier (deterministic)
                                                         │
                                                    QA Verifier (Flash)
                                                      │       │
                                                    PASS    FAIL → retry (up to 2×)
                                                      │
                                                  ✅ Personalized Page
                                                  + CRO Audit
                                                  + Before/After Screenshots
                                                  + Change Explanations
```

**6 specialized agents**, not a single prompt. Each does one thing well:

| Agent | Model | Thinking | What It Does |
|---|---|---|---|
| **Ad Analyzer** | Gemini 3 Flash | `low` | Vision — reads the ad image into structured JSON (headline, offer, discount, CTA, colors, tone) |
| **Page Scraper** | Firecrawl + Playwright | — | Scrapes full HTML, takes screenshot, builds a semantic map of hero, CTAs, social proof elements |
| **CRO Strategist** | Gemini 3.1 Pro | `high` | Scores the page on 7 weighted CRO criteria against the ad, proposes prioritized changes |
| **Copywriter** | Gemini 3.1 Pro | `high` | Generates replacement copy for each change candidate → outputs a structured PatchSpec (JSON) |
| **Code Modifier** | BeautifulSoup | — | **Deterministic.** Applies the PatchSpec to the real DOM via CSS selectors. No LLM writes raw HTML. |
| **QA Verifier** | Gemini 3 Flash | `high` | 5-layer validation: structural, key elements, rule-based hallucination, LLM cross-check, visual diff |

### Parallel Execution

Ad Analyzer and Page Scraper run **in parallel** (LangGraph fan-out/fan-in). The CRO Strategist waits for both, then the rest runs sequentially. This saves ~10-15 seconds per run.

---

## CRO Scoring — 7 Criteria

Every page is scored before and after modification:

| Criterion | Weight | What It Measures |
|---|---|---|
| **Message Match** | 25% | Does the hero copy match the ad's specific offer? |
| **Hero Clarity** | 20% | Is the value proposition clear above the fold? |
| **CTA Visibility** | 20% | Is the primary CTA prominent and action-oriented? |
| **Social Proof** | 15% | Are trust signals present and well-placed? |
| **Urgency/Scarcity** | 10% | Are urgency cues from the ad restated on the page? |
| **Trust Signals** | 5% | Are secure checkout/guarantee badges near the CTA? |
| **Mobile Readiness** | 5% | Is the layout responsive? |

---

## Guardrails

The assignment asked: _"How do you handle random changes, broken UI, hallucinations, and inconsistent outputs?"_

| Problem | Solution |
|---|---|
| **Random changes** | Only selectors from the SemanticMap are valid targets. Every change must reference a CRO criterion. The LLM cannot invent selectors. |
| **Broken UI** | Inserted HTML is sanitized (absolute/fixed positioning stripped). QA checks structural integrity + visual diff. Failed? Auto-retry with error context. |
| **Hallucinations** | Rule-based check + Gemini Flash cross-references all new text against ad + original page. Invented discounts, product names, or claims = QA failure. |
| **Inconsistent outputs** | Every LLM call uses `response_mime_type: "application/json"`. Pydantic models enforce schema at every stage boundary. DOM patching is deterministic. |

### The Key Design Decision

**LLMs output JSON instructions, not HTML.** The Copywriter produces a `PatchSpec` — a list of operations like `replaceText("h1.hero__title", "40% Off Summer Skincare")`. A deterministic BeautifulSoup function applies them. This separates _intent_ (LLM) from _execution_ (code) and eliminates an entire class of formatting, syntax, and layout bugs.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | FastAPI (Python 3.12) + uvicorn (2 workers) |
| **Agent Orchestration** | LangGraph `StateGraph` with parallel fan-out + conditional retry |
| **Primary LLM** | Gemini 3.1 Pro (`gemini-3.1-pro-preview`) — strategy + copywriting |
| **Vision LLM** | Gemini 3 Flash (`gemini-3-flash-preview`) — ad analysis + QA |
| **LLM SDK** | `google-genai` (direct SDK, not LangChain wrappers) |
| **Web Scraping** | Firecrawl API + Playwright (Chromium) |
| **HTML Manipulation** | BeautifulSoup 4 + lxml |
| **Frontend** | Next.js 16 (App Router) + TypeScript + Tailwind CSS 4 |
| **Streaming** | Server-Sent Events (SSE) — real-time pipeline progress |
| **Hosting** | GCP Cloud Run (asia-south1) — zero cold start (`min-instances=1`) |
| **Artifact Storage** | Google Cloud Storage |
| **Observability** | LangSmith (optional) |

---

## Live URLs

| Service | URL |
|---|---|
| 🌐 **Frontend** | https://retrofit-frontend-411746695116.asia-south1.run.app |
| ⚡ **Backend API** | https://retrofit-backend-411746695116.asia-south1.run.app |
| 📄 **API Docs** | https://retrofit-backend-411746695116.asia-south1.run.app/docs |

Both services run with `min-instances=1` — always warm, zero cold start latency.

---

## Run Locally

### Prerequisites

- Python 3.12+, Node.js 20+
- [Gemini API key](https://aistudio.google.com/) (free)
- [Firecrawl API key](https://firecrawl.dev) (free tier)

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# Create .env from the template
cp .env.example .env
# Fill in: GEMINI_API_KEY, FIRECRAWL_API_KEY

uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

---

## What You Get

Upload an ad → enter a landing page URL → watch the 6-stage pipeline execute in real time → receive:

- **Personalized page** — live HTML preview in iframe, fully interactive
- **Before/after comparison** — screenshot slider for pixel-level visual diff
- **CRO scorecard** — 7 criteria scored 0–100 with before/after delta
- **Explanation panel** — every change listed with the CRO principle it addresses
- **HTML diff** — exact before/after text for each modified element
- **QA report** — structural integrity, hallucination flags, visual diff results

---

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── agents/          # LangGraph nodes (6 agents + graph definition)
│   │   ├── models/          # Pydantic data contracts (AdContext, PatchSpec, etc.)
│   │   ├── prompts/         # System prompts for each agent
│   │   ├── routes/          # FastAPI routes (runs, preview, health)
│   │   ├── storage/         # Local + GCS artifact management
│   │   └── tools/           # DOM mapper, HTML patcher, scraper
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js pages (home, run/[id])
│   │   ├── components/      # Pipeline timeline, CRO scorecard, before/after slider
│   │   ├── hooks/           # useSSE (real-time streaming)
│   │   └── lib/             # API client, TypeScript types
│   ├── Dockerfile
│   └── cloudbuild.yaml
└── Docs/                    # Architecture, CRO methodology, research
```

---

## Deployment

Both services deploy to GCP Cloud Run via Cloud Build:

```bash
# Backend
cd backend
gcloud builds submit --tag asia-south1-docker.pkg.dev/PROJECT/retrofit/backend --region=asia-south1
gcloud run deploy retrofit-backend --image=... --memory=2Gi --cpu=2 --min-instances=1

# Frontend
cd frontend
gcloud builds submit --config=cloudbuild.yaml --region=asia-south1 \
  --substitutions="_BACKEND_URL=https://YOUR-BACKEND.run.app,_IMAGE=.../frontend"
gcloud run deploy retrofit-frontend --image=... --memory=512Mi --cpu=1 --min-instances=1
```

---

<div align="center">

Built for the [Troopod](https://troopod.io) AI PM assignment.

</div>
