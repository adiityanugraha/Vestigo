"""Konfigurasi aplikasi.

Semua nilai sensitif (DATABASE_URL, REDIS_URL) dibaca dari environment /
file .env — TIDAK PERNAH di-hardcode di kode, sehingga aman di-commit.
Lihat backend/.env.example untuk template.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Metadata aplikasi
    app_name: str = "Pocket Screener API"
    app_version: str = "0.1.0"
    environment: str = "development"  # development | production

    # Koneksi (diisi mulai Day 2 & Day 4). Optional agar Day 1 tetap jalan
    # tanpa kredensial.
    database_url: str | None = None
    redis_url: str | None = None

    # CORS: origin frontend yang boleh memanggil API.
    # Comma-separated string di .env, mis. "http://localhost:3000,https://app.vercel.app"
    cors_origins: str = "http://localhost:3000"

    # Path file model ONNX. Default (None) -> backend/app/ml/model.onnx
    # (resolve di app.ml.inference). Override lewat env ONNX_MODEL_PATH bila perlu.
    onnx_model_path: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Settings di-cache agar .env hanya dibaca sekali."""
    return Settings()
