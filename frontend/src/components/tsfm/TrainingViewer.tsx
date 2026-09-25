"use client";

import {
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
import { getTsfmUi, type TsfmFinetuneRun, type TsfmTitik, type TsfmTraining } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { CardError, CardSkeleton } from "../CardStatus";
import { VCard } from "../vestigo/Card";
import { AXIS, C, TOOLTIP_STYLE, tip } from "./shared";

const STATUS: Record<string, string> = {
  dipakai: "badge-up",
  "diekspor ke Vestigo": "badge-info",
  dibuang: "badge-down",
};

function KurvaKecil({
  titik,
  kunci,
  nama,
  satuan,
  batasSesi,
  domain,
  ambang,
}: {
  titik: TsfmTitik[];
  kunci: "win_s" | "suhu";
  nama: string;
  satuan: string;
  batasSesi: number[];
  /** domain tetap + garis ambang, mis. suhu 97 C (throttling) */
  domain?: [number, number];
  ambang?: { y: number; label: string };
}) {
  return (
    <div style={{ height: 180 }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={titik} margin={{ top: 8, right: 8, bottom: 4, left: 0 }}>
          <CartesianGrid stroke={C.grid} vertical={false} />
          <XAxis dataKey="jam" type="number" domain={[0, "dataMax"]} {...AXIS} tickFormatter={(v: number) => `${v.toFixed(0)}j`} />
          <YAxis {...AXIS} width={40} domain={domain ?? ["auto", "auto"]} />
          {ambang && (
            <ReferenceLine
              y={ambang.y}
              stroke={C.down}
              label={{ value: ambang.label, fill: C.down, fontSize: 10, position: "insideTopRight" }}
            />
          )}
          {batasSesi.map((j) => (
            <ReferenceLine key={j} x={j} stroke={C.axis} />
          ))}
          <Tooltip
            contentStyle={TOOLTIP_STYLE}
            formatter={tip((v) => `${v.toFixed(1)} ${satuan}`)}
            labelFormatter={(l) => `jam ke-${Number(l).toFixed(1)}`}
          />
          <Line dataKey={kunci} name={nama} stroke={C.brand} strokeWidth={1.5} dot={false} isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

function BarisFinetune({ r, label }: { r: TsfmFinetuneRun; label: string }) {
  return (
    <tr>
      <td className="mono">{label}</td>
      <td className="mono" style={{ textAlign: "right" }}>
        {r.best_step.toLocaleString("id-ID")} / {r.step_akhir.toLocaleString("id-ID")}
      </td>
      <td className="mono" style={{ textAlign: "right" }}>
        {r.best_val_loss.toFixed(4)}
      </td>
      <td className="mono" style={{ textAlign: "right" }}>
        {r.jam.toFixed(2)} j
      </td>
    </tr>
  );
}

export function TrainingViewer() {
  const tr = useApi(() => getTsfmUi<TsfmTraining>("training"), []);
  if (tr.status === "loading") return <CardSkeleton />;
  if (tr.status === "error") return <CardError message={tr.error} onRetry={tr.reload} />;
  const d = tr.data;
  const a = d.stage_a;
  // garis vertikal = titik resume (akhir tiap sesi kecuali yang terakhir)
  const batasSesi = a.sesi.slice(0, -1).map((s) => s.jam_akhir);
  const totalJam = a.titik[a.titik.length - 1]?.jam ?? 0;

  return (
    <>
      <div className="tile-grid-4" style={{ marginBottom: 16 }}>
        <div className="tile">
          <div className="tile-label">Stage A wall-clock</div>
          <div className="tile-val mono">{totalJam.toFixed(1)} jam</div>
          <div className="card-sub">{a.sesi.length} sesi, 0 crash</div>
        </div>
        <div className="tile">
          <div className="tile-label">Step pretraining</div>
          <div className="tile-val mono">{a.sesi[a.sesi.length - 1]?.akhir_step.toLocaleString("id-ID")}</div>
          <div className="card-sub">3 miliar patch-token</div>
        </div>
        <div className="tile">
          <div className="tile-label">GPU</div>
          <div className="tile-val" style={{ fontSize: 15 }}>
            {d.perangkat.gpu}
          </div>
          <div className="card-sub">{d.perangkat.presisi}</div>
        </div>
        <div className="tile">
          <div className="tile-label">Fold walk-forward</div>
          <div className="tile-val mono">{d.stage_c.length}</div>
          <div className="card-sub">
            {d.stage_c.reduce((s, r) => s + r.jam, 0).toFixed(1)} jam total
          </div>
        </div>
      </div>

      <VCard
        title="Loss pretraining vs jam wall-clock"
        sub="garis vertikal = sesi berhenti rapi di checkpoint lalu dilanjutkan"
      >
        <div style={{ height: 300 }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart margin={{ top: 8, right: 8, bottom: 4, left: 0 }}>
              <CartesianGrid stroke={C.grid} vertical={false} />
              <XAxis
                dataKey="jam"
                type="number"
                domain={[0, "dataMax"]}
                {...AXIS}
                tickFormatter={(v: number) => `${v.toFixed(0)}j`}
              />
              {/* log: keruntuhan run rusak ke 1e-4 (inti ceritanya) dan kurva jujur ~0,2
                  sama-sama terbaca; skala linier menjepit keduanya di bawah lonjakan warmup */}
              <YAxis
                {...AXIS}
                width={52}
                scale="log"
                domain={[1e-4, 1]}
                allowDataOverflow
                ticks={[1e-4, 1e-3, 1e-2, 0.1, 1]}
                tickFormatter={(v: number) => (v >= 0.1 ? v.toFixed(1) : v.toExponential(0))}
              />
              {batasSesi.map((j) => (
                <ReferenceLine key={j} x={j} stroke={C.axis} label={{ value: "resume", fill: C.axis, fontSize: 10, position: "top" }} />
              ))}
              <Tooltip
                contentStyle={TOOLTIP_STYLE}
                formatter={tip((v) => v.toFixed(4))}
                labelFormatter={(l) => `jam ke-${Number(l).toFixed(1)}`}
              />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Line
                data={a.titik}
                dataKey="loss"
                name="Stage A (dipakai)"
                stroke={C.brand}
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
              />
              <Line
                data={d.stage_a_rusak.titik}
                dataKey="loss"
                name="Run rusak (dibuang)"
                stroke={C.neutral}
                strokeWidth={2}
                strokeDasharray="5 4"
                dot={false}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <p className="disclaimer">
          Run rusak: loss runtuh ke ~0 bukan karena belajar - target rekonstruksi ikut dibentuk parameter yang
          dilatih, dan model menyusutkannya. Loss rendah itu kalah dari tebakan nol. Run dipakai: loss jujur,
          datar di ~0,20 setelah ~12 ribu step.
        </p>
      </VCard>

      <div className="grid-2 mt-card">
        <VCard title="Throughput" sub="window per detik, Stage A">
          <KurvaKecil titik={a.titik} kunci="win_s" nama="throughput" satuan="win/s" batasSesi={batasSesi} />
        </VCard>
        <VCard title="Suhu GPU" sub="derajat Celsius, Stage A">
          <KurvaKecil
            titik={a.titik}
            kunci="suhu"
            nama="suhu"
            satuan="C"
            batasSesi={batasSesi}
            domain={[70, 100]}
            ambang={{ y: 97, label: "throttling 97 C" }}
          />
          <p className="disclaimer">{d.perangkat.catatan_suhu}</p>
        </VCard>
      </div>

      <div className="grid-2 mt-card">
        <VCard title="Silsilah run" sub="run mana turunan dari checkpoint mana">
          <div className="table-wrap">
            <table className="dtable">
              <thead>
                <tr>
                  <th>Run</th>
                  <th>Induk</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {d.silsilah.map((r) => (
                  <tr key={r.id}>
                    <td className="mono" title={r.alasan}>
                      {r.id}
                    </td>
                    <td className="mono card-sub">{r.induk ?? "-"}</td>
                    <td>
                      <span className={`badge ${STATUS[r.status] ?? ""}`}>{r.status}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div style={{ marginTop: 12 }}>
            {d.silsilah
              .filter((r) => r.status === "dibuang")
              .map((r) => (
                <p key={r.id} className="disclaimer">
                  <span className="mono">{r.id}</span>: {r.alasan}
                </p>
              ))}
          </div>
        </VCard>

        <VCard title="Fine-tune & checkpoint" sub="best step dipilih dari val loss">
          <div className="table-wrap">
            <table className="dtable">
              <thead>
                <tr>
                  <th>Run</th>
                  <th style={{ textAlign: "right" }}>Best / akhir</th>
                  <th style={{ textAlign: "right" }}>Val loss</th>
                  <th style={{ textAlign: "right" }}>Durasi</th>
                </tr>
              </thead>
              <tbody>
                <BarisFinetune r={d.stage_b_v1} label="stage_b_v1" />
                <BarisFinetune r={d.stage_b} label="stage_b" />
                {d.stage_c.map((r) => (
                  <BarisFinetune key={r.id} r={r} label={r.id.replace("stage_c/", "C ")} />
                ))}
                <BarisFinetune r={d.stage_d} label="stage_d" />
              </tbody>
            </table>
          </div>
        </VCard>
      </div>
    </>
  );
}
