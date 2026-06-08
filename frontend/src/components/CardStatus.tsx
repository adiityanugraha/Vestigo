// Komponen status bersama untuk card berbasis API (loading & error+retry).

export function CardSkeleton({ lines = 4 }: { lines?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: lines }).map((_, index) => (
        <div
          key={index}
          className="h-3 animate-pulse rounded-full bg-white/10"
          style={{ width: `${90 - index * 12}%` }}
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
    <div className="rounded-lg border border-rose-400/30 bg-rose-500/10 p-4">
      <p className="text-sm font-medium text-rose-200">Gagal memuat</p>
      <p className="mt-1 break-words text-sm text-rose-100/80">{message}</p>
      <button
        className="mt-3 rounded-lg border border-rose-300/30 px-3 py-1.5 text-sm font-medium text-rose-100 transition-colors hover:bg-rose-400/10"
        onClick={onRetry}
        type="button"
      >
        Coba lagi
      </button>
    </div>
  );
}

/** Badge kecil "cached" bila respons dilayani dari Redis. */
export function CachedBadge({ cached }: { cached: boolean }) {
  if (!cached) return null;
  return (
    <span className="rounded-md border border-white/10 px-2 py-0.5 text-[10px] font-medium text-slate-400">
      cached
    </span>
  );
}
