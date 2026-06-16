"""Phase 5 Day 1 — wrapper LLM provider-agnostic (Gemini).

Tes unit tanpa jaringan (aman-gagal saat key kosong) + smoke LIVE yang
di-skip bila GEMINI_API_KEY belum dikonfigurasi (mirror tes DB-gated Phase 4).
Smoke LIVE memanggil API sungguhan (memakai sedikit kuota free tier).
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.ai import llm_client


@pytest.fixture(autouse=True)
def _reset_llm():
    """Reset singleton sebelum & sesudah tiap tes agar tak ada state bocor."""
    llm_client.reset_client()
    yield
    llm_client.reset_client()


def test_unavailable_without_key(monkeypatch):
    """Tanpa API key: lapisan AI nonaktif & pemanggilan melempar LLMError (bukan crash)."""
    monkeypatch.setattr(
        llm_client,
        "get_settings",
        lambda: SimpleNamespace(gemini_api_key=None, llm_model="gemini-2.5-flash"),
    )
    llm_client.reset_client()

    assert llm_client.is_available() is False
    with pytest.raises(llm_client.LLMError):
        llm_client.generate("halo")
    with pytest.raises(llm_client.LLMError):
        llm_client.generate_json("halo")
    with pytest.raises(llm_client.LLMError):
        list(llm_client.stream("halo"))


def test_generate_smoke():
    """LIVE: prompt sederhana -> teks non-kosong (skip bila AI nonaktif)."""
    if not llm_client.is_available():
        pytest.skip("GEMINI_API_KEY belum dikonfigurasi — lewati smoke LIVE.")
    out = llm_client.generate(
        "Balas hanya dengan satu kata: pong",
        max_output_tokens=20,
    )
    assert isinstance(out, str)
    assert out.strip() != ""


def test_generate_json_smoke():
    """LIVE: output terstruktur (JSON) bisa di-parse jadi dict (skip bila nonaktif)."""
    if not llm_client.is_available():
        pytest.skip("GEMINI_API_KEY belum dikonfigurasi — lewati smoke LIVE.")
    data = llm_client.generate_json(
        'Kembalikan objek JSON {"ok": true} saja.',
        max_output_tokens=50,
    )
    assert isinstance(data, (dict, list))


def test_stream_smoke():
    """LIVE: streaming menghasilkan setidaknya satu potongan teks (skip bila nonaktif)."""
    if not llm_client.is_available():
        pytest.skip("GEMINI_API_KEY belum dikonfigurasi — lewati smoke LIVE.")
    chunks = list(llm_client.stream("Hitung 1 sampai 3.", max_output_tokens=30))
    assert all(isinstance(c, str) for c in chunks)
    assert "".join(chunks).strip() != ""
