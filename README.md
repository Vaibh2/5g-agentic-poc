# 5G Agentic AI Operations — POC

Autonomous AI system for 5G infrastructure anomaly detection, rollback, and RCA generation using Gemini AI.

## Architecture

```
React Frontend  ──►  FastAPI Backend  ──►  CrewAI Agents (Gemini)
                         │
                    Deploy Agent → Network Agent → Security Agent
                                    ↓ (on failure)
                              Rollback Agent
```

## Tech Stack

- **Frontend**: React + Vite + TypeScript + TailwindCSS
- **Backend**: FastAPI + Python
- **AI**: CrewAI + Gemini (Google Generative AI)
- **Database**: ChromaDB (RAG for context retrieval)

## How to Start the Project

### 1. Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env          # Add GEMINI_API_KEY
uvicorn main:app --reload
```
- Backend runs at: http://localhost:8000

### 2. Frontend (React)
```bash
cd frontend
npm install
npm run dev
```
- Frontend runs at: http://localhost:5173

### 3. Demo Flow
1. Open Frontend at http://localhost:5173
2. Go to **Deploy** tab
3. Click "Deploy Configuration"
4. Watch the AI agents validate your configuration
5. Use different config files to test pass/fail scenarios

## Configuration Testing

### ✅ Test 1: Valid Configuration (Passes)
Use `config.yaml` - Contains valid MTU values
```bash
# Push config.yaml to trigger successful deployment
git add config.yaml
git commit -m "valid config"
git push
```
Expected: Deployment passes all validation agents

### ❌ Test 2: Invalid Configuration (Fails)
Use `config2.yaml` - Contains invalid MTU (99999)
```bash
# Push config2.yaml to trigger failed deployment
git add config2.yaml
git commit -m "invalid config"
git push
```
Expected: Deploy Agent fails → Triggers Rollback Agent

## Environment Variables

Create `backend/.env`:
```env
GEMINI_API_KEY=your_google_gemini_api_key_here
```

Get your Gemini API key from: https://aistudio.google.com/app/apikey

## Notes

- Works **without** API key using deterministic mock responses
- Add valid `GEMINI_API_KEY` to `backend/.env` for real Gemini AI analysis
- The system uses CrewAI multi-agent architecture with:
  - Deploy Agent: Validates YAML configs
  - Network Agent: Validates network settings
  - Security Agent: Validates security compliance
  - Rollback Agent: Handles recovery on failure