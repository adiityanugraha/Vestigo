"use client";

// Chat With Stock (Phase 5 Day 15) — tanya-jawab streaming berbasis data sistem.
// session_id digenerate klien; streaming via streamChat().

import { useRef, useState } from "react";
import { streamChat } from "@/lib/api";

type Msg = { role: "user" | "assistant"; text: string };

export function ChatWithStock() {
  const sessionId = useRef<string>(
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID()
      : String(Date.now()),
  );
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function send() {
    const text = input.trim();
    if (!text || busy) return;
    setError(null);
    setBusy(true);
    setInput("");
    setMessages((m) => [...m, { role: "user", text }, { role: "assistant", text: "" }]);
    try {
      await streamChat(text, sessionId.current, (chunk) => {
        setMessages((m) => {
          const next = [...m];
          next[next.length - 1] = {
            role: "assistant",
            text: next[next.length - 1].text + chunk,
          };
          return next;
        });
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal mengirim pesan");
      setMessages((m) => m.slice(0, -1)); // buang gelembung assistant kosong
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="rounded-lg border border-white/10 bg-white/[0.03] p-5">
      <h2 className="mb-1 text-base font-semibold text-white">Chat With Stock</h2>
      <p className="mb-4 text-xs text-slate-500">
        Tanya dalam bahasa alami — mis. &ldquo;Mengapa BBCA score tinggi?&rdquo;, &ldquo;Apakah BMRI overbought?&rdquo;
      </p>

      <div className="mb-4 max-h-96 space-y-3 overflow-y-auto">
        {messages.length === 0 && (
          <p className="text-sm text-slate-500">Belum ada percakapan.</p>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            className={`rounded-lg px-3 py-2 text-sm ${
              m.role === "user"
                ? "ml-auto max-w-[85%] bg-sky-500/15 text-sky-100"
                : "mr-auto max-w-[90%] border border-white/10 bg-white/[0.04] text-slate-200"
            }`}
          >
            <p className="whitespace-pre-wrap">{m.text || (busy ? "…" : "")}</p>
          </div>
        ))}
      </div>

      {error && <p className="mb-3 text-sm text-rose-300">{error}</p>}

      <form
        className="flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          void send();
        }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={busy}
          placeholder="Tulis pertanyaan…"
          className="flex-1 rounded-lg border border-white/10 bg-white/[0.03] px-3 py-2 text-sm text-white disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={busy || !input.trim()}
          className="rounded-lg border border-sky-400/40 bg-sky-500/15 px-4 py-2 text-sm font-medium text-sky-100 transition-colors hover:bg-sky-500/25 disabled:opacity-50"
        >
          {busy ? "…" : "Kirim"}
        </button>
      </form>
    </section>
  );
}
