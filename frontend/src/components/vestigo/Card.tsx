import type { ReactNode } from "react";
import { CachedDot } from "../CardStatus";

type VCardProps = {
  title?: ReactNode;
  /** Small sub-line under the title (ticker/context). Mono by default. */
  sub?: ReactNode;
  subMono?: boolean;
  /** Right-aligned slot in the card head (controls, badges). */
  right?: ReactNode;
  cached?: boolean;
  className?: string;
  children: ReactNode;
};

/** Vestigo card shell: surface-1, thin border, 14px radius, cached dot top-right. */
export function VCard({
  title,
  sub,
  subMono = true,
  right,
  cached = false,
  className = "",
  children,
}: VCardProps) {
  return (
    <section className={`card ${className}`}>
      <CachedDot cached={cached} />
      {(title || right) && (
        <div className="card-head">
          <div>
            {title && <h2 className="card-title">{title}</h2>}
            {sub && <p className={`card-sub ${subMono ? "mono" : ""}`}>{sub}</p>}
          </div>
          {right}
        </div>
      )}
      {children}
    </section>
  );
}
