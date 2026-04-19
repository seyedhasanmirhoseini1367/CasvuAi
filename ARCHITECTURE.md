# CasvuAI — Autonomous Content Generation Pipeline

## What This System Does

CasvuAI is an autonomous pipeline that produces **GEO-optimized, brand-aligned, multilingual marketing content** for SME clients. The client provides their data and a content goal. The system handles everything — from brand analysis to publication-ready output in multiple languages.

---

## The Core Problem It Solves

The world is shifting from **Google Search → AI Engines** (ChatGPT, Perplexity, Claude, Google AI Overview). SMEs without in-house marketing teams are losing visibility as users stop clicking links and start asking AI. This pipeline makes SME content discoverable in the AI-first era.

---

## Pipeline Architecture

```
CLIENT INPUT
  • Company data (website text, docs, past content)  [required]
  • Content goal ("Launch new AI onboarding service")  [required]
  • Competitor data  [optional — system infers top 5 if not provided]
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 1 — DATA INGESTION                                   │
│                                                             │
│  Client data → Chunk → Embed (local, no API) → ChromaDB    │
│  Per-client isolated vector store                           │
│  Model: sentence-transformers/all-MiniLM-L6-v2              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 2 — PRE-FILTERS                                      │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Query Intent Classifier  (runs first)              │   │
│  │                                                     │   │
│  │  Detects the query intent behind the goal           │   │
│  │  (e.g. WHAT / WHY / HOW / WHO / WHICH /             │   │
│  │   WHEN / WHERE)                                     │   │
│  │                                                     │   │
│  │  Selects structure template + GEO priority signal   │   │
│  │  OUTPUT: ContentType                                │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                         │                                   │
│           ┌─────────────┴──────────────┐                    │
│           ▼                            ▼                    │
│  ┌─────────────────────┐   ┌──────────────────────────┐    │
│  │  Brand Analyzer     │   │  Competitor Analyzer     │    │
│  │  (RAG-powered)      │   │                          │    │
│  │                     │   │  Uses query intent to    │    │
│  │  Queries client     │   │  target the right space  │    │
│  │  VectorDB → extracts│   │                          │    │
│  │  tone, values,      │   │  With client data:       │    │
│  │  audience, style    │   │  analyzes actual content │    │
│  │                     │   │                          │    │
│  │  OUTPUT:            │   │  Without client data:    │    │
│  │  BrandProfile       │   │  LLM infers top 5        │    │
│  │                     │   │  competitors for this    │    │
│  │                     │   │  query + finds their     │    │
│  │                     │   │  gaps                    │    │
│  │                     │   │                          │    │
│  │                     │   │  OUTPUT: CompetitorGapMap│    │
│  └──────────┬──────────┘   └────────────┬─────────────┘    │
│             └──────────────┬────────────┘                   │
│                            ▼                                │
│              ┌─────────────────────────┐                    │
│              │  Content Brief Builder  │                    │
│              │                         │                    │
│              │  Synthesizes:           │                    │
│              │  ContentType + Brand +  │                    │
│              │  CompetitorGapMap       │                    │
│              │  → single writing brief │                    │
│              │                         │                    │
│              │  OUTPUT: ContentBrief   │                    │
│              └─────────────────────────┘                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASES 3–5 — QUALITY LOOP  (max 3 attempts)                │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                                                       │  │
│  │  PHASE 3 — CONTENT GENERATION                        │  │
│  │  Content Writer (RAG-grounded)                       │  │
│  │  • Queries client VectorDB for similar past content  │  │
│  │  • Writes using ContentType structure template       │  │
│  │  • Matches brand voice from BrandProfile             │  │
│  │  • Stays within ContentBrief angle + key messages    │  │
│  │                          ↓                           │  │
│  │  PHASE 4 — GEO OPTIMIZATION                         │  │
│  │  Injects: statistics · citations · expert quotes     │  │
│  │           definition blocks · unique data            │  │
│  │  Restructures for AI retrieval (clear H2s)           │  │
│  │                          ↓                           │  │
│  │  PHASE 5 — EVALUATION (judges 1, 2, 4)              │  │
│  │                                                       │  │
│  │  ┌────────────────┐  ┌────────────────┐              │  │
│  │  │ Judge 1        │  │ Judge 2        │              │  │
│  │  │ CUSTOMER FIT   │  │ GEO COMPLIANCE │              │  │
│  │  │ (LLM)          │  │ (regex/determ.)│              │  │
│  │  │ Pain points?   │  │ ✓ Statistics   │              │  │
│  │  │ Value prop?    │  │ ✓ Citations    │              │  │
│  │  │ Right tone?    │  │ ✓ Expert quote │              │  │
│  │  │                │  │ ✓ Definition   │              │  │
│  │  │                │  │ ✓ Unique data  │              │  │
│  │  │                │  │ 20pts each     │              │  │
│  │  └────────────────┘  └────────────────┘              │  │
│  │  ┌──────────────────────────────────────┐            │  │
│  │  │ Judge 4: HUMAN NATURALNESS  (LLM)    │            │  │
│  │  │ AI cliché detection + naturalness    │            │  │
│  │  │ Reads like a skilled copywriter?     │            │  │
│  │  └──────────────────────────────────────┘            │  │
│  │                                                       │  │
│  │  Loop score = avg(J1 + J2 + J4)                      │  │
│  │  Score ≥ 70 → exit loop                              │  │
│  │  Score < 70 → specific feedback → rewrite            │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  POST-LOOP — COMPETITOR EDGE (Judge 3, runs once)           │
│  ┌──────────────────────────────────────┐                   │
│  │ Compares final content vs competitors│                   │
│  │ More specific? Fills gaps? Unique    │                   │
│  │ angle? (LLM judge)                   │                   │
│  └──────────────────────────────────────┘                   │
│                                                             │
│  Final overall = avg(J1 + J2 + J3 + J4)                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 6 — LOCALIZATION                                     │
│                                                             │
│  For each target language (EN, FI, SE, DE...):              │
│  • Queries client VectorDB for existing content in          │
│    that language to match local voice                       │
│  • Applies cultural adaptation (not just translation)       │
│  • Preserves all GEO signals in target language             │
│  • Finnish: directness, modesty, practical tone             │
│                                                             │
│  OUTPUT: One ContentPiece per language                      │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
OUTPUT
  • publication-ready content per language (Markdown)
  • scores: Customer Fit / GEO / Competitor Edge / Naturalness
  • content type detected (WHAT/WHY/HOW/WHO/WHICH/WHEN/WHERE)
  • AI feedback per judge
```

