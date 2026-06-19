"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

export type Mode = "LITE" | "PRO";

type ModeContextValue = {
  mode: Mode;
  pro: boolean;
  setMode: (mode: Mode) => void;
  /** True once the client has read the persisted preference (avoids SSR flash logic). */
  ready: boolean;
};

const STORAGE_KEY = "vestigo.mode";

const ModeContext = createContext<ModeContextValue | null>(null);

/**
 * Lite / Pro is the core of the Vestigo redesign: Lite answers "what & how sure"
 * with a curated shallow surface; Pro unlocks full analytic depth. The choice is
 * global (persists across routes) and remembered in localStorage. Default = LITE.
 */
export function ModeProvider({ children }: { children: ReactNode }) {
  const [mode, setModeState] = useState<Mode>("LITE");
  const [ready, setReady] = useState(false);

  // Read persisted preference on the client only (server always renders LITE).
  useEffect(() => {
    const saved = window.localStorage.getItem(STORAGE_KEY);
    if (saved === "PRO" || saved === "LITE") setModeState(saved);
    setReady(true);
  }, []);

  const setMode = useCallback((next: Mode) => {
    setModeState(next);
    try {
      window.localStorage.setItem(STORAGE_KEY, next);
    } catch {
      /* localStorage unavailable (private mode) — preference is session-only */
    }
  }, []);

  return (
    <ModeContext.Provider value={{ mode, pro: mode === "PRO", setMode, ready }}>
      {children}
    </ModeContext.Provider>
  );
}

export function useMode(): ModeContextValue {
  const ctx = useContext(ModeContext);
  if (!ctx) {
    throw new Error("useMode must be used within a <ModeProvider>");
  }
  return ctx;
}
