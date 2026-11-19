import { formatSize } from "@/lib/format";

import styles from "./ActionBar.module.css";
import { ArrowIcon, SpinnerIcon } from "./icons";

interface Props {
  count: number;
  bytes: number;
  running: boolean;
  disabledReason: string | null;
  onRun: () => void;
}

/** Always-visible bar with the selection summary and the main action. */
export function ActionBar({ count, bytes, running, disabledReason, onRun }: Props) {
  return (
    <div className={styles.bar}>
      <p className={styles.text}>
        {count > 0 ? (
          <>
            <strong>{count}</strong> file(s) selected · {formatSize(bytes)}
          </>
        ) : (
          "No file selected"
        )}
        {disabledReason && !running && <span className={styles.reason}> · {disabledReason}</span>}
      </p>
      <button
        type="button"
        className="button primary large"
        onClick={onRun}
        disabled={running || disabledReason !== null}
      >
        {running ? <SpinnerIcon /> : null}
        {running ? "Processing" : "Extract text"}
        {!running && <ArrowIcon size={16} />}
      </button>
    </div>
  );
}
