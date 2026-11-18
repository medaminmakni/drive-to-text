"use client";

import { useState } from "react";

import { formatDuration, METHOD_LABEL, REVIEW_LABEL, STATUS_LABEL } from "@/lib/format";
import type { BatchFile } from "@/lib/types";

import styles from "./ResultList.module.css";

/** Steps 04 and 05: one card per file with its status, then its text, method and review flags. */
export function ResultList({ files }: { files: BatchFile[] }) {
  return (
    <div className={styles.list}>
      {files.map((file) => (
        <ResultCard key={file.id} file={file} />
      ))}
    </div>
  );
}

function ResultCard({ file }: { file: BatchFile }) {
  const result = file.result;
  const reasons = result ? [...new Set(result.pages.map((page) => page.review_reason).filter(Boolean))] : [];

  return (
    <details className={styles.card}>
      <summary className={styles.summary}>
        <span className={`badge ${file.status}`}>{STATUS_LABEL[file.status]}</span>
        <span className={styles.name}>{file.name}</span>
        {result && <span className="badge accent">{METHOD_LABEL[result.method]}</span>}
        {result?.needs_review && <span className="badge warn">Needs review</span>}
        <span className={styles.meta}>
          {result && `${result.pages_count} page(s)`}
          {result?.confidence != null && ` · confidence ${Math.round(result.confidence)}%`}
          {file.duration_ms != null && ` · ${formatDuration(file.duration_ms)}`}
        </span>
      </summary>

      <div className={styles.body}>
        {file.status === "failed" && <p className={styles.error}>{file.error}</p>}
        {(file.status === "pending" || file.status === "processing") && (
          <p className={styles.muted}>{file.status === "pending" ? "Waiting for a free worker…" : "Reading this file…"}</p>
        )}
        {result && (
          <>
            {result.warnings.map((warning) => (
              <p key={warning} className={styles.warning}>
                {warning}
              </p>
            ))}
            {reasons.length > 0 && (
              <p className={styles.warning}>
                Review: {reasons.map((reason) => REVIEW_LABEL[reason!]).join(", ")}
              </p>
            )}
            <TextBlock text={result.text} />
            {result.pages_count > 1 && (
              <ul className={styles.pages}>
                {result.pages.map((page) => (
                  <li key={page.number}>
                    Page {page.number}: {METHOD_LABEL[page.method]}
                    {page.confidence != null && `, confidence ${Math.round(page.confidence)}%`}
                    {page.review_reason && ` · ${REVIEW_LABEL[page.review_reason]}`}
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
      </div>
    </details>
  );
}

function TextBlock({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  if (!text) return <p className={styles.muted}>No text found in this file.</p>;
  return (
    <div className={styles.text}>
      <button type="button" className="button small" onClick={copy}>
        {copied ? "Copied" : "Copy text"}
      </button>
      {/* dir="auto" lets each paragraph pick its own direction: Arabic right to left, French left to right. */}
      <pre dir="auto">{text}</pre>
    </div>
  );
}
