"use client";

import { useState } from "react";

import { formatDuration, METHOD_LABEL, REVIEW_LABEL, STATUS_LABEL } from "@/lib/format";
import type { BatchFile, ExtractionResult } from "@/lib/types";

import styles from "./ResultList.module.css";
import { AlertIcon, CheckIcon, ChevronIcon, ClockIcon, CopyIcon, CrossIcon, DownloadIcon, SpinnerIcon } from "./icons";

/** One row per file: live status, then method, confidence, review flag and the extracted text. */
export function ResultList({ files }: { files: BatchFile[] }) {
  return (
    <ul className={styles.list}>
      {files.map((file) => (
        <ResultRow key={file.id} file={file} />
      ))}
    </ul>
  );
}

const STATUS_ICON = {
  pending: <ClockIcon size={16} />,
  processing: <SpinnerIcon size={16} />,
  done: <CheckIcon size={16} />,
  failed: <CrossIcon size={16} />,
};

function ResultRow({ file }: { file: BatchFile }) {
  const [open, setOpen] = useState(false);
  const result = file.result;
  const canOpen = file.status === "done" || file.status === "failed";

  return (
    <li className={`${styles.row} ${open ? styles.open : ""}`}>
      <button
        type="button"
        className={styles.head}
        onClick={() => setOpen(!open)}
        disabled={!canOpen}
        aria-expanded={open}
      >
        <span className={`${styles.status} ${styles[file.status]}`} title={STATUS_LABEL[file.status]}>
          {STATUS_ICON[file.status]}
        </span>
        <span className={styles.title}>
          <span className={styles.name}>{file.name}</span>
          <span className={styles.sub}>
            {STATUS_LABEL[file.status]}
            {result && ` · ${result.pages_count} page(s)`}
            {file.duration_ms != null && ` · ${formatDuration(file.duration_ms)}`}
          </span>
        </span>
        <span className={styles.badges}>
          {result && <span className="tag accent">{METHOD_LABEL[result.method]}</span>}
          {result?.needs_review && (
            <span className="tag warn">
              <AlertIcon size={12} /> Needs review
            </span>
          )}
          {result && <ConfidenceMeter value={result.confidence} />}
        </span>
        {canOpen && <ChevronIcon className={styles.chevron} />}
      </button>

      {open && (
        <div className={styles.body}>
          {file.status === "failed" && <p className={styles.error}>{file.error}</p>}
          {result && <ResultDetails name={file.name} result={result} />}
        </div>
      )}
    </li>
  );
}

/** Green from 85%, orange from 70% (the default review threshold), red below. */
function ConfidenceMeter({ value }: { value: number | null }) {
  if (value == null) return <span className={styles.noScore}>no score</span>;
  const tone = value >= 85 ? styles.high : value >= 70 ? styles.medium : styles.low;
  return (
    <span className={`${styles.meter} ${tone}`} title="Lowest OCR confidence among the pages">
      <span className={styles.meterTrack}>
        <span className={styles.meterFill} style={{ width: `${value}%` }} />
      </span>
      {Math.round(value)}%
    </span>
  );
}

function ResultDetails({ name, result }: { name: string; result: ExtractionResult }) {
  const [tab, setTab] = useState<"text" | "pages">("text");
  const [copied, setCopied] = useState(false);
  const reasons = [...new Set(result.pages.flatMap((page) => (page.review_reason ? [page.review_reason] : [])))];

  async function copy() {
    await navigator.clipboard.writeText(result.text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  function download() {
    const url = URL.createObjectURL(new Blob([result.text], { type: "text/plain;charset=utf-8" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = `${name.replace(/\.[^.]+$/, "")}.txt`;
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <>
      {[...result.warnings, ...(reasons.length ? [`Review: ${reasons.map((r) => REVIEW_LABEL[r]).join(", ")}.`] : [])].map(
        (message) => (
          <p key={message} className={styles.warning}>
            <AlertIcon size={14} /> {message}
          </p>
        ),
      )}

      <div className={styles.toolbar}>
        <div className={styles.tabs} role="tablist">
          <button type="button" role="tab" aria-selected={tab === "text"} onClick={() => setTab("text")}>
            Text
          </button>
          <button type="button" role="tab" aria-selected={tab === "pages"} onClick={() => setTab("pages")}>
            Pages ({result.pages_count})
          </button>
        </div>
        <div className={styles.actions}>
          <button type="button" className="button ghost small" onClick={copy} disabled={!result.text}>
            <CopyIcon size={14} /> {copied ? "Copied" : "Copy"}
          </button>
          <button type="button" className="button ghost small" onClick={download} disabled={!result.text}>
            <DownloadIcon size={14} /> .txt
          </button>
        </div>
      </div>

      {tab === "text" ? (
        result.text ? (
          // dir="auto": each paragraph picks its own direction (Arabic right to left, French left to right).
          <pre className={styles.text} dir="auto">
            {result.text}
          </pre>
        ) : (
          <p className={styles.muted}>No text found in this file.</p>
        )
      ) : (
        <table className={styles.pages}>
          <thead>
            <tr>
              <th>Page</th>
              <th>Method</th>
              <th>Confidence</th>
              <th>Review</th>
            </tr>
          </thead>
          <tbody>
            {result.pages.map((page) => (
              <tr key={page.number}>
                <td>{page.number}</td>
                <td>{METHOD_LABEL[page.method]}</td>
                <td>
                  <ConfidenceMeter value={page.confidence} />
                </td>
                <td>{page.review_reason ? REVIEW_LABEL[page.review_reason] : "–"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}
