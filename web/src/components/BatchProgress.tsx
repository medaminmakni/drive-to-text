import { api } from "@/lib/api";
import { formatDuration } from "@/lib/format";
import type { Batch } from "@/lib/types";

import styles from "./BatchProgress.module.css";
import { AlertIcon, CheckIcon, ClockIcon, CrossIcon, DownloadIcon } from "./icons";

/** Batch overview: counters, progress bar while running, JSON export when finished. */
export function BatchProgress({ batch }: { batch: Batch }) {
  const { done, failed } = batch.counts;
  const total = batch.files.length;
  const finished = done + failed;
  const percent = total ? Math.round((finished / total) * 100) : 0;
  const completed = batch.status === "completed";
  const review = batch.files.filter((file) => file.result?.needs_review).length;
  const durations = batch.files.map((file) => file.duration_ms).filter((ms): ms is number => ms != null);
  const average = durations.length ? Math.round(durations.reduce((a, b) => a + b, 0) / durations.length) : null;

  const tiles = [
    { label: "Done", value: done, icon: <CheckIcon size={16} />, tone: styles.ok },
    { label: "Failed", value: failed, icon: <CrossIcon size={16} />, tone: styles.fail },
    { label: "Needs review", value: review, icon: <AlertIcon size={16} />, tone: styles.warn },
    { label: "Avg time / file", value: average != null ? formatDuration(average) : "–", icon: <ClockIcon size={16} />, tone: styles.neutral },
  ];

  return (
    <div className={styles.wrap}>
      <div className={styles.tiles}>
        {tiles.map((tile) => (
          <div key={tile.label} className={`${styles.tile} ${tile.tone}`}>
            <span className={styles.tileIcon}>{tile.icon}</span>
            <span className={styles.value}>{tile.value}</span>
            <span className={styles.label}>{tile.label}</span>
          </div>
        ))}
      </div>

      <div className={styles.progressRow}>
        <div
          className={`${styles.bar} ${completed ? "" : styles.running}`}
          role="progressbar"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={percent}
          aria-label="Batch progress"
        >
          <div className={styles.fill} style={{ width: `${Math.max(percent, completed ? 100 : 4)}%` }} />
        </div>
        <span className={styles.percent} aria-live="polite">
          {completed ? `${finished}/${total} processed` : `${finished}/${total} · ${percent}%`}
        </span>
        <a
          className={`button ${completed ? "primary" : ""}`}
          href={completed ? api.exportUrl(batch.batch_id) : undefined}
          aria-disabled={!completed}
          download
        >
          <DownloadIcon size={16} />
          Export JSON
        </a>
      </div>
    </div>
  );
}
