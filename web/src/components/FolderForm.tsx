"use client";

import { type FormEvent, useState } from "react";

import { api, errorMessage } from "@/lib/api";
import type { FolderListing } from "@/lib/types";

import styles from "./FolderForm.module.css";
import { FolderIcon, SpinnerIcon } from "./icons";

// Same formats the backend accepts (app/drive/links.py). Checked here too for instant feedback.
const DRIVE_FOLDER = /^(https?:\/\/)?(www\.)?drive\.google\.com\/(drive\/(u\/\d+\/)?folders\/[\w-]{10,}|open\?id=[\w-]{10,})/;

interface Props {
  disabled?: boolean;
  onLoading: (loading: boolean) => void;
  onListed: (listing: FolderListing, url: string) => void;
}

/** Step 1: paste a public Drive folder link. Invalid or private links show a clear error. */
export function FolderForm({ disabled, onLoading, onListed }: Props) {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    const link = url.trim();
    if (!link) return setError("Paste a Google Drive folder link.");
    if (!DRIVE_FOLDER.test(link)) {
      return setError("This doesn't look like a Google Drive folder link (…/drive/folders/…).");
    }
    setLoading(true);
    onLoading(true);
    setError(null);
    try {
      onListed(await api.listFolder(link), link);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
      onLoading(false);
    }
  }

  return (
    <form className={styles.form} onSubmit={submit} noValidate>
      <div className={styles.row}>
        <label className={`${styles.field} ${error ? styles.invalid : ""}`}>
          <span className="visually-hidden">Google Drive folder link</span>
          <FolderIcon className={styles.icon} />
          <input
            type="url"
            inputMode="url"
            autoComplete="off"
            spellCheck={false}
            placeholder="https://drive.google.com/drive/folders/…"
            value={url}
            onChange={(event) => {
              setUrl(event.target.value);
              setError(null);
            }}
            disabled={disabled || loading}
            aria-invalid={Boolean(error)}
            aria-describedby="folder-hint"
          />
        </label>
        <button className="button primary large" type="submit" disabled={disabled || loading}>
          {loading ? <SpinnerIcon /> : null}
          {loading ? "Reading folder" : "List files"}
        </button>
      </div>
      {error ? (
        <p className={styles.error} role="alert" id="folder-hint">
          {error}
        </p>
      ) : (
        <p className={styles.hint} id="folder-hint">
          The folder must be shared as <strong>Anyone with the link</strong>. Only PDF, PNG and JPG files are listed.
        </p>
      )}
    </form>
  );
}
