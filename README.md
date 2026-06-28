🛡️ SENTINEL — Digital Public Safety Intelligence Platform

ET AI Hackathon 2.0 | Economic Times

1. Problem Statement

India faces rapidly evolving digital threats:

High-volume scam messages targeting citizens
Counterfeit currency circulation in offline economies
Fragmented fraud intelligence across systems
Lack of unified network-level fraud visibility

Existing solutions are siloed, reactive, and non-intelligent.

SENTINEL addresses this by building a unified AI-driven intelligence system that detects, analyzes, and correlates fraud across text, image, and network data.

2. Solution Overview

SENTINEL is a multi-agent intelligence platform that combines:

Real-time scam detection
Currency authenticity verification using computer vision
Fraud network graph intelligence
Cross-module threat correlation engine

It functions as a shared intelligence system, not independent tools.

3. Core Architecture
System Design
User Input (Text / Image / Structured Data)
        ↓
FastAPI Backend (Orchestration Layer)
        ↓
LangGraph Multi-Agent Pipelines
        ↓
Shared Intelligence Layer (ChromaDB)
        ↓
Optional Graph Intelligence Layer (Neo4j)
        ↓
LLM Reasoning (Groq Llama 3.3 70B)
        ↓
Outputs (Risk Score / Reports / Graphs / Alerts)
4. Technology Stack
Backend
FastAPI (REST orchestration layer)
Pydantic (strict schema validation)
LangGraph (stateful multi-step AI pipelines)
AI Layer
Groq Llama 3.3 70B (reasoning and synthesis)
HuggingFace all-MiniLM-L6-v2 (embeddings)
Hybrid rule-based + LLM decision system
Data Layer
ChromaDB (shared intelligence memory)
Neo4j Aura (fraud network graph, fallback to in-memory graph)
Vision
OpenCV (feature-based currency verification pipeline)
Visualization
Pyvis + NetworkX (fraud network graphs)
Frontend
Streamlit multi-page dashboard
Reporting
ReportLab (court-ready PDF intelligence reports)
5. System Modules
A. SCAMWatch — Scam Detection Engine
Purpose

Detects and scores scam messages received by users.

Pipeline (LangGraph 5-stage system)
Rule-based scam classification (India-specific scam patterns)
LLM semantic fraud analysis (Groq Llama 3.3 70B)
Structured parsing of risk indicators
Multi-signal risk scoring engine (0.0 to 1.0)
Intelligence storage in ChromaDB
Outputs
Scam type classification
Risk score (LOW to CRITICAL)
Behavioral indicators
Recommended user action
B. CURRENCYGuard — Currency Authentication System
Purpose

Detects counterfeit Indian currency using computer vision.

Pipeline (4-stage system)
OpenCV-based feature extraction:
brightness, edges, HSV distribution
security thread detection
watermark region analysis
print sharpness scoring
LLM-based verification synthesis
Automated PDF report generation
Intelligence logging in shared store
Supported Denominations

₹50, ₹100, ₹200, ₹500, ₹2000

Outputs
Authentic / Suspected / Counterfeit verdict
Feature-wise breakdown
Downloadable forensic report
C. FRAUDGraph — Fraud Network Intelligence System
Purpose

Maps fraud networks and identifies organized crime structures.

Pipeline (6-stage system)
Entity extraction (phones, accounts, devices, victims)
Graph construction (Neo4j + NetworkX)
Fraud ring clustering (connected components analysis)
Centrality-based hub detection
LLM intelligence summarization
Court-ready PDF report generation
Relationship Model
CALLS
TRANSFERS_TO
USED_BY
BELONGS_TO
CONTACTED
Outputs
Fraud ring visualization (interactive graph)
Network risk scoring
Intelligence briefing report
6. Cross-Module Intelligence Layer
Shared Intelligence Store (ChromaDB)

All modules write to a unified intelligence memory:

scam_patterns
currency_events
fraud_networks
Correlation Engine

Detects:

Repeated phone numbers across modules
Shared account identifiers
Cross-domain fraud patterns

This enables:

A scam message → linked to fraud network → correlated with prior scam reports

7. Key Engineering Features
1. LangGraph Stateful Pipelines

Each module is a deterministic multi-node graph with typed state transitions.

2. Hybrid Intelligence System
Rule-based systems for speed and zero cost
LLM reasoning for semantic understanding
OpenCV for deterministic visual verification
3. Fault-Tolerant Architecture
Neo4j fallback to in-memory graph
LLM failure fallback responses
Safe degraded mode across services
4. Cross-Module Intelligence Correlation

Shared vector store enables multi-source threat linking.

5. Forensic-Level Reporting

ReportLab-generated structured reports designed for:

law enforcement usage
audit trails
formal documentation
6. Interactive Intelligence Visualization
Pyvis network graphs
entity-level fraud mapping
risk-based node coloring
8. API Endpoints
SCAMWatch
POST /api/scamwatch/analyze
GET /api/scamwatch/patterns
CURRENCYGuard
POST /api/currencyguard/analyze
GET /api/currencyguard/report/{id}
FRAUDGraph
POST /api/fraudgraph/analyze
GET /api/fraudgraph/report/{id}
GET /api/fraudgraph/health
Intelligence Layer
GET /api/intelligence/stats
GET /api/intelligence/recent
GET /api/intelligence/correlations
GET /api/intelligence/health
9. Project Structure
sentinel/
├── backend/
│   ├── api/
│   ├── agents/
│   ├── core/
│   ├── modules/
│   ├── models/
│   └── main.py
├── frontend/
│   ├── app.py
│   └── pages/
├── docker-compose.yml
├── requirements.txt
└── README.md
10. How to Run
git clone https://github.com/Sushit-prog/sentinel
cd sentinel

cp .env.example .env
pip install -r requirements.txt
Backend
uvicorn backend.main:app --reload --port 8000
Frontend
streamlit run frontend/app.py
11. System Behavior Summary

SENTINEL operates as a multi-modal fraud intelligence engine:

Text → scam detection
Image → currency verification
Graph → fraud network reconstruction
Shared memory → cross-domain correlation
12. License

For hackathon evaluation only.
