"use client";

import { useEffect, useState } from "react";

import { api, errorMessage } from "@/lib/api";
import type { BatchOptions, Config, FolderListing } from "@/lib/types";
import { useBatch } from "@/lib/useBatch";

import { BatchProgress } from "./BatchProgress";
import styles from "./DriveToText.module.css";
import { ExtractOptions } from "./ExtractOptions";
import { FileTable } from "./FileTable";
import { FolderForm } from "./FolderForm";
import { ResultList } from "./ResultList";

/** The whole user flow of the brief on one page: link → list → select → run → results. */
export function DriveToText() {
  const [config, setConfig] = useState<Config | null>(null);
  const [configError, setConfigError] = useState<string | null>(null);
  const [folder, setFolder] = useState<{ listing: FolderListing; url: string } | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [options, setOptions] = useState<BatchOptions>({ lang: "eng", page_mode: "auto", engine: "tesseract" });
  const { batch, error: batchError, running, start, reset } = useBatch();

  useEffect(() => {
    api
      .config()
      .then((loaded) => {
        setConfig(loaded);
        setOptions({ lang: loaded.default_language, page_mode: "auto", engine: loaded.default_engine });
      })
      .catch((err) => setConfigError(errorMessage(err)));
  }, []);

  function showFolder(listing: FolderListing, url: string) {
    setFolder({ listing, url });
    setSelected(new Set());
    reset();
  }

  function toggle(id: string) {
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function toggleAll(checked: boolean) {
    setSelected(checked && folder ? new Set(folder.listing.files.map((file) => file.id)) : new Set());
  }

  function run() {
    if (!folder) return;
    // Keep the folder order, whatever the order in which the boxes were ticked.
    const fileIds = folder.listing.files.filter((file) => selected.has(file.id)).map((file) => file.id);
    start({ url: folder.url, file_ids: fileIds, ...options });
  }

  const files = folder?.listing.files ?? [];
  const canRun = selected.size > 0 && options.lang !== "" && !running;

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <h1>Drive-to-Text</h1>
        <p>Paste a public Google Drive folder link, choose the PDFs and images, and extract their text.</p>
      </header>

      {configError && (
        <p className={styles.banner} role="alert">
          Backend not reachable: {configError}
        </p>
      )}

      <section className="card" aria-labelledby="step-1">
        <h2 id="step-1">
          <span className="step">1</span> Folder link
        </h2>
        <FolderForm onListed={showFolder} disabled={running} />
      </section>

      {folder && (
        <section className="card" aria-labelledby="step-2">
          <div className={styles.sectionHead}>
            <h2 id="step-2">
              <span className="step">2</span> Select files
            </h2>
            <span className="badge neutral" aria-live="polite">
              {selected.size} of {files.length} selected
            </span>
          </div>
          <p className={styles.muted}>
            {folder.listing.folder_name ? `“${folder.listing.folder_name}”` : "This folder"}:{" "}
            {files.length ? `${files.length} PDF or image file(s).` : "no PDF or image files."}
            {folder.listing.skipped > 0 && ` ${folder.listing.skipped} other item(s) ignored (not a PDF or image).`}
          </p>
          {files.length > 0 && (
            <>
              <FileTable
                files={files}
                selected={selected}
                disabled={running}
                onToggle={toggle}
                onToggleAll={toggleAll}
              />
              {config && (
                <ExtractOptions config={config} options={options} disabled={running} onChange={setOptions} />
              )}
              <div className={styles.actions}>
                <button type="button" className="button primary" onClick={run} disabled={!canRun}>
                  {running ? "Processing…" : `Extract text (${selected.size})`}
                </button>
              </div>
            </>
          )}
        </section>
      )}

      {(batch || batchError) && (
        <section className="card" aria-labelledby="step-3">
          <h2 id="step-3">
            <span className="step">3</span> Results
          </h2>
          {batchError && (
            <p className={styles.banner} role="alert">
              {batchError}
            </p>
          )}
          {batch && (
            <>
              <BatchProgress batch={batch} />
              <ResultList files={batch.files} />
            </>
          )}
        </section>
      )}
    </main>
  );
}
