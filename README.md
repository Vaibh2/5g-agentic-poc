# 5G Agentic AI Operations — POC

Autonomous AI system for 5G infrastructure anomaly detection, rollback, and RCA generation.

## Architecture

```
Streamlit UI  ──►  FastAPI Backend  ──►  ChromaDB (RAG)
                        │
                   AI Agent (Claude)
                        │
              Simulated Metrics + Deployments
```

## Quick Start

### 1. Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env          # Optional: add ANTHROPIC_API_KEY
uvicorn main:app --reload
```

### 2. Frontend (new terminal)
```bash
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

### 3. Demo Flow
1. Open Streamlit at http://localhost:8501
2. Go to **🚀 Deploy** → click "Deploy Configuration"
3. Click "Inject Anomaly Spike"
4. Copy the deployment ID, go to **🤖 AI Agent**
5. Paste the ID and click "Run AI Analysis"
6. Watch the agent reason, retrieve RAG context, decide rollback, and generate RCA

## Notes
- Works **without** an API key using deterministic mock AI responses
- Add `ANTHROPIC_API_KEY` to `backend/.env` for real Claude analysis
- ChromaDB is auto-installed; falls back to keyword matching if unavailable
