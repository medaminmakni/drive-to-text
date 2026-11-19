"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { formatSize } from "@/lib/format";
import type { DriveFile } from "@/lib/types";

import styles from "./FileTable.module.css";
import { ImageIcon, PdfIcon, SearchIcon } from "./icons";

interface Props {
  files: DriveFile[];
  selected: Set<string>;
  disabled?: boolean;
  onChange: (selected: Set<string>) => void;
}

/** Step 2: the folder's PDFs and images. Search, select one by one or all, see the totals. */
export function FileTable({ files, selected, disabled, onChange }: Props) {
  const [query, setQuery] = useState("");
  const selectAll = useRef<HTMLInputElement>(null);

  const visible = useMemo(
    () => files.filter((file) => file.name.toLowerCase().includes(query.trim().toLowerCase())),
    [files, query],
  );
  const visibleSelected = visible.filter((file) => selected.has(file.id)).length;
  const allVisible = visible.length > 0 && visibleSelected === visible.length;
  const pdfs = files.filter((file) => file.type === "pdf").length;
  const totalSize = files.reduce((sum, file) => sum + (file.size ?? 0), 0);

  // The half-ticked state can only be set from JavaScript, not as an HTML attribute.
  useEffect(() => {
    if (selectAll.current) selectAll.current.indeterminate = visibleSelected > 0 && !allVisible;
  }, [visibleSelected, allVisible]);

  function toggle(id: string) {
    const next = new Set(selected);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    onChange(next);
  }

  function toggleVisible(checked: boolean) {
    const next = new Set(selected);
    for (const file of visible) {
      if (checked) next.add(file.id);
      else next.delete(file.id);
    }
    onChange(next);
  }

  return (
    <div className={styles.wrap}>
      <div className={styles.toolbar}>
        <p className={styles.summary}>
          <strong>{files.length}</strong> file(s) · {pdfs} PDF · {files.length - pdfs} image(s) · {formatSize(totalSize)}
        </p>
        <label className={styles.search}>
          <span className="visually-hidden">Filter files by name</span>
          <SearchIcon size={16} />
          <input
            type="search"
            placeholder="Filter by name"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </label>
        {selected.size > 0 && (
          <button type="button" className="button ghost small" onClick={() => onChange(new Set())} disabled={disabled}>
            Clear selection
          </button>
        )}
      </div>

      <div className={styles.tableWrap}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th className={styles.check}>
                <input
                  ref={selectAll}
                  type="checkbox"
                  aria-label="Select all files shown"
                  checked={allVisible}
                  disabled={disabled || visible.length === 0}
                  onChange={(event) => toggleVisible(event.target.checked)}
                />
              </th>
              <th>Name</th>
              <th>Type</th>
              <th className={styles.num}>Size</th>
            </tr>
          </thead>
          <tbody>
            {visible.map((file) => {
              const isSelected = selected.has(file.id);
              return (
                <tr
                  key={file.id}
                  className={isSelected ? styles.selected : undefined}
                  onClick={() => !disabled && toggle(file.id)}
                >
                  <td className={styles.check}>
                    <input
                      type="checkbox"
                      aria-label={`Select ${file.name}`}
                      checked={isSelected}
                      disabled={disabled}
                      onClick={(event) => event.stopPropagation()}
                      onChange={() => toggle(file.id)}
                    />
                  </td>
                  <td>
                    <span className={styles.name}>
                      <span className={`${styles.fileIcon} ${file.type === "pdf" ? styles.pdf : styles.image}`}>
                        {file.type === "pdf" ? <PdfIcon size={16} /> : <ImageIcon size={16} />}
                      </span>
                      {file.name}
                    </span>
                  </td>
                  <td>
                    <span className="tag">{file.type.toUpperCase()}</span>
                  </td>
                  <td className={styles.num}>{formatSize(file.size)}</td>
                </tr>
              );
            })}
            {visible.length === 0 && (
              <tr>
                <td colSpan={4} className={styles.empty}>
                  No file matches “{query}”.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/** Placeholder rows shown while the folder is being read. */
export function FileTableSkeleton() {
  return (
    <div className={styles.tableWrap} aria-busy="true" aria-label="Loading files">
      {[0, 1, 2, 3].map((row) => (
        <div key={row} className={styles.skeletonRow}>
          <span className="skeleton" style={{ width: 18 }} />
          <span className="skeleton" style={{ width: `${40 + row * 10}%` }} />
          <span className="skeleton" style={{ width: 48, marginLeft: "auto" }} />
        </div>
      ))}
    </div>
  );
}
