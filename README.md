<div align="center">

# 🛡️ SENTINEL

### AI-Powered Digital Public Safety Intelligence Platform

**Built for ET AI Hackathon 2.0 | The Economic Times**

Detect Digital Scams • Authenticate Currency • Map Fraud Networks

---

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi)
![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-blue?style=for-the-badge)
![Groq](https://img.shields.io/badge/Groq-Llama--3.3%2070B-orange?style=for-the-badge)
![Neo4j](https://img.shields.io/badge/Neo4j-GraphDB-4581C3?style=for-the-badge&logo=neo4j)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20Store-purple?style=for-the-badge)
![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-5C3EE8?style=for-the-badge&logo=opencv)

</div>

---

# 📖 Overview

**SENTINEL** is an AI-powered public safety intelligence platform designed to combat digital fraud, counterfeit currency, and organised financial crime in India.

Rather than solving a single problem, SENTINEL combines multiple AI systems into one unified intelligence platform where every investigation contributes to a shared knowledge base.

The platform consists of three independent AI modules connected through a common intelligence layer, allowing threats discovered in one module to strengthen investigations across the others.

---

# 🎯 Problem Statement

India is witnessing a rapid increase in digital financial crimes including:

- Digital Arrest scams
- Fake KYC verification fraud
- Investment scams
- Lottery scams
- Counterfeit currency circulation
- Organised financial crime networks

Current solutions generally address these problems independently.

SENTINEL provides a unified AI-driven intelligence platform capable of analysing scams, verifying currency authenticity, investigating fraud networks, and correlating intelligence across multiple investigations.

---

# ✨ Key Features

- Multi-Agent AI workflows powered by LangGraph
- Shared Threat Intelligence using ChromaDB
- Graph-based Fraud Network Analysis
- AI Scam Detection with Risk Scoring
- Computer Vision Currency Authentication
- Interactive Intelligence Dashboard
- Automatic PDF Intelligence Reports
- Neo4j Network Visualization
- Cross-Module Threat Correlation
- Graceful Failure Recovery

---

# 🏗 System Architecture

```
                    ┌───────────────────────┐
                    │      Streamlit UI     │
                    └──────────┬────────────┘
                               │
                    ┌──────────▼───────────┐
                    │      FastAPI API     │
                    └──────────┬───────────┘
                               │
        ┌──────────────┬──────────────┬──────────────┐
        │              │              │
        ▼              ▼              ▼
  SCAMWatch      CURRENCYGuard    FRAUDGraph
        │              │              │
        └──────────────┴──────────────┘
                      │
                      ▼
         Shared Intelligence Store
                (ChromaDB)
                      │
                      ▼
      Cross-Module Threat Correlation
```

---

# 🧠 Intelligence Modules

---

## 🛡️ SCAMWatch

AI-powered scam detection engine for analysing suspicious messages and calls.

### Pipeline

```
Input Text
     │
     ▼
Rule-Based Classification
     │
     ▼
LLM Semantic Analysis
     │
     ▼
Risk Scoring Engine
     │
     ▼
Threat Intelligence Store
```

### Detects

- Digital Arrest
- Fake KYC
- Investment Scam
- Lottery Scam
- Job Scam
- Romance Scam
- Authority Impersonation

---

## 💵 CURRENCYGuard

Computer Vision pipeline for counterfeit currency detection.

### Pipeline

```
Currency Image
      │
      ▼
OpenCV Feature Analysis
      │
      ▼
LLM Expert Reasoning
      │
      ▼
Authenticity Report
      │
      ▼
Threat Intelligence Store
```

### Security Checks

- Image Quality
- Aspect Ratio
- Security Thread
- Watermark Region
- Serial Number
- Print Sharpness
- Color Distribution

Supported Denominations

- ₹50
- ₹100
- ₹200
- ₹500
- ₹2000

---

## 🕸 FRAUDGraph

Graph Intelligence engine for analysing organised financial crime.

### Pipeline

```
Evidence
     │
     ▼
Entity Extraction
     │
     ▼
Graph Construction
     │
     ▼
Cluster Detection
     │
     ▼
LLM Intelligence Summary
     │
     ▼
Investigation Report
```

### Entity Types

- Phone Numbers
- Bank Accounts
- Devices
- Victims
- Locations

---

# 🔗 Cross-Module Intelligence

The most important innovation of SENTINEL is its **shared intelligence layer**.

Instead of operating independently, every module contributes to a common ChromaDB intelligence store.

Example workflow:

```
Citizen Reports Scam
         │
         ▼
 Phone Number Stored
         │
         ▼
FraudGraph Investigation
         │
         ▼
Same Number Discovered
         │
         ▼
High Confidence Alert
```

This enables threat correlation across multiple investigations and improves intelligence over time.

---

# ⚙️ Technology Stack

| Layer | Technology |
|--------|------------|
| Frontend | Streamlit |
| Backend | FastAPI |
| AI Framework | LangGraph |
| LLM | Groq Llama 3.3 70B |
| Vector Database | ChromaDB |
| Graph Database | Neo4j Aura |
| Computer Vision | OpenCV |
| Embeddings | HuggingFace MiniLM |
| Graph Analysis | NetworkX |
| Visualization | PyVis |
| Reports | ReportLab |

---

# 📂 Project Structure

```
sentinel/

├── backend/
│   ├── api/
│   ├── agents/
│   ├── core/
│   ├── models/
│   └── modules/
│
├── frontend/
│   ├── app.py
│   └── pages/
│
├── docker-compose.yml
├── requirements.txt
├── README.md
└── .env.example
```

---

# 🚀 Installation

Clone the repository

```bash
git clone https://github.com/Sushit-prog/sentinel.git

cd sentinel
```

Install dependencies

```bash
pip install -r requirements.txt
```

Create environment variables

```bash
cp .env.example .env
```

Configure

```
GROQ_API_KEY=

NEO4J_URI=

NEO4J_USERNAME=

NEO4J_PASSWORD=
```

---

# ▶️ Running the Project

## Start Backend

```bash
uvicorn backend.main:app --reload --port 8000
```

---

## Start Frontend

```bash
streamlit run frontend/app.py
```

---

# 📡 API Endpoints

| Endpoint | Description |
|-----------|-------------|
| POST `/api/scamwatch/analyze` | Analyse suspicious messages |
| GET `/api/scamwatch/patterns` | Scam pattern library |
| POST `/api/currencyguard/analyze` | Currency authentication |
| GET `/api/currencyguard/report/{id}` | Download PDF report |
| POST `/api/fraudgraph/analyze` | Fraud network analysis |
| GET `/api/fraudgraph/report/{id}` | Investigation report |
| GET `/api/intelligence/stats` | Intelligence statistics |
| GET `/api/intelligence/recent` | Recent activity |
| GET `/api/intelligence/correlations` | Cross-module correlations |

---

# 📊 Future Roadmap

- Voice Scam Detection
- OCR for FIR Documents
- WhatsApp Integration
- Multi-Language Support
- Real-Time Alert Streaming
- Government Intelligence Integration
- Mobile Application
- Federated Threat Intelligence

---

# 🤝 Contributing

Contributions, feature requests, and suggestions are welcome.

If you would like to improve SENTINEL, feel free to fork the repository and submit a pull request.

---

# 📄 License

This project is licensed under the MIT License.

---

<div align="center">

**Built for ET AI Hackathon 2.0**

AI for Public Safety • Intelligence • Trust

</div>
