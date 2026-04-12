# RetroFit

Feeds an ad screenshot and a landing page URL into a pipeline of 6 AI agents that rewrite the hero section to match the ad — improving message match and conversion rate without touching the rest of the page.

**Live demo**: _coming soon_

---

## What it does

Most landing pages are generic. They exist before any specific ad campaign, so they can't reflect the exact offer, tone, or audience of a particular ad. That gap between what the ad promises and what the page delivers kills conversions.

RetroFit closes that gap automatically. Given a Meta/Google ad creative and the destination landing page:

1. Reads the ad — extracts the headline, offer, discount, CTA text, tone, and target audience
2. Scrapes the landing page — maps the hero section, CTAs, social proof, and trust elements
3. Scores the page — 7-criterion CRO audit against the specific ad
4. Writes new copy — replacement text grounded entirely in the ad and original page content
5. Patches the HTML — applies changes surgically via CSS selectors, never rewrites the full page
6. Validates the output — checks for broken structure, layout regression, and hallucinated claims

The result: a personalized variant of the page with an audit trail explaining every change.

---

## Architecture

```
Ad Image + Landing URL
        │
        ▼
┌──────────────────────────────────────────────────────┐
│                  LangGraph Pipeline                   │
│                                                       │
│  Ad Analyzer → Page Scraper → CRO Strategist         │
│                                    │                  │
│                               Copywriter              │
│                                    │                  │
│                           Code Modifier               │
│                                    │                  │
│                            QA Verifier ──► retry      │
└──────────────────────────────────────────────────────┘
        │
        ▼
Personalized page + CRO audit + before/after screenshots
```

| Agent | Model | Role |
|---|---|---|
| Ad Analyzer | Gemini 3 Flash | Vision extraction — reads ad image into structured JSON |
| Page Scraper | Firecrawl + Playwright | Scrapes HTML, screenshots, maps semantic elements |
| CRO Strategist | Gemini 3.1 Pro | Scores page on 7 CRO criteria, proposes changes |
| Copywriter | Gemini 3.1 Pro | Writes replacement copy for each change candidate |
| Code Modifier | BeautifulSoup (deterministic) | Applies PatchSpec to HTML — no LLM writes raw HTML |
| QA Verifier | Gemini 3 Flash | Validates output — structure, visual diff, hallucinations |

---

## How it's different

**LLMs don't write HTML here.** The copywriter outputs a `PatchSpec` — a JSON list of surgical operations (`replaceText`, `insertBefore`, `replaceStyle`). A deterministic function applies those to the DOM. This is what keeps outputs predictable and safe.

**Changes are grounded.** Every piece of new copy must be traceable to either the ad creative or the original page. The QA agent explicitly checks for hallucinated discount values, product names, or claims not present in the source material.

**Retry loop.** If QA fails, the pipeline loops back to the Code Modifier with the failure reasons and tries again, up to 2 retries.

---

## Tech stack

| Layer | Tech |
|---|---|
| Backend | FastAPI (Python 3.12) + uvicorn |
| Agent orchestration | LangGraph `StateGraph` |
| LLM | Gemini 3 Flash + Gemini 3.1 Pro via `google-genai` SDK |
| Web scraping | Firecrawl API + Playwright |
| HTML manipulation | BeautifulSoup 4 + lxml |
| Frontend | Next.js 15 (App Router) + TypeScript + Tailwind + shadcn/ui |
| Observability | LangSmith (optional) |
| Backend hosting | GCP Cloud Run |
| Frontend hosting | Vercel |

---

## Getting started

### Prerequisites

- Python 3.12+
- Node.js 20+
- [Firecrawl API key](https://firecrawl.dev) (free tier works)
- [Gemini API key](https://aistudio.google.com/) (free with GCP credits)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium

cp .env.example .env
# Fill in GEMINI_API_KEY and FIRECRAWL_API_KEY

uvicorn app.main:app --reload --port 8080
```

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
# Set NEXT_PUBLIC_API_URL=http://localhost:8080

npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

---

## Example output

Upload an ad → enter a landing page URL → watch the pipeline run → get:

- **Before/after screenshot comparison** with a drag slider
- **CRO scorecard** — 7 criteria scored 0–100 with before/after delta
- **Explanation panel** — every change listed with the CRO principle it addresses
- **HTML diff** — exact before/after text for each modified element
- **QA report** — structural checks, hallucination flags, visual diff score

---

## Guardrails

| Problem | How it's handled |
|---|---|
| Random/irrelevant changes | Only selectors from the SemanticMap are valid targets |
| Broken layout | QA fails if key elements disappear or visual diff > 50% |
| Hallucinated content | QA cross-checks all new text against ad + original page |
| LLM writing broken HTML | Code Modifier is fully deterministic — LLMs output JSON, not HTML |
| Stuck pipeline | Max 2 QA retries, then returns best-effort with warnings |

---

## Project structure

```
├── backend/
│   ├── app/
│   │   ├── agents/          # LangGraph agent nodes
│   │   ├── models/          # Pydantic data contracts
│   │   ├── prompts/         # System prompts
│   │   ├── routes/          # FastAPI routes
│   │   ├── storage/         # Artifact management
│   │   └── tools/           # Scraper, DOM mapper, HTML patcher
│   ├── tests/
│   └── Dockerfile
├── frontend/
│   └── src/
│       ├── app/             # Next.js pages
│       ├── components/      # UI components
│       ├── hooks/           # SSE, pipeline state
│       └── lib/             # API client, types
└── docs/
    ├── architecture.md
    ├── agent-prompts.md
    ├── cro-methodology.md
    └── api.md
```

---

## License

MIT
