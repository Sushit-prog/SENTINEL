<div align="center">

# SENTINEL

### Digital Public Safety Intelligence Platform

**ET AI Hackathon 2.0 | The Economic Times**

*"AI for Digital Public Safety: Defeating Counterfeiting, Fraud & Digital Arrest Scams"*

---

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agent%20Orchestration-3178C6?style=flat-square&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![Groq](https://img.shields.io/badge/Groq-Llama%203.3%2070B-FF6B35?style=flat-square&logoColor=white)](https://groq.com/)
[![Neo4j](https://img.shields.io/badge/Neo4j-Graph%20Database-4581C3?style=flat-square&logo=neo4j&logoColor=white)](https://neo4j.com/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20Store-FF6B9D?style=flat-square&logoColor=white)](https://www.trychroma.com/)
[![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-5C3EE8?style=flat-square&logo=opencv&logoColor=white)](https://opencv.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Frontend-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io/)

</div>

---

## The Problem

India logged **1.14 million cybercrime complaints in 2023** — up 60% year-on-year. "Digital arrest" scams alone cost citizens over **₹1,776 crore in nine months of 2024**. RBI's 2025 report flagged record counterfeit currency seizures, with fakes now sophisticated enough to defeat manual bank checks.

The real failure isn't lack of evidence after a crime — it's lack of intelligence before mass victimisation. Most fraud-detection tools work in isolation; a scam detector doesn't talk to a graph-analysis tool, which doesn't talk to a currency scanner.

## The Solution

**SENTINEL** connects four AI modules through a single shared intelligence layer. Every threat caught by a citizen-facing tool automatically strengthens a law-enforcement investigation tool — in real time, with zero manual cross-referencing.

```
                          ┌─────────────────────────┐
                          │     Streamlit UI         │
                          │  (6 pages, dark theme)   │
                          └────────────┬────────────┘
                                       │
                          ┌────────────▼────────────┐
                          │      FastAPI Backend     │
                          │     (11+ REST endpoints) │
                          └────────────┬────────────┘
                                       │
          ┌────────────────┬───────────┴───────────┬────────────────┐
          │                │                       │                │
          ▼                ▼                       ▼                ▼
    ┌───────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────┐
    │ SCAMWatch │  │ CURRENCYGuard│  │  FRAUDGraph  │  │ GeoIntel │
    │  5-node   │  │   4-node     │  │   6-node     │  │ Heatmap  │
    │ LangGraph │  │   Pipeline   │  │   Pipeline   │  │ Dashboard│
    └─────┬─────┘  └──────┬───────┘  └──────┬───────┘  └────┬─────┘
          │               │                  │               │
          └───────────────┴──────────┬───────┴───────────────┘
                                     │
                          ┌──────────▼──────────┐
                          │   Shared ChromaDB    │
                          │  Intelligence Layer  │
                          └──────────┬──────────┘
                                     │
                          ┌──────────▼──────────┐
                          │  Cross-Module Threat │
                          │    Correlation       │
                          └─────────────────────┘
```

---

## Modules

### SCAMWatch — Citizen Scam Detection

Real-time scam message analysis powered by a 5-node LangGraph pipeline. A zero-cost rule-based pre-classifier flags obvious signals, then Groq Llama 3.3 70B performs deep semantic analysis followed by structured risk scoring.

**Scam Types:** Digital Arrest | Fake KYC | Fake Investment | Fake Job | Fake Lottery | Impersonation | Romance

**Languages:** English, Hindi, Tamil, Bengali, Telugu

**Accuracy:** 85% detection, 0 false positives across 20 sample cases

**Features:**
- Plain-language verdict with recommended actions
- One-click File Complaint (cybercrime.gov.in)
- One-click Number Block (Sanchar Saathi / TRAI)
- Citizen Alert with emergency contacts (1930, cybercrime.gov.in)
- Structured MHA-shaped alert payload

```
Input Text → Rule-Based Classification → LLM Semantic Analysis → Risk Scoring → Intelligence Store
```

---

### CURRENCYGuard — Currency Authentication

Computer-vision pipeline running 7 OpenCV security checks with a dedicated play-money detector that flags obvious fakes before deeper analysis (cost-efficient design).

**Security Checks:** Image Quality | Aspect Ratio | Color Distribution | Security Thread | Serial Number | Watermark Region | Print Sharpness

**Supported Denominations:** ₹50, ₹100, ₹200, ₹500, ₹2000

**Verdicts:** GENUINE | SUSPECT | COUNTERFEIT | INCONCLUSIVE

**Features:**
- Downloadable PDF authenticity report
- Play money pre-screening
- Hybrid rule+CV+LLM pipeline

```
Currency Image → OpenCV Feature Analysis → LLM Expert Reasoning → Authenticity Report → Intelligence Store
```

---

### FRAUDGraph — Fraud Network Mapping

Graph-AI engine for analysing organised financial crime. Extracts entities from structured input and free-text victim statements (LLM-powered extraction from unstructured narrative).

**Entity Types:** Phone Numbers | Bank Accounts | Devices | Victims | Locations

**Analysis:** Connected components + betweenness centrality fraud ring detection

**Evidence Kit (ZIP):**
- PDF intelligence report
- Interactive graph visualization (HTML)
- Entity inventory (CSV)
- Raw analysis data (JSON)
- Manifest citing IT Act 2000 and DPDP Act 2023

```
Evidence → Entity Extraction → Graph Construction → Cluster Detection → Intelligence Summary → Court-Admissible Report
```

---

### GeoIntel — Geospatial Intelligence

Maps live incidents from all three modules onto real, publicly-reported NCRB/RBI/MHA fraud and counterfeit hotspot regions across India.

**15 Hotspot Locations:** Jamtara, Mewat, Deoghar, major metros, and other NCRB/RBI/MHA-flagged regions

**Features:**
- Pydeck heatmap with dark theme
- Filterable by module and risk level
- Geographic intelligence picture from individual reports

---

### WhatsApp Shield — Chat-Based Detection

A WhatsApp-styled chat interface that lets citizens interact with SCAMWatch conversationally — same backend, familiar channel.

- WhatsApp-style UI
- Real-time analysis via SCAMWatch API
- 4 sample scam messages for demo

---

### Intelligence Dashboard — Cross-Module Analytics

The platform's signature view: turns individual reports into a unified threat intelligence picture.

- Live Threat Monitor with detection timeline chart
- Cross-module correlation alerts
- Real-time activity feed
- Module health checks

**Key Correlation:** A phone number flagged independently in a citizen's SCAMWatch report and a police FRAUDGraph investigation surfaces as an automatic correlation alert — a connection a human analyst would otherwise have to find by hand.

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | Streamlit | 6-page dark-theme UI |
| Backend | FastAPI | 11+ REST API endpoints |
| Agent Orchestration | LangGraph | 5/4/6-node multi-agent pipelines |
| LLM | Groq Llama 3.3 70B | Semantic analysis & reasoning |
| Vector Store | ChromaDB | Shared intelligence layer |
| Graph Database | Neo4j | Fraud network mapping (in-memory fallback) |
| Computer Vision | OpenCV | 7 currency security feature checks |
| Embeddings | HuggingFace all-MiniLM-L6-v2 | Semantic search |
| PDF Generation | ReportLab | Intelligence & authenticity reports |
| Graph Visualization | NetworkX + pyvis | Interactive fraud network graphs |
| Mapping | pydeck | Geospatial heatmap dashboard |

---

## Project Structure

```
sentinel/
├── backend/
│   ├── api/              # FastAPI route handlers
│   ├── agents/           # LangGraph agent definitions
│   ├── core/             # Shared utilities, config, intelligence store
│   ├── models/           # Pydantic data models
│   └── modules/          # Module implementations
│       ├── scamwatch/     # Scam detection pipeline
│       ├── currencyguard/ # Currency authentication pipeline
│       ├── fraudgraph/    # Fraud network analysis pipeline
│       ├── geointel/      # Geospatial heatmap module
│       ├── whatsapp/      # WhatsApp-style interface backend
│       └── intelligence/  # Cross-module analytics
├── frontend/
│   ├── app.py            # Streamlit entry point
│   └── pages/            # 6 UI pages
├── data/                 # Hotspot data, sample inputs
├── reports/              # Generated PDF reports
├── docker-compose.yml
├── requirements.txt
├── test_all.py           # Integration test suite
└── .env.example
```

**~50 files** across 6 frontend pages, 6 backend APIs, 3 agents, 9 module implementations, and 4 config files.

---

## Quick Start

### Prerequisites

- Python 3.11+
- Groq API key (free tier works)
- Neo4j (optional — falls back to in-memory graph)

### Installation

```bash
git clone https://github.com/Sushit-prog/SENTINEL.git
cd SENTINEL
pip install -r sentinel/requirements.txt
```

### Configuration

```bash
cp sentinel/.env.example sentinel/.env
```

Edit `sentinel/.env`:

```env
GROQ_API_KEY=your_groq_api_key_here
NEO4J_URI=bolt://localhost:7687    # optional
NEO4J_USERNAME=neo4j               # optional
NEO4J_PASSWORD=                    # optional
```

### Running

```bash
# Start the backend (API server)
uvicorn sentinel.backend.main:app --reload --port 8000

# Start the frontend (in a separate terminal)
streamlit run sentinel/frontend/app.py
```

Open **http://localhost:8501** in your browser.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/scamwatch/analyze` | Analyse suspicious messages for scam patterns |
| GET | `/api/scamwatch/patterns` | Scam pattern library |
| POST | `/api/currencyguard/analyze` | Currency authenticity verification |
| GET | `/api/currencyguard/report/{id}` | Download PDF authenticity report |
| POST | `/api/fraudgraph/analyze` | Fraud network analysis from evidence |
| GET | `/api/fraudgraph/report/{id}` | Download investigation evidence kit |
| GET | `/api/geointel/hotspots` | Geospatial hotspot data |
| POST | `/api/whatsapp/analyze` | WhatsApp-style chat analysis |
| GET | `/api/intelligence/stats` | Cross-module intelligence statistics |
| GET | `/api/intelligence/recent` | Recent detection activity |
| GET | `/api/intelligence/correlations` | Cross-module threat correlations |

---

## Engineering Design Decisions

**Hybrid rule+LLM pipelines** — Cheap deterministic checks run before expensive LLM calls, keeping cost per analysis minimal while maintaining accuracy.

**Graceful degradation** — Neo4j falls back to in-memory NetworkX graph. LLM failures return safe fallback messages instead of crashing. Every module works independently even if shared infrastructure is unavailable.

**Shared intelligence layer** — All modules write to a single ChromaDB vector store. A phone number flagged in SCAMWatch automatically strengthens a FRAUDGraph investigation — zero manual cross-referencing.

**Typed Pydantic models end-to-end** — Structured data contracts between all layers, preventing silent data-shape bugs.

**CPU-inference, zero GPU dependency** — Runs on 8GB RAM. Built to be realistically deployable, not just demo-able.

---

## Scope Transparency

SENTINEL is honest about what it is and isn't:

- **Voice-spoofing and deepfake-image detection** are architecture placeholders, not trained classifiers — flagged transparently in-product rather than overclaimed.
- **WhatsApp/IVR integration** is a functional simulation (identical backend, mocked channel) rather than a live Meta/telecom API integration — a deliberate scope choice given hackathon constraints.
- **Neo4j** runs with graceful in-memory fallback when the graph database isn't available — full functionality preserved.

---

## Test Results

```
Accuracy:  85% scam detection (0 false positives)
Languages: 5 (English, Hindi, Tamil, Bengali, Telugu)
Hotspots:  15 (NCRB/RBI/MHA flagged regions)
Scam Types: 7
CV Checks:  7 (OpenCV security feature analysis)
```

---

## Future Roadmap

- Voice scam detection (audio analysis pipeline)
- Deepfake image detection (GAN-generated currency imagery)
- OCR for FIR document processing
- Real-time WhatsApp/Telegram bot integration
- Multi-language expansion (Kannada, Malayalam, Marathi)
- Real-time alert streaming via WebSockets
- Government intelligence API integration
- Mobile application (React Native)
- Federated threat intelligence across jurisdictions

---

## Contributing

Contributions, feature requests, and suggestions are welcome.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit changes (`git commit -m 'Add your feature'`)
4. Push to branch (`git push origin feature/your-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License.

---

<div align="center">

**Built for ET AI Hackathon 2.0**

AI for Digital Public Safety — Intelligence at Scale

</div>