---

## Key Design Decisions

### 1. RAG as the Backbone
Every agent that touches content draws from the client's own VectorDB. This ensures the output is grounded in real brand data — not generic AI output. The brand voice is learned, not assumed.

### 2. Dual-Role Agents
Brand Analyzer and Competitor Analyzer run **twice** — once as pre-filters to guide content creation, and once as post-filters to evaluate the result. This makes evaluation independent from generation.

### 3. Content Type Classification
Before writing, the pipeline detects the **query intent** of the goal — the underlying question the content needs to answer. WH-type intents (What, Why, How, Who, Which, When, Where) are the natural categories that emerge from how people query AI engines. Each type maps to a different structure and GEO priority signal:

| Intent | Structure | GEO Priority |
|--------|-----------|-------------|
| WHAT | Definition → Features → Proof | Definition block |
| WHY | Problem → Evidence → Solution | Statistics |
| HOW | Overview → Steps → Start | Numbered steps |
| WHO | Audience → Challenges → Fit | Specificity |
| WHICH | Options → Comparison → Pick | Comparison data |
| WHEN | Moment → Use cases → Next | Use cases |
| WHERE | Availability → Access → Start | Factual statements |

### 4. GEO Over SEO
Traditional SEO optimizes for Google ranking. GEO optimizes for being **cited by AI engines**. The key signals (Princeton research) that increase AI citation rates by +37-41%:

