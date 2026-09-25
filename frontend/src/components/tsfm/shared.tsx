"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { getTsfmModelCard } from "@/lib/api";
import { useApi } from "@/lib/useApi";

// Palet grafik TSFM - divalidasi dengan dataviz/scripts/validate_palette.js di
// permukaan kartu #1B1B1B (bukan dikira-kira):
//   perunggu vs abu pembanding : CVD dE 15,1 / normal 17,8 / kontras >= 3:1
//   turun / datar / naik       : CVD dE 8,7  / normal 23,3 / kontras >= 3:1
// Abu hangat #8A8178 sempat dicoba untuk pembanding dan GAGAL (normal dE 11,9 <
// 15, sulit dibedakan dari perunggu bahkan dengan penglihatan normal).
// Perunggu, hijau, merah adalah warna merek Vestigo yang terkunci.
export const C = {
  brand: "#c19a6b",
  neutral: "#6e7681", // pembanding: IHSG, baseline, run lain
  up: "#22c55e",
  down: "#ef4444",
  axis: "#6b6157",
  grid: "#ffffff14",
} as const;

export const TOOLTIP_STYLE = {
  background: "var(--s1)",
  border: "1px solid var(--bd2)",
  borderRadius: 8,
  color: "var(--t1)",
  fontSize: 12,
} as const;

/** Formatter tooltip Recharts: nilainya bertipe ValueType | undefined, bukan number. */
export function tip(f: (n: number) => string) {
  return (v: unknown) => (v == null ? "-" : f(Number(v)));
}

export const AXIS = { stroke: C.axis, fontSize: 11, tickLine: false } as const;

const TABS = [
  { href: "/model", label: "Sinyal" },
  { href: "/model/performance", label: "Performa Model" },
  { href: "/model/backtest", label: "Backtest" },
  { href: "/model/training", label: "Training Run" },
];

export function ModelTabs() {
  const path = usePathname();
  return (
    <nav className="seg" aria-label="Halaman Vestigo-TSFM" style={{ marginBottom: 16, flexWrap: "wrap" }}>
      {TABS.map((t) => (
        <Link key={t.href} href={t.href} className={`seg-btn ${path === t.href ? "seg-on" : ""}`}>
          {t.label}
        </Link>
      ))}
    </nav>
  );
}

/**
 * Status riset - tampil di keempat halaman. Bukan disclaimer formalitas: di
 * 2016-2024 strategi di atas skor ini kalah dari beli-tahan IHSG setelah biaya,
 * dan halaman yang menampilkan peringkat tanpa konteks itu akan menyesatkan.
 */
export function ResearchStatus() {
  const { data } = useApi(getTsfmModelCard, []);
  if (!data) return null;
  const b = data.backtest_2016_2024;
  const h = data.holdout_2025_2026;
  return (
    <div className="card" style={{ marginBottom: 16, borderColor: "rgba(193,154,107,0.28)" }}>
      <p className="section-label">Status riset</p>
      <p style={{ margin: "6px 0 12px", lineHeight: 1.55 }}>{data.ringkasan}</p>
      <div className="tile-grid-4">
        <div className="tile">
          <div className="tile-label">IC walk-forward</div>
          <div className="tile-val mono">{data.walk_forward.ic_netral_rata.toFixed(3)}</div>
          <div className="card-sub">
            {data.walk_forward.fold_positif}/{data.walk_forward.n_fold} fold positif
          </div>
        </div>
        <div className="tile">
          <div className="tile-label">Bersih 2016-2024</div>
          <div className={`tile-val mono ${b.tsfm_ret_tahunan_bersih < 0 ? "num-down" : "num-up"}`}>
            {(b.tsfm_ret_tahunan_bersih * 100).toFixed(1)}%/thn
          </div>
          <div className="card-sub">IHSG {(b.ihsg_ret_tahunan * 100).toFixed(1)}%/thn</div>
        </div>
        <div className="tile">
          <div className="tile-label">Biaya impas</div>
          <div className="tile-val mono">{b.biaya_impas_persen.toFixed(2)}%</div>
          <div className="card-sub">biaya IDX nyata ~0,70%</div>
        </div>
        <div className="tile">
          <div className="tile-label">Holdout 2025-2026</div>
          <div className={`tile-val mono ${h.tsfm_ret_tahunan_bersih < 0 ? "num-down" : "num-up"}`}>
            {(h.tsfm_ret_tahunan_bersih * 100).toFixed(1)}%/thn
          </div>
          <div className="card-sub">
            t = {h.t_stat_return_bersih.toFixed(2)}, {h.n_rebalance} rebalance - belum signifikan
          </div>
        </div>
      </div>
    </div>
  );
}

export function pct(v: number, dp = 1): string {
  return `${v > 0 ? "+" : ""}${(v * 100).toFixed(dp)}%`;
}
