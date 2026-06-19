// Vestigo — shared status components for API-backed cards.
// Skeleton = subtle shimmer (not a spinner); error = clear, no apology.

const CACHE_DATE = "2026-06-15";

export function CardSkeleton({ lines = 4 }: { lines?: number }) {
  return (
    <div className="skel">
      {Array.from({ length: lines }).map((_, index) => (
        <div
          key={index}
          className="skel-line"
          style={{ width: `${60 + (index % 3) * 14}%` }}
        />
      ))}
    </div>
  );
}

export function CardError({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  return (
    <div className="empty-state" style={{ textAlign: "left" }}>
      <p style={{ color: "var(--down)", fontWeight: 500 }}>Gagal memuat data.</p>
      <p className="small mt" style={{ wordBreak: "break-word" }}>
        {message}
      </p>
      <button className="ghost-btn mt" onClick={onRetry} type="button">
        Muat ulang
      </button>
    </div>
  );
}

/**
 * "cached" indicator — a small dot in the card's top-right with a hover tooltip,
 * replacing the noisy pill (design.txt §4.3). Place inside a `.card`.
 */
export function CachedDot({ cached, date = CACHE_DATE }: { cached: boolean; date?: string }) {
  if (!cached) return null;
  return (
    <span
      className="cached-dot"
      tabIndex={0}
      data-tip={`Data per ${date} · cached`}
      aria-label={`Data per ${date}, cached`}
    />
  );
}

/** Back-compat alias: older imports used <CachedBadge cached=… />. */
export function CachedBadge({ cached }: { cached: boolean }) {
  return <CachedDot cached={cached} />;
}
