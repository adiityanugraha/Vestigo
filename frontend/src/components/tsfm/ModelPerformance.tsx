"use client";

import { useState } from "react";
import {
  Area,
  Bar,
  CartesianGrid,
  Cell,
  ComposedChart,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { getTsfmTrackRecord, getTsfmUi, type TsfmPerformance } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { CardError, CardSkeleton } from "../CardStatus";
import { VCard } from "../vestigo/Card";
import { AXIS, C, TOOLTIP_STYLE, pct, tip } from "./shared";

const KELAS = ["turun", "datar", "naik"] as const;
const WARNA_KELAS = { turun: C.down, datar: C.neutral, naik: C.up };

function Confusion({ data }: { data: TsfmPerformance["confusion"] }) {
  const periode = Object.keys(data);
  const [pilih, setPilih] = useState(periode[0]);
  const m = data[pilih].matriks;
  return (
    <>
      <div className="seg" style={{ marginBottom: 12 }}>
        {periode.map((p) => (
          <button key={p} className={`seg-btn ${p === pilih ? "seg-on" : ""}`} onClick={() => setPilih(p)}>
            {p}
          </button>
        ))}
      </div>
      <div className="table-wrap">
        <table className="dtable">
          <thead>
            <tr>
              <th>Aktual \ Prediksi</th>
              {KELAS.map((k) => (
                <th key={k} style={{ textAlign: "center" }}>
                  {k}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {KELAS.map((k, i) => (
              <tr key={k}>
                <td>{k}</td>
                {m[i].map((v, j) => (
                  <td
                    key={j}
                    className="mono"
                    style={{
                      textAlign: "center",
                      background: `rgba(193,154,107,${(v * 0.55).toFixed(3)})`,
                      fontWeight: i === j ? 500 : 400,
                    }}
                  >
                    {(v * 100).toFixed(0)}%
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="disclaimer" style={{ marginTop: 12 }}>
        Per baris dijumlah 100 persen (recall). Diagonal = benar. {data[pilih].n.toLocaleString("id-ID")} prediksi.
      </p>
    </>
  );
}

export function ModelPerformance() {
  const perf = useApi(() => getTsfmUi<TsfmPerformance>("performance"), []);
  const live = useApi(getTsfmTrackRecord, []);

  if (perf.status === "loading") return <CardSkeleton />;
  if (perf.status === "error") return <CardError message={perf.error} onRetry={perf.reload} />;
  const d = perf.data;
  const p = d.pembanding;

  return (
    <>
      <div className="grid-2">
        <VCard title="Rolling IC 60 hari" sub="walk-forward 2016-2024, dinetralkan terhadap volatilitas">
          <div className="tile-grid-3" style={{ marginBottom: 12 }}>
            <div className="tile">
              <div className="tile-label">IC rata-rata</div>
              <div className="tile-val mono">{d.ic_harian_ringkas.rata.toFixed(3)}</div>
            </div>
            <div className="tile">
              <div className="tile-label">Hari IC positif</div>
              <div className="tile-val mono">{d.ic_harian_ringkas.positif_pct.toFixed(0)}%</div>
            </div>
            <div className="tile">
              <div className="tile-label">Hari diukur</div>
              <div className="tile-val mono">{d.ic_harian_ringkas.n_hari.toLocaleString("id-ID")}</div>
            </div>
          </div>
          <div style={{ height: 260 }}>
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={d.rolling_ic} margin={{ top: 8, right: 8, bottom: 4, left: 0 }}>
                <CartesianGrid stroke={C.grid} vertical={false} />
                <XAxis dataKey="tanggal" {...AXIS} minTickGap={48} tickFormatter={(t: string) => t.slice(0, 4)} />
                <YAxis {...AXIS} width={44} tickFormatter={(v: number) => v.toFixed(2)} />
                <Tooltip
                  contentStyle={TOOLTIP_STYLE}
                  formatter={(v, n) =>
                    Array.isArray(v)
                      ? [`${Number(v[0]).toFixed(3)} .. ${Number(v[1]).toFixed(3)}`, "pita 95%"]
                      : [Number(v).toFixed(3), n]
                  }
                />
                <ReferenceLine y={0} stroke={C.axis} />
                <Area
                  dataKey={(r: { lo: number; hi: number }) => [r.lo, r.hi]}
                  stroke="none"
                  fill={C.brand}
                  fillOpacity={0.14}
                  name="pita 95%"
                  isAnimationActive={false}
                />
                <Line dataKey="ic" stroke={C.brand} strokeWidth={2} dot={false} name="IC" isAnimationActive={false} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
          <p className="disclaimer">{d.catatan_rolling}</p>
        </VCard>

        <VCard title="Reliability diagram" sub="head arah: probabilitas prediksi vs frekuensi teramati">
          <div style={{ height: 300 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart margin={{ top: 8, right: 8, bottom: 4, left: 0 }}>
                <CartesianGrid stroke={C.grid} />
                <XAxis
                  type="number"
                  dataKey="prediksi"
                  domain={[0, 0.8]}
                  {...AXIS}
                  tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`}
                />
                <YAxis
                  type="number"
                  domain={[0, 0.8]}
                  {...AXIS}
                  width={44}
                  tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`}
                />
                <ReferenceLine
                  segment={[
                    { x: 0, y: 0 },
                    { x: 0.8, y: 0.8 },
                  ]}
                  stroke={C.axis}
                  label={{ value: "sempurna", fill: C.axis, fontSize: 11, position: "insideTopLeft" }}
                />
                <Tooltip
                  contentStyle={TOOLTIP_STYLE}
                  formatter={tip((v) => `${(v * 100).toFixed(1)}%`)}
                  labelFormatter={(l) => `prediksi ${(Number(l) * 100).toFixed(0)}%`}
                />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                {KELAS.map((k) => (
                  <Line
                    key={k}
                    data={d.reliability[k]}
                    dataKey="teramati"
                    name={k}
                    stroke={WARNA_KELAS[k]}
                    strokeWidth={2}
                    dot={{ r: 4, strokeWidth: 2, stroke: "var(--s1)", fill: WARNA_KELAS[k] }}
                    isAnimationActive={false}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
          <p className="disclaimer">Titik di atas diagonal = model terlalu ragu; di bawah = terlalu yakin.</p>
        </VCard>
      </div>

      <div className="grid-2" style={{ marginTop: 16 }}>
        <VCard title="Performa per fold walk-forward" sub="IC netral vol per fold, termasuk fold yang gagal">
          <div style={{ height: 260 }}>
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={d.per_fold} margin={{ top: 8, right: 8, bottom: 4, left: 0 }}>
                <CartesianGrid stroke={C.grid} vertical={false} />
                <XAxis dataKey="val_mulai" {...AXIS} tickFormatter={(t: string) => t.slice(0, 7)} />
                <YAxis {...AXIS} width={44} tickFormatter={(v: number) => v.toFixed(2)} />
                <ReferenceLine y={0} stroke={C.axis} />
                <Tooltip contentStyle={TOOLTIP_STYLE} formatter={tip((v) => v.toFixed(4))} cursor={{ fill: "#ffffff08" }} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Bar dataKey="ic_netral" name="TSFM" radius={[4, 4, 0, 0]}>
                  {d.per_fold.map((f) => (
                    <Cell key={f.fold} fill={f.ic_netral >= 0 ? C.brand : C.down} />
                  ))}
                </Bar>
                <Line
                  dataKey="ic_reversal_netral"
                  name="Baseline reversal 20h"
                  stroke={C.neutral}
                  strokeWidth={2}
                  strokeDasharray="5 4"
                  dot={{ r: 4, strokeWidth: 2, stroke: "var(--s1)", fill: C.neutral }}
                  isAnimationActive={false}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
          <div className="table-wrap" style={{ marginTop: 8 }}>
            <table className="dtable">
              <thead>
                <tr>
                  <th>Fold</th>
                  <th>Val mulai</th>
                  <th style={{ textAlign: "right" }}>IC netral</th>
                  <th style={{ textAlign: "right" }}>Arah bal acc</th>
                  <th style={{ textAlign: "right" }}>QLIKE vs konstan</th>
                </tr>
              </thead>
              <tbody>
                {d.per_fold.map((f) => (
                  <tr key={f.fold}>
                    <td className="mono">{f.fold}</td>
                    <td className="mono">{f.val_mulai}</td>
                    <td className={`mono ${f.ic_netral < 0 ? "num-down" : ""}`} style={{ textAlign: "right" }}>
                      {f.ic_netral.toFixed(4)}
                    </td>
                    <td className="mono" style={{ textAlign: "right" }}>
                      {f.dir_bal_acc.toFixed(3)}
                    </td>
                    <td
                      className={`mono ${f.qlike_model > f.qlike_konstan ? "num-down" : ""}`}
                      style={{ textAlign: "right" }}
                    >
                      {f.qlike_model.toFixed(2)} / {f.qlike_konstan.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </VCard>

        <VCard title="Confusion matrix head arah" sub="triple-barrier, dipecah per periode">
          <Confusion data={d.confusion} />
        </VCard>
      </div>

      <VCard title="Pembanding baseline" sub="model harus mengalahkan pembanding sederhana; kalau kalah, dilaporkan" className="mt-card">
        <div className="grid-3">
          <div>
            <p className="section-label">Peringkat (IC netral vol)</p>
            <table className="dtable">
              <tbody>
                {p.peringkat.map((r) => (
                  <tr key={r.nama}>
                    <td style={{ fontWeight: r.utama ? 500 : 400 }} title={r.catatan}>
                      {r.nama}
                      {r.catatan ? " *" : ""}
                    </td>
                    <td className="mono" style={{ textAlign: "right" }}>
                      {r.ic_netral.toFixed(4)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {p.peringkat.some((r) => r.catatan) && (
              <p className="disclaimer">* {p.peringkat.find((r) => r.catatan)?.catatan}</p>
            )}
          </div>
          <div>
            <p className="section-label">Strategi bersih biaya 2016-2024</p>
            <table className="dtable">
              <tbody>
                {p.strategi_bersih.map((r) => (
                  <tr key={r.nama}>
                    <td style={{ fontWeight: r.utama ? 500 : 400 }}>{r.nama}</td>
                    <td className={`mono ${r.ret_tahunan < 0 ? "num-down" : "num-up"}`} style={{ textAlign: "right" }}>
                      {pct(r.ret_tahunan)}
                    </td>
                    <td className="mono card-sub" style={{ textAlign: "right" }}>
                      SR {r.sharpe.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div>
            <p className="section-label">Volatilitas (QLIKE, kecil = baik)</p>
            <table className="dtable">
              <tbody>
                {p.volatilitas_qlike.map((r) => (
                  <tr key={r.nama}>
                    <td style={{ fontWeight: r.utama ? 500 : 400 }}>{r.nama}</td>
                    <td className="mono" style={{ textAlign: "right" }}>
                      {r.qlike.toFixed(3)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="disclaimer">
              {(() => {
                const t = p.volatilitas_qlike.find((r) => r.utama);
                const kalah = p.volatilitas_qlike.filter((r) => !r.utama && t && r.qlike < t.qlike).length;
                const n = p.volatilitas_qlike.length - 1;
                return kalah === n
                  ? "Head volatilitas kalah dari semua pembanding."
                  : `Head volatilitas kalah dari ${kalah} dari ${n} pembanding.`;
              })()}
            </p>
          </div>
        </div>
      </VCard>

      <VCard title="Track record live" sub="IC dari prediksi harian yang sudah terealisasi (milestone M10)" className="mt-card">
        {live.status === "loading" && <CardSkeleton />}
        {live.status === "error" && <CardError message={live.error} onRetry={live.reload} />}
        {live.data && (
          <div className="tile-grid-3">
            <div className="tile">
              <div className="tile-label">Hari terealisasi</div>
              <div className="tile-val mono">
                {live.data.n_hari} / {live.data.target_m10_hari}
              </div>
              <div className="card-sub">{live.data.n_prediksi_terealisasi} prediksi</div>
            </div>
            <div className="tile">
              <div className="tile-label">IC live rata-rata</div>
              <div className="tile-val mono">{live.data.ringkasan ? live.data.ringkasan.ic_rata.toFixed(3) : "-"}</div>
              <div className="card-sub">
                riset: {live.data.pembanding_riset.ic_walk_forward.toFixed(3)} (netral vol)
              </div>
            </div>
            <div className="tile">
              <div className="tile-label">Status</div>
              <div className="tile-val" style={{ fontSize: 14 }}>
                {live.data.n_hari === 0
                  ? "Menunggu prediksi pertama melewati horizon 10 hari"
                  : live.data.n_hari < live.data.target_m10_hari
                    ? "Terkumpul, belum cukup untuk disimpulkan"
                    : "Cukup untuk dilaporkan"}
              </div>
            </div>
          </div>
        )}
      </VCard>
    </>
  );
}
