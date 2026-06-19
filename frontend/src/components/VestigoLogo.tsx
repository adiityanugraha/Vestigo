type VestigoLogoProps = {
  size?: number;
  className?: string;
  strokeWidth?: number;
};

/**
 * Vestigo brand mark — an owl rendered from a single trail/jejak stroke,
 * a nod to the name (Latin: "I track / trace"). Drawn in --brand (bronze).
 * Reused in the sidebar wordmark and the Chat With Stock empty state.
 */
export function VestigoLogo({
  size = 30,
  className,
  strokeWidth = 3.6,
}: VestigoLogoProps) {
  return (
    <svg
      viewBox="0 0 100 100"
      width={size}
      height={size}
      fill="none"
      stroke="var(--brand)"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d="M50 93 C26 83 13 62 16 43 C17 34 25 30 32 34 C40 38 46 43 50 50 C54 43 60 38 68 34 C75 30 83 34 84 43 C87 62 74 83 50 93 Z" />
      <path d="M31 35 C26 25 24 13 29 11 C33 16 37 28 40 33 Z" />
      <path d="M69 35 C74 25 76 13 71 11 C67 16 63 28 60 33 Z" />
      <circle cx="35" cy="57" r="13" />
      <circle cx="65" cy="57" r="13" />
      <circle cx="35" cy="57" r="4.4" fill="var(--brand)" stroke="none" />
      <circle cx="65" cy="57" r="4.4" fill="var(--brand)" stroke="none" />
      <path d="M47 51 L50 57 L53 51" />
    </svg>
  );
}
