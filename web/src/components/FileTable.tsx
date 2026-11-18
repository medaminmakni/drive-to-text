"use client";

import { useEffect, useRef } from "react";

import { formatSize } from "@/lib/format";
import type { DriveFile } from "@/lib/types";

import styles from "./FileTable.module.css";

interface Props {
  files: DriveFile[];
  selected: Set<string>;
  disabled?: boolean;
  onToggle: (id: string) => void;
  onToggleAll: (checked: boolean) => void;
}

/** Steps 02 and 03: the PDFs and images of the folder, with individual and "Select all" selection. */
export function FileTable({ files, selected, disabled, onToggle, onToggleAll }: Props) {
  const selectAll = useRef<HTMLInputElement>(null);
  const count = files.filter((file) => selected.has(file.id)).length;
  const all = files.length > 0 && count === files.length;

  // "indeterminate" (half-ticked) can only be set from JavaScript, not as an HTML attribute.
  useEffect(() => {
    if (selectAll.current) selectAll.current.indeterminate = count > 0 && !all;
  }, [count, all]);

  return (
    <div className={styles.wrap}>
      <table className={styles.table}>
        <thead>
          <tr>
            <th className={styles.check}>
              <input
                ref={selectAll}
                type="checkbox"
                aria-label="Select all files"
                checked={all}
                disabled={disabled || files.length === 0}
                onChange={(event) => onToggleAll(event.target.checked)}
              />
            </th>
            <th>Name</th>
            <th>Type</th>
            <th className={styles.num}>Size</th>
          </tr>
        </thead>
        <tbody>
          {files.map((file) => (
            <tr key={file.id} className={selected.has(file.id) ? styles.selected : undefined}>
              <td className={styles.check}>
                <input
                  type="checkbox"
                  aria-label={`Select ${file.name}`}
                  checked={selected.has(file.id)}
                  disabled={disabled}
                  onChange={() => onToggle(file.id)}
                />
              </td>
              <td className={styles.name}>{file.name}</td>
              <td>
                <span className="badge neutral">{file.type.toUpperCase()}</span>
              </td>
              <td className={styles.num}>{formatSize(file.size)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
