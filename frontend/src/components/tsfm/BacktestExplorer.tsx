"use client";

import { useMemo, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { getTsfmUi, type TsfmBacktest, type TsfmBacktestConfig } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { CardError, CardSkeleton } from "../CardStatus";
import { VCard } from "../vestigo/Card";
import { AXIS, C, TOOLTIP_STYLE, pct, tip } from "./shared";

function Seg<T extends string | number>({
  label,
  nilai,
  pilihan,
  ubah,
  fmt = String,
}: {
  label: string;
  nilai: T;
  pilihan: T[];
  ubah: (v: T) => void;
  fmt?: (v: T) => string;
}) {
  return (
    <div>
      <p className="section-label" style={{ marginBottom: 4 }}>
        {label}
      </p>
      <div className="seg">
        {pilihan.map((p) => (
          <button key={String(p)} className={`seg-btn ${p === nilai ? "seg-on" : ""}`} onClick={() => ubah(p)}>
            {fmt(p)}
          </button>
        ))}
      </div>
    </div>
  );
}

function cari(grid: TsfmBacktestConfig[], periode: string, hold: number, topK: number, biaya: number) {
  return grid.find((g) => g.periode === periode && g.hold === hold && g.top_k === topK && g.biaya === biaya);
}

export function BacktestExplorer() {
  const bt = useApi(() => getTsfmUi<TsfmBacktest>("backtest"), []);
  const [periode, setPeriode] = useState("walk-forward 2016-2024");
  const [hold, setHold] = useState(10);
  const [topK, setTopK] = useState(20);
  const [biaya, setBiaya] = useState(0.7);
  const [tampilGratis, setTampilGratis] = useState(true);

  const pilih = bt.data ? cari(bt.data.grid, periode, hold, topK, biaya) : undefined;
  const gratis = bt.data ? cari(bt.data.grid, periode, hold, topK, 0) : undefined;
  const ihsg = bt.data?.ihsg[`${periode}|${hold}`];

  const seri = useMemo(() => {
    if (!pilih) return [];
    const g = new Map(gratis?.kurva.map(([t, e]) => [t, e]));
    const ih = new Map(ihsg?.kurva.map(([t, e]) => [t, e]));
    return pilih.kurva.map(([t, e, dd]) => ({
      t,
      tsfm: (e - 1) * 100,
      gratis: g.has(t) ? (g.get(t)! - 1) * 100 : null,
      ihsg: ih.has(t) ? (ih.get(t)! - 1) * 100 : null,
      dd: dd * 100,
    }));
  }, [pilih, gratis, ihsg]);

  if (bt.status === "loading") return <CardSkeleton />;
  if (bt.status === "error") return <CardError message={bt.error} onRetry={bt.reload} />;
  const o = bt.data.pilihan;

  return (
    <>
      <div className="chart-ctrls" style={{ flexWrap: "wrap", gap: 16, marginBottom: 12, alignItems: "flex-end" }}>
        <Seg label="Periode" nilai={periode} pilihan={o.periode} ubah={setPeriode} />
        <Seg label="Top-k emiten" nilai={topK} pilihan={o.top_k} ubah={setTopK} />
        <Seg label="Rebalance (hari)" nilai={hold} pilihan={o.hold} ubah={setHold} />
        <Seg
          label="Biaya bolak-balik"
          nilai={biaya}
          pilihan={o.biaya}
          ubah={setBiaya}
          fmt={(v) => (v === 0 ? "0%" : `${v.toFixed(1)}%`)}
        />
        <button
          className={`pill-chip ${tampilGratis ? "pill-on" : ""}`}
          onClick={() => setTampilGratis((v) => !v)}
          aria-pressed={tampilGratis}
        >
          Tumpuk versi tanpa biaya
        </button>
      </div>

      {pilih && (
        <div className="tile-grid-4" style={{ marginBottom: 16 }}>
          <div className="tile">
            <div className="tile-label">Return tahunan</div>
            <div className={`tile-val mono ${pilih.ret_tahunan < 0 ? "num-down" : "num-up"}`}>
              {pct(pilih.ret_tahunan)}
            </div>
            <div className="card-sub">IHSG {ihsg ? pct(ihsg.ret_tahunan) : "-"}</div>
          </div>
          <div className="tile">
            <div className="tile-label">Sharpe</div>
            <div className="tile-val mono">{pilih.sharpe.toFixed(2)}</div>
            <div className="card-sub">IHSG {ihsg ? ihsg.sharpe.toFixed(2) : "-"}</div>
          </div>
          <div className="tile">
            <div className="tile-label">Drawdown maks</div>
            <div className="tile-val mono num-down">{pct(pilih.maks_drawdown)}</div>
            <div className="card-sub">IHSG {ihsg ? pct(ihsg.maks_drawdown) : "-"}</div>
          </div>
          <div className="tile">
            <div className="tile-label">Dampak biaya</div>
            <div className="tile-val mono">
              {gratis && biaya > 0 ? pct(pilih.ret_tahunan - gratis.ret_tahunan) : "-"}
            </div>
            <div className="card-sub">
              {pilih.n_rebal} rebalance · hit-rate {(pilih.hit_rate * 100).toFixed(0)}%
            </div>
          </div>
        </div>
      )}

      <VCard title="Kurva ekuitas" sub="return kumulatif sejak awal periode, persen">
        <div style={{ height: 300 }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={seri} margin={{ top: 8, right: 8, bottom: 4, left: 0 }}>
              <CartesianGrid stroke={C.grid} vertical={false} />
              <XAxis dataKey="t" {...AXIS} minTickGap={48} tickFormatter={(t: string) => t.slice(0, 7)} />
              <YAxis {...AXIS} width={48} tickFormatter={(v: number) => `${v.toFixed(0)}%`} />
              <ReferenceLine y={0} stroke={C.axis} />
              <Tooltip
                contentStyle={TOOLTIP_STYLE}
                formatter={tip((v) => `${v.toFixed(1)}%`)}
              />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Line
                dataKey="tsfm"
                name={`TSFM, biaya ${biaya}%`}
                stroke={C.brand}
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
              />
              {tampilGratis && biaya > 0 && (
                <Line
                  dataKey="gratis"
                  name="TSFM, tanpa biaya"
                  stroke={C.brand}
                  strokeWidth={2}
                  strokeDasharray="5 4"
                  strokeOpacity={0.7}
                  dot={false}
                  isAnimationActive={false}
                />
              )}
              <Line
                dataKey="ihsg"
                name="Beli-tahan IHSG"
                stroke={C.neutral}
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
                connectNulls
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div style={{ height: 120, marginTop: 8 }}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={seri} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
              <CartesianGrid stroke={C.grid} vertical={false} />
              <XAxis dataKey="t" {...AXIS} minTickGap={48} tickFormatter={(t: string) => t.slice(0, 7)} />
              <YAxis {...AXIS} width={48} tickFormatter={(v: number) => `${v.toFixed(0)}%`} />
              <Tooltip contentStyle={TOOLTIP_STYLE} formatter={tip((v) => `${v.toFixed(1)}%`)} />
              <Area
                dataKey="dd"
                name="Drawdown TSFM"
                stroke={C.down}
                strokeWidth={1.5}
                fill={C.down}
                fillOpacity={0.14}
                isAnimationActive={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
        <p className="disclaimer">{bt.data.catatan}</p>
      </VCard>
    </>
  );
}
