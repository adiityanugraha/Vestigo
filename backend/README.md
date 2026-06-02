# Pocket Screener — Backend (Phase 2)

Backend FastAPI: data pipeline, screener (BSJP/BPJS), composite score, AI report,
risk meter, support/resistance, market breadth, dan scheduler harian.

## Setup lokal (Windows)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env   # lalu isi DATABASE_URL & REDIS_URL
uvicorn app.main:app --reload --port 8000
```

- Health check: http://localhost:8000/api/health
- Swagger docs: http://localhost:8000/docs

## Struktur

```
app/
├── main.py          FastAPI entrypoint
├── api/             route handlers (health, screener, ranking, dst.)
├── core/            config + engine (indicators, composite_score, ai_report, ...)
├── ml/              inferensi ONNX server-side
├── db/              SQLAlchemy models & session
├── cache/           Redis client
└── scheduler/       APScheduler jobs
```

## Keamanan
Kredensial hanya di `.env` (lokal) / environment variables (produksi).
Jangan commit `.env`. Hanya `.env.example` yang di-push.
