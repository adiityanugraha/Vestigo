# Pocket Screener — Backend (Phase 2)

Backend FastAPI: data pipeline, screener (BSJP/BPJS), composite score, AI report,
risk meter, support/resistance, market breadth, screener history, dan scheduler
harian. Gambaran besar proyek: lihat [../README.md](../README.md).

**Layanan:** PostgreSQL **Neon** · Redis **Upstash** · inferensi ML **ONNX Runtime**
(CPU, server-side) · data OHLCV dari **Yahoo Finance** (`.JK`; indeks IHSG → `^JKSE`).

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

> Jalankan `uvicorn` via venv. Jika `uvicorn` tak dikenali, aktifkan venv dulu
> (`.\.venv\Scripts\Activate.ps1`) atau pakai `python -m uvicorn ...`.

## Inisialisasi data

```powershell
python -m app.db.init_db            # buat tabel + seed 81 emiten (incl. IHSG)
python -m app.core.market_data      # ingest OHLCV + hitung indikator (seluruh universe)
python -m app.db.backfill_screening # (opsional) isi screening_history dari data historis
```

> Set `SCHEDULER_ENABLED=false` di `.env` untuk mematikan scheduler saat dev/testing.

## Endpoint utama

| Endpoint | Fungsi |
| -------- | ------ |
| `GET /api/health` | Status app + database + redis |
| `GET /api/screener` | Screener BSJP & BPJS (+ persist ke `screening_history`) |
| `GET /api/ranking` | Composite Score ranking 0–100 |
| `GET /api/stock-report/{ticker}` | AI Stock Report (sentimen + faktor + confidence) |
| `GET /api/risk/{ticker}` | Risk Meter (volatilitas, ATR, drawdown, beta) |
| `GET /api/support-resistance/{ticker}` | Support/Resistance + Breakout Zone |
| `GET /api/market-breadth` | Breadth pasar (persist harian ke PostgreSQL) |
| `GET /api/history` (`/dates`, `/performance`) | Riwayat screener + tracking + winrate |
| `GET /api/market-data/{ticker}` | OHLCV + indikator (untuk chart) |

**Scheduler (WIB):** 07:00 update data · 09:30/10:00/15:30 screener · 16:00 ranking · 17:00 AI report.

**IHSG** disimpan sebagai instrumen indeks (ticker `IHSG` → Yahoo `^JKSE`) dan
**dikecualikan** dari screener/ranking/breadth — hanya dipakai sebagai konteks
pasar (chart/report/risk/S&R di dashboard).

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

## Kontribusi
Dikembangkan oleh **[@adiityanugraha](https://github.com/adiityanugraha)**.
Backend Phase 2 ini dikerjakan dengan bantuan **Claude (Anthropic)** sebagai AI
pair-programmer melalui Claude Code.
