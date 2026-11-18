import type { Config } from "@/lib/types";

import styles from "./AppHeader.module.css";
import { LogoMark } from "./LogoMark";

interface Props {
  config: Config | null;
  backendError: string | null;
}

/** Product header with live status: is the backend up, which OCR engines are ready. */
export function AppHeader({ config, backendError }: Props) {
  const backend = backendError ? "down" : config ? "up" : "checking";
  const backendLabel = { up: "Backend connected", down: "Backend unreachable", checking: "Connecting…" }[backend];

  return (
    <header className={styles.header}>
      <div className={styles.brand}>
        <LogoMark size={36} />
        <div>
          <p className={styles.name}>Drive-to-Text</p>
          <p className={styles.tagline}>Document extraction from Google Drive</p>
        </div>
      </div>
      <div className={styles.status} aria-live="polite">
        <span className={`${styles.chip} ${styles[backend]}`}>
          <span className={styles.dot} />
          {backendLabel}
        </span>
        {config?.engines.map((engine) => (
          <span key={engine.name} className={`${styles.chip} ${engine.available ? styles.up : styles.off}`}>
            <span className={styles.dot} />
            {engine.name}
          </span>
        ))}
      </div>
    </header>
  );
}
