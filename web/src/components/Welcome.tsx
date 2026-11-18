"use client";

import { useEffect, useState } from "react";

import { WELCOME_KEY } from "@/lib/welcome";

import { LOGO } from "./LogoMark";
import styles from "./Welcome.module.css";

type Phase = "playing" | "leaving" | "done";

/** Short brand animation over the app on first open. Click or Esc skips it. */
export function Welcome() {
  const [phase, setPhase] = useState<Phase>("playing");

  useEffect(() => {
    try {
      sessionStorage.setItem(WELCOME_KEY, "1");
    } catch {
      // Storage blocked (private mode): the animation simply plays again next time.
    }
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setPhase("leaving");
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  if (phase === "done") return null;

  return (
    <div
      className={`${styles.overlay} ${phase === "leaving" ? styles.leaving : ""}`}
      aria-hidden="true"
      onClick={() => setPhase("leaving")}
      onAnimationEnd={(event) => {
        // Only the overlay's own fade-out ends the animation, not its children's.
        if (event.target === event.currentTarget) setPhase("done");
      }}
    >
      <div className={styles.content}>
        <svg className={styles.mark} width="112" height="112" viewBox="0 0 64 64">
          <rect width="64" height="64" rx="16" fill="var(--brand)" />
          <g fill="none" stroke="#fff" strokeWidth={3.5} strokeLinecap="round" strokeLinejoin="round">
            <path className={styles.folder} pathLength={1} d={LOGO.folder} />
            <path className={styles.line1} pathLength={1} d={LOGO.line1} />
            <path className={styles.line2} pathLength={1} d={LOGO.line2} />
          </g>
          <rect className={styles.beam} x="9" y="14" width="46" height="2.5" rx="1.25" />
        </svg>
        <p className={styles.name}>Drive-to-Text</p>
        <p className={styles.tagline}>Document extraction from Google Drive</p>
      </div>
    </div>
  );
}
