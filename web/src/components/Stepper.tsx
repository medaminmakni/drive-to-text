import styles from "./Stepper.module.css";
import { CheckIcon } from "./icons";

const STEPS = ["Folder link", "Select files", "Extract", "Results"];

/** Where the user is in the flow. `current` is 1-based. */
export function Stepper({ current }: { current: number }) {
  return (
    <ol className={styles.stepper} aria-label="Progress">
      {STEPS.map((label, index) => {
        const number = index + 1;
        const state = number < current ? "done" : number === current ? "active" : "todo";
        return (
          <li key={label} className={`${styles.step} ${styles[state]}`} aria-current={state === "active" ? "step" : undefined}>
            <span className={styles.marker}>{state === "done" ? <CheckIcon size={14} /> : number}</span>
            <span className={styles.label}>{label}</span>
          </li>
        );
      })}
    </ol>
  );
}
