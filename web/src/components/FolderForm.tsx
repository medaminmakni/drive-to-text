"use client";

import { type FormEvent, useState } from "react";

import { api, errorMessage } from "@/lib/api";
import type { FolderListing } from "@/lib/types";

import styles from "./FolderForm.module.css";

interface Props {
  disabled?: boolean;
  onListed: (listing: FolderListing, url: string) => void;
}

/** Step 01: paste a public Drive folder link. Invalid or private links show a clear error. */
export function FolderForm({ disabled, onListed }: Props) {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    const link = url.trim();
    if (!link) {
      setError("Please paste a Google Drive folder link.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      onListed(await api.listFolder(link), link);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className={styles.form} onSubmit={submit} noValidate>
      <label htmlFor="folder-url" className="visually-hidden">
        Google Drive folder link
      </label>
      <input
        id="folder-url"
        className={styles.input}
        type="url"
        inputMode="url"
        autoComplete="off"
        placeholder="https://drive.google.com/drive/folders/..."
        value={url}
        onChange={(event) => setUrl(event.target.value)}
        disabled={disabled || loading}
      />
      <button className="button primary" type="submit" disabled={disabled || loading}>
        {loading ? "Reading folder…" : "List files"}
      </button>
      {error && (
        <p className={styles.error} role="alert">
          {error}
        </p>
      )}
    </form>
  );
}
