"use client";

// Form bersama untuk Portfolio Builder (Quant) & Portfolio AI Advisor (AI):
// pemilih profil risiko + input modal + tombol. Tabel hasilnya berbeda per
// komponen, jadi hanya kontrol input yang di-share di sini.

export const RISK_PROFILES = [
  { key: "CONSERVATIVE", label: "Conservative" },
  { key: "MODERATE", label: "Moderate" },
  { key: "AGGRESSIVE", label: "Aggressive" },
];

type RiskCapitalFormProps = {
  risk: string;
  setRisk: (risk: string) => void;
  capital: number;
  setCapital: (capital: number) => void;
  onSubmit: () => void;
  loading: boolean;
  /** Label tombol saat idle, mis. "Bangun Portofolio". */
  submitLabel: string;
  loadingLabel?: string;
};

export function RiskCapitalForm({
  risk,
  setRisk,
  capital,
  setCapital,
  onSubmit,
  loading,
  submitLabel,
  loadingLabel = "Menyusun…",
}: RiskCapitalFormProps) {
  return (
    <div className="cmp-row" style={{ alignItems: "flex-end" }}>
      <div>
        <p className="chip-label" style={{ marginBottom: 6 }}>
          Profil risiko
        </p>
        <div className="cmp-row">
          {RISK_PROFILES.map((p) => (
            <button
              key={p.key}
              type="button"
              onClick={() => setRisk(p.key)}
              className={`pill-chip ${risk === p.key ? "pill-on" : ""}`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>
      <input
        type="number"
        value={capital}
        min={1_000_000}
        step={10_000_000}
        onChange={(e) => setCapital(Number(e.target.value) || 0)}
        className="field-input flex1"
        style={{ minWidth: 160 }}
        placeholder="Modal (Rp)"
      />
      <button type="button" onClick={onSubmit} disabled={loading} className="primary-btn">
        {loading ? loadingLabel : submitLabel}
      </button>
    </div>
  );
}
