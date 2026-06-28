# 🛡️ SENTINEL — Digital Public Safety Intelligence Platform

> ET AI Hackathon 2.0 | Economic Times

## Overview

SENTINEL is a three-module AI platform built to combat digital fraud,
counterfeit currency, and organised crime networks in India.

## Modules

- **SCAMWatch** — Real-time scam detection for citizens
- **CURRENCYGuard** — Computer vision currency authentication
- **FRAUDGraph** — Graph AI fraud network mapping

## Stack

- LangGraph · Groq · ChromaDB · Neo4j · OpenCV · FastAPI · Streamlit

## Setup

```bash
git clone https://github.com/Sushit-prog/sentinel
cd sentinel
cp .env.example .env
# Fill in your API keys in .env
pip install -r requirements.txt
```

## Run Backend
```bash
uvicorn backend.main:app --reload --port 8000
```

## Run Frontend
```bash
streamlit run frontend/app.py
```

## Architecture

Three intelligence modules share a common ChromaDB threat intelligence
store, enabling cross-module pattern sharing.

---
*Built for ET AI Hackathon 2.0*
