# TruthGraph — UI + Backend Starter

This starter creates a frontend first and a FastAPI backend contract for your existing TruthGraph model.
Live web evidence retrieval is intentionally not included yet.

## Requirements
- Node.js 20+ and npm
- Python 3.10+
- Your existing model artifacts, expected by default at `backend/models/`:
  - `truthgraph_final_model.pkl`
  - `truthgraph_feature_columns.pkl`
  - `truthgraph_label_encoder.pkl`
  - optional `truthgraph_model_metadata.json`

## 1. Start the backend
From this folder:

```bash
cd backend
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API docs: http://127.0.0.1:8000/docs
Health endpoint: http://127.0.0.1:8000/api/health

## 2. Put model files in place
Copy the model files listed above into `backend/models/`, or set environment variables:
- `TRUTHGRAPH_MODEL_PATH`
- `TRUTHGRAPH_FEATURES_PATH`
- `TRUTHGRAPH_ENCODER_PATH`
- `TRUTHGRAPH_METADATA_PATH` (optional)

**Important:** the classifier expects the same 47 engineered claim-level features used during training. Raw claim text alone is not enough. The current backend deliberately returns a clear `pipeline_not_configured` response until the training-time feature-generation pipeline is connected. Do not interpret placeholder/sample UI data as a real prediction.

## 3. Start the frontend
In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite (usually http://localhost:5173).

The frontend calls `VITE_API_BASE_URL`, defaulting to `http://127.0.0.1:8000`.
You can override it by creating `frontend/.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## 4. Connect the feature pipeline (next backend step)
Implement the project-specific function in `backend/app/prediction.py` named `build_claim_features(claim)`.
It must return a one-row pandas DataFrame with exactly the feature columns expected by the saved model, in the same semantic meaning and preprocessing order used during training. The starter refuses to fabricate those features.

After that, run a smoke test with known examples and compare predictions with your existing notebook/script before adding live retrieval.

## Current scope
- Included: UI, API schema, health endpoint, model artifact loader, safe error handling, CORS for local development.
- Not included: live search/scraping, claim-to-evidence retrieval, production hosting, authentication, persistent history.
