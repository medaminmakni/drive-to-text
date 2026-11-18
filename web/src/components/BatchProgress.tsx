import { api } from "@/lib/api";
import type { Batch } from "@/lib/types";

import styles from "./BatchProgress.module.css";

/** Step 04: overall progress of the batch, and the JSON export once it is finished. */
export function BatchProgress({ batch }: { batch: Batch }) {
  const { done, failed, processing, pending } = batch.counts;
  const total = batch.files.length;
  const finished = done + failed;
  const percent = total ? Math.round((finished / total) * 100) : 0;
  const completed = batch.status === "completed";

  return (
    <div className={styles.progress}>
      <div className={styles.head}>
        <p className={styles.summary} aria-live="polite">
          {completed
            ? `Finished: ${done} done, ${failed} failed, out of ${total} file(s).`
            : `Processing ${finished}/${total}… (${processing} running, ${pending} waiting)`}
        </p>
        {completed && (
          <a className="button" href={api.exportUrl(batch.batch_id)} download>
            Export JSON
          </a>
        )}
      </div>
      <div className={styles.bar} role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={percent}>
        <div className={styles.fill} style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}
