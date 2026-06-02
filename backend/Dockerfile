# Pocket Screener Backend — image produksi (dipakai saat deploy Day 15)
FROM python:3.11-slim

WORKDIR /app

# Dependencies dulu agar layer cache efektif
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kode aplikasi
COPY app ./app

EXPOSE 8000

# Railway/produksi menyuntik $PORT; default 8000 untuk lokal.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
