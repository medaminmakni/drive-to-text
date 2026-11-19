"use client";

import { useEffect, useMemo, useState } from "react";

import { api, errorMessage } from "@/lib/api";
import type { BatchOptions, Config, FolderListing } from "@/lib/types";
import { useBatch } from "@/lib/useBatch";

import { ActionBar } from "./ActionBar";
import { AppHeader } from "./AppHeader";
import { BatchProgress } from "./BatchProgress";
import styles from "./DriveToText.module.css";
import { ExtractOptions } from "./ExtractOptions";
import { FileTable, FileTableSkeleton } from "./FileTable";
import { FolderForm } from "./FolderForm";
import { ResultList } from "./ResultList";
import { Stepper } from "./Stepper";

/** The whole user flow of the brief on one page: link → select → extract → results. */
export function DriveToText() {
  const [config, setConfig] = useState<Config | null>(null);
  const [configError, setConfigError] = useState<string | null>(null);
  const [listing, setListing] = useState(false);
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

  const files = useMemo(() => folder?.listing.files ?? [], [folder]);
  const chosen = files.filter((file) => selected.has(file.id));
  const chosenBytes = chosen.reduce((sum, file) => sum + (file.size ?? 0), 0);
  const step = batch?.status === "completed" ? 4 : batch || running ? 3 : folder ? 2 : 1;
  const disabledReason =
    chosen.length === 0 ? "select at least one file" : options.lang === "" ? "pick a language" : null;

  function showFolder(next: FolderListing, url: string) {
    setFolder({ listing: next, url });
    setSelected(new Set());
    reset();
  }

  function run() {
    if (!folder) return;
    // Keep the folder order, whatever the order in which the boxes were ticked.
    start({ url: folder.url, file_ids: chosen.map((file) => file.id), ...options });
  }

  return (
    <>
      <AppHeader config={config} backendError={configError} />
      <main className={styles.page}>
        <div className={styles.intro}>
          <h1>Extract text from a Google Drive folder</h1>
          <p>
            Native PDFs are read exactly by the PDF parser. Images and scanned pages go through OCR, with a confidence
            score and review flags.
          </p>
        </div>

        <Stepper current={step} />

        {configError && (
          <p className={styles.banner} role="alert">
            The backend is not reachable ({configError}). Start it with <code>uvicorn app.main:app</code> or{" "}
            <code>docker compose up</code>.
          </p>
        )}

        <section className="card" aria-labelledby="step-link">
          <h2 id="step-link">Folder link</h2>
          <FolderForm onListed={showFolder} onLoading={setListing} disabled={running} />
        </section>

        {(listing || folder) && (
          <section className="card" aria-labelledby="step-files">
            <div className={styles.sectionHead}>
              <h2 id="step-files">
                {folder?.listing.folder_name ? `Files in “${folder.listing.folder_name}”` : "Files"}
              </h2>
              {folder && folder.listing.skipped > 0 && (
                <span className={styles.muted}>{folder.listing.skipped} other item(s) ignored (not PDF or image)</span>
              )}
            </div>
            {listing ? (
              <FileTableSkeleton />
            ) : files.length === 0 ? (
              <p className={styles.empty}>This folder has no PDF or image files.</p>
            ) : (
              <FileTable files={files} selected={selected} disabled={running} onChange={setSelected} />
            )}
          </section>
        )}

        {folder && files.length > 0 && config && (
          <section className="card" aria-labelledby="step-options">
            <h2 id="step-options">Extraction settings</h2>
            <ExtractOptions config={config} options={options} disabled={running} onChange={setOptions} />
          </section>
        )}

        {folder && files.length > 0 && (
          <ActionBar
            count={chosen.length}
            bytes={chosenBytes}
            running={running}
            disabledReason={disabledReason}
            onRun={run}
          />
        )}

        {(batch || batchError) && (
          <section className="card" aria-labelledby="step-results">
            <h2 id="step-results">Results</h2>
            {batchError && (
              <p className={styles.banner} role="alert">
                {batchError}
              </p>
            )}
            {batch && (
              <div className={styles.results}>
                <BatchProgress batch={batch} />
                <ResultList files={batch.files} />
              </div>
            )}
          </section>
        )}
      </main>
      <footer className={styles.footer}>
        Open-source and self-hosted: pypdf · pypdfium2 · Tesseract · FastAPI · Next.js
      </footer>
    </>
  );
}
