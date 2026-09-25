"use client";

import { useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import {
  getTsfmPredictions,
  getTsfmUi,
  type TsfmCalibration,
  type TsfmDesil,
  type TsfmPrediction,
} from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { CardError, CardSkeleton } from "../CardStatus";
import { VCard } from "../vestigo/Card";
import { AXIS, C, TOOLTIP_STYLE, pct, tip } from "./shared";

const REZIM: Record<TsfmPrediction["regime"], { label: string; cls: string }> = {
  trending_up: { label: "Tren naik", cls: "badge-up" },
  trending_down: { label: "Tren turun", cls: "badge-down" },
  ranging: { label: "Menyamping", cls: "" },
  high_vol: { label: "Vol tinggi", cls: "badge-warn" },
};

/** Keterangan grafik desil, DIHITUNG dari data supaya tidak menyimpang darinya. */
function ringkasDesil(k: TsfmCalibration): string {
  const awal = k.desil_skor["2016-2020"];
  const akhir = k.desil_skor["2021-2024"];
  const rugi = akhir.filter((d) => d.ret_rata < 0).length;
  const f = (v: number) => `${v > 0 ? "+" : ""}${(v * 100).toFixed(2)}%`;
  return (
    `2016-2020: D1 ${f(awal[0].ret_rata)} sampai D10 ${f(awal[9].ret_rata)}. ` +
    `2021-2024: ${rugi} dari 10 desil rata-rata rugi, D10 ${f(akhir[9].ret_rata)}.`
  );
}

function desilDari(rankPct: number): number {
  return Math.min(9, Math.floor(rankPct * 10));
}

/** Distribusi arah sebagai bar bertumpuk (blueprint 8.1), bukan satu angka. */
function ArahBar({ p }: { p: TsfmPrediction["prob"] }) {
  const seg = [
    { v: p.down, c: C.down, t: "turun" },
    { v: p.flat, c: C.neutral, t: "datar" },
    { v: p.up, c: C.up, t: "naik" },
  ];
  return (
    <div
      title={seg.map((s) => `${s.t} ${(s.v * 100).toFixed(0)}%`).join(" · ")}
      style={{ display: "flex", gap: 2, width: 120, height: 8 }}
    >
      {seg.map((s) => (
        <span key={s.t} style={{ flex: s.v, background: s.c, borderRadius: 2 }} />
      ))}
    </div>
  );
}

export function SignalDashboard() {
  const pred = useApi(() => getTsfmPredictions(200), []);
  const kal = useApi(() => getTsfmUi<TsfmCalibration>("calibration"), []);
  const [sektor, setSektor] = useState("semua");
  const [rezim, setRezim] = useState<"semua" | TsfmPrediction["regime"]>("semua");
  const [atas, setAtas] = useState(false);

  const daftarSektor = useMemo(
    () => [...new Set((pred.data?.predictions ?? []).map((p) => p.sector ?? "Lainnya"))].sort(),
    [pred.data],
  );
  const baris = useMemo(
    () =>
      (pred.data?.predictions ?? []).filter(
        (p) =>
          (sektor === "semua" || (p.sector ?? "Lainnya") === sektor) &&
          (rezim === "semua" || p.regime === rezim) &&
          (!atas || p.rank_pct >= 0.7),
      ),
    [pred.data, sektor, rezim, atas],
  );

  const semua: TsfmDesil[] = kal.data?.desil_skor["2016-2024"] ?? [];
  const baru: TsfmDesil[] = kal.data?.desil_skor["2021-2024"] ?? [];

  return (
    <>
      {/* filter di satu baris di atas konten, bukan di dalam kartu */}
      <div className="chart-ctrls" style={{ marginBottom: 12, flexWrap: "wrap", gap: 8 }}>
        <select className="select" value={sektor} onChange={(e) => setSektor(e.target.value)} aria-label="Sektor">
          <option value="semua">Semua sektor</option>
          {daftarSektor.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        {(["semua", "trending_up", "trending_down", "ranging", "high_vol"] as const).map((r) => (
          <button key={r} className={`pill-chip ${rezim === r ? "pill-on" : ""}`} onClick={() => setRezim(r)}>
            {r === "semua" ? "Semua rezim" : REZIM[r].label}
          </button>
        ))}
        <button className={`pill-chip ${atas ? "pill-on" : ""}`} onClick={() => setAtas((v) => !v)}>
          Hanya 30% teratas
        </button>
      </div>

      <VCard
        title="Peringkat harian"
        sub={
          pred.data
            ? `data per ${pred.data.prediction_date} · horizon ${pred.data.horizon_days} hari · ${baris.length} dari ${pred.data.n} emiten`
            : "memuat"
        }
      >
        {pred.status === "loading" && <CardSkeleton />}
        {pred.status === "error" && (
          <div className="empty-state">
            <p>{pred.error}</p>
            <p className="card-sub" style={{ fontFamily: "inherit" }}>
              Prediksi dibuat job harian 07:45 WIB setelah data pasar diperbarui. Jalankan backend dengan
              scheduler aktif, atau picu manual <span className="mono">job_generate_tsfm_predictions</span>.
            </p>
          </div>
        )}
        {pred.data && (
          <div className="table-wrap">
            <table className="dtable">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Emiten</th>
                  <th>Sektor</th>
                  <th style={{ textAlign: "right" }}>Persentil skor</th>
                  <th style={{ textAlign: "right" }}>Historis desil ini (rata-rata 10h)</th>
                  <th style={{ textAlign: "right" }}>Hit-rate hist.</th>
                  <th>Arah (proxy vol)</th>
                  <th style={{ textAlign: "right" }}>Vol harian</th>
                  <th>Rezim</th>
                </tr>
              </thead>
              <tbody>
                {baris.map((p, i) => {
                  const d = desilDari(p.rank_pct);
                  const h = semua[d];
                  const hb = baru[d];
                  return (
                    <tr key={p.ticker}>
                      <td className="mono">{i + 1}</td>
                      <td>
                        <span className="tk-pill mono">{p.ticker}</span>
                        {p.bad_rows > 0 && (
                          <span className="card-sub" title={`${p.bad_rows} dari 512 hari tanpa transaksi di window`}>
                            {" "}
                            · {p.bad_rows} hari kosong
                          </span>
                        )}
                      </td>
                      <td className="card-sub" style={{ fontFamily: "inherit" }}>
                        {p.sector ?? "-"}
                      </td>
                      <td className="mono" style={{ textAlign: "right" }}>
                        {(p.rank_pct * 100).toFixed(0)} <span className="card-sub">D{d + 1}</span>
                      </td>
                      <td className="mono" style={{ textAlign: "right" }}>
                        {h ? (
                          <>
                            <span className={h.ret_rata < 0 ? "num-down" : ""}>{pct(h.ret_rata, 2)}</span>
                            <span className="card-sub" title="Periode 2021-2024 saja">
                              {" "}
                              / {hb ? pct(hb.ret_rata, 2) : "-"}
                            </span>
                          </>
                        ) : (
                          "-"
                        )}
                      </td>
                      <td className="mono" style={{ textAlign: "right" }}>
                        {h ? `${(h.hit_rate * 100).toFixed(0)}%` : "-"}
                      </td>
                      <td>
                        <ArahBar p={p.prob} />
                      </td>
                      <td className="mono" style={{ textAlign: "right" }}>
                        {(p.predicted_vol * 100).toFixed(2)}%
                      </td>
                      <td>
                        <span className={`badge ${REZIM[p.regime].cls}`} style={{ whiteSpace: "nowrap" }}>
                          {REZIM[p.regime].label}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
        <p className="disclaimer" style={{ marginTop: 12 }}>
          Kolom historis: rata-rata return 10 hari emiten di desil skor yang sama, 2016-2024 / 2021-2024 saja. Bar
          arah ditampilkan untuk transparansi - riset membuktikan ia hanya proxy volatilitas, jangan dipakai sebagai
          sinyal.
        </p>
      </VCard>

      <div className="grid-2" style={{ marginTop: 16 }}>
        <VCard title="Apa yang terjadi di tiap desil skor" sub="rata-rata return 10 hari, eksekusi di open berikutnya">
          {kal.status === "loading" && <CardSkeleton />}
          {kal.status === "error" && <CardError message={kal.error} onRetry={kal.reload} />}
          {kal.data && (
            <>
              <div style={{ height: 260 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={semua.map((d, i) => ({
                      desil: `D${d.desil}`,
                      awal: kal.data!.desil_skor["2016-2020"][i].ret_rata * 100,
                      akhir: baru[i].ret_rata * 100,
                    }))}
                    margin={{ top: 8, right: 8, bottom: 4, left: 0 }}
                    barGap={2}
                  >
                    <CartesianGrid stroke={C.grid} vertical={false} />
                    <XAxis dataKey="desil" {...AXIS} />
                    <YAxis {...AXIS} tickFormatter={(v: number) => `${v.toFixed(1)}%`} width={48} />
                    <ReferenceLine y={0} stroke={C.axis} />
                    <Tooltip
                      contentStyle={TOOLTIP_STYLE}
                      formatter={tip((v) => `${v.toFixed(2)}%`)}
                      cursor={{ fill: "#ffffff08" }}
                    />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                    <Bar dataKey="awal" name="2016-2020" fill={C.brand} radius={[4, 4, 0, 0]} />
                    <Bar dataKey="akhir" name="2021-2024" fill={C.neutral} radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <p className="disclaimer">
                {ringkasDesil(kal.data)} Rata-rata dipakai, bukan median: median tiga desil teratas tepat 0 persen
                karena banyak saham IDX tidak bergerak dalam 10 hari (fraksi harga).
              </p>
            </>
          )}
        </VCard>

        <VCard title="Kalibrasi keyakinan head arah" sub="confidence prediksi vs seberapa sering benar">
          {kal.data && (
            <div className="table-wrap">
              <table className="dtable">
                <thead>
                  <tr>
                    <th>Confidence</th>
                    <th style={{ textAlign: "right" }}>Rata-rata</th>
                    <th style={{ textAlign: "right" }}>Benar</th>
                    <th style={{ textAlign: "right" }}>n</th>
                  </tr>
                </thead>
                <tbody>
                  {kal.data.confidence_arah.map((b) => (
                    <tr key={b.dari}>
                      <td className="mono">
                        {b.dari.toFixed(2)}-{b.sampai.toFixed(2)}
                      </td>
                      <td className="mono" style={{ textAlign: "right" }}>
                        {(b.conf_rata * 100).toFixed(0)}%
                      </td>
                      <td className="mono" style={{ textAlign: "right" }}>
                        {(b.akurasi * 100).toFixed(0)}%
                      </td>
                      <td className="mono card-sub" style={{ textAlign: "right" }}>
                        {b.n.toLocaleString("id-ID")}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <p className="disclaimer" style={{ marginTop: 12 }}>
            Model yang terkalibrasi punya kolom &quot;Benar&quot; mendekati &quot;Rata-rata&quot;. Dari 500 ribu
            prediksi walk-forward 2016-2024.
          </p>
        </VCard>
      </div>
    </>
  );
}