| Signal | Detection pattern | Why AI engines value it |
|--------|------------------|------------------------|
| Statistics | `37%`, `4.5%`, `3x faster`, `3 out of 4` | Citable, specific, trustworthy |
| Citations | `according to`, `study by`, `(2024)`, `report from` | Signals authoritative sourcing |
| Expert quotes | Attributed strings 15+ chars, `CEO/analyst/researcher` | Human authority signal |
| Definition block | `is defined as`, `refers to`, `What is X?` | AI lifts these verbatim as answers |
| Unique data | `over 200 clients`, `12 countries`, `5 years of experience` | Not found elsewhere = exclusive signal |

The GEO judge is **deterministic regex** (not LLM) — objective, reproducible, and zero tokens.

### 5. Competitor Analysis — Always On
Competitor analysis runs regardless of whether the client provides competitor data:
- **With data:** analyzes the actual competitor content for gaps and unique angles
- **Without data:** LLM infers the competitive landscape from the goal and brand profile — typical claims competitors make in that industry, what they miss, and angles to own

Clients are never asked to research their own competitors.

### 6. Per-Client Isolation
Each client has their own ChromaDB collection. Data never mixes between clients. Re-runs always recreate the collection to avoid stale data.

---

## Data Models

```
BrandProfile
  tone, values[], audience, preferred_style,
  forbidden_words[], differentiators[]

CompetitorGapMap
  competitors[], common_claims[], gaps[], unique_angles[]

ContentBrief
  goal, angle, target_audience, key_messages[], gap_opportunities[]

ContentType
  primary_intent, secondary_intents[], structure[],
  geo_priority, opening_instruction

ContentPiece
  title, headline, sections[{heading, body}], cta, language

JudgeResult
  score (0-100), feedback, details{}

EvaluationResult
  customer: JudgeResult
  geo: JudgeResult
  competitor: JudgeResult
  naturalness: JudgeResult
  overall_score, passed

PipelineOutput
  content_en, content_fi, evaluation, content_type
```

---

## Tech Stack

| Layer | Tool | Why |
|-------|------|-----|
| LLM (generation) | Groq — llama-3.1-8b-instant | Free, 500k tokens/day, fast |
| Embeddings (RAG) | sentence-transformers (local) | No API, no limits, runs offline |
| Vector DB | ChromaDB (local) | Simple, per-client isolation |
| Data validation | Pydantic v2 | Strict models, auto-repair nested lists |
| JSON repair | json-repair | Handles malformed LLM JSON output |
| Orchestration | Plain Python | No framework overhead |

---

## File Structure

```
casevuAI/
│
├── pipeline.py              # Master orchestrator
├── models.py                # All Pydantic data models
├── config.py                # API keys, thresholds, model names
├── demo.py                  # Run with hardcoded sample data
├── run.py                   # CLI — load data from files
│
├── agents/
│   ├── ingestion.py         # Phase 1 — chunk, embed, store
│   ├── brand_analyzer.py    # Phase 2 — brand profile + evaluator
│   ├── competitor_analyzer.py # Phase 2 — gap map + evaluator
│   ├── content_classifier.py  # Phase 2 — WH intent detection
│   ├── content_writer.py    # Phase 3 — RAG-grounded writer
│   ├── geo_optimizer.py     # Phase 4 — GEO signal injection
│   ├── evaluator.py         # Phase 5 — 4 independent judges
│   ├── localizer.py         # Phase 6 — cultural localization
│   └── gemini_client.py     # Shared LLM client (Groq + JSON repair)
│
├── data/
│   ├── chromadb/            # Per-client vector stores (auto-created)
│   └── clients/
│       └── <client_id>/
│           ├── about.txt
│           ├── services.txt
│           └── competitors/
│               └── competitor1.txt
│
├── output/
│   ├── <client>_en.md       # English content
│   ├── <client>_fi.md       # Finnish content
│   └── <client>_scores.json # Evaluation scores
│
└── web/                     # Django demo interface (tool, not product)
```

---

## Competitive Advantage

### The Market Gap

SMEs are losing search visibility as users shift from Google to AI engines (ChatGPT, Perplexity, Claude, Google AI Overview). Existing tools were built for the Google era — keyword density, backlinks, meta tags. None of them optimize for how AI engines decide what to cite.

CasvuAI is built specifically for the AI-first era, targeting the SME segment that has no in-house marketing team and cannot afford an agency.

---

### How CasvuAI Compares

| Capability | Generic AI tools | SEO platforms | Marketing agencies | **CasvuAI** |
|---|---|---|---|---|
| Brand voice | Prompt guess | None | Manual briefs | **Learned from client's real data via RAG** |
| GEO / AI visibility | No | No | Rarely | **Princeton-backed signals (+37-41% AI citation)** |
| Competitor intelligence | None | Keyword gaps only | Manual research | **Autonomous — top 5 inferred per query intent** |
| Content structure | Generic template | Keyword-based | Human judgment | **Query intent classified → matched to GEO template** |
| Quality control | One-shot | One-shot | Human review | **4-judge evaluation loop with automatic retry** |
| Localization | Translation API | None | Extra cost | **Cultural adaptation using client's own language data** |
| Speed | Minutes | Minutes | Days/weeks | **Fully autonomous, single pipeline run** |

---

### Key Differentiators

**1. GEO over SEO**
The system is the first in this segment to explicitly optimize for AI engine citation rather than Google ranking. The 5 GEO signals (statistics, citations, expert quotes, definition blocks, unique data) are injected and verified by a deterministic judge — not left to chance.

**2. Brand voice that is learned, not assumed**
Every agent that touches content queries the client's own ChromaDB vector store. The brand voice is extracted from real past content — tone, values, audience, preferred style, forbidden words. Generic tools guess from a prompt. This system learns from evidence.

**3. Autonomous competitive intelligence**
Clients do not need to know who their competitors are or research their content. The system infers the top 5 most relevant competitors for the specific query intent, identifies what they claim, what they miss, and builds a differentiation strategy automatically.

**4. Query intent drives structure**
Before writing, the pipeline classifies the underlying query intent (WHAT / WHY / HOW / WHO / WHICH / WHEN / WHERE). Each intent maps to a different content structure and GEO priority signal. This is how AI engines organize knowledge — the content is built to match that structure from the start.

**5. Quality loop, not one-shot**
Three independent judges (customer fit, GEO compliance, human naturalness) evaluate every draft. If the overall score is below 70, specific feedback is fed back into the writer and the content is regenerated — up to 3 times. A fourth judge (competitor edge) evaluates the final result once. Most tools generate once and deliver.

**6. Cultural localization, not translation**
Finnish content is not translated from English — it is written using the client's own Finnish-language content as a style reference. Finnish business culture (directness, modesty, practical tone) is applied as a cultural brief, not just a language switch.

**7. Zero marginal cost**
The entire stack runs on free tiers: Groq (500k tokens/day), local sentence-transformers embeddings (no API), and local ChromaDB. An SME can run this pipeline repeatedly with no per-use cost — which is the only model that works for the target market.

---

### Who This Is For

| Segment | Problem | How CasvuAI solves it |
|---|---|---|
| Finnish SMEs (10-100 employees) | No marketing team, losing AI visibility | Fully autonomous pipeline, no expertise required |
| Marketing consultants | Too slow to produce multilingual GEO content manually | Pipeline handles brand extraction, writing, optimization, QA |
| SaaS platforms serving SMEs | Need white-label content automation | Modular pipeline with per-client data isolation |
