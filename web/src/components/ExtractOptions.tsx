"use client";

import type { BatchOptions, Config } from "@/lib/types";

import styles from "./ExtractOptions.module.css";

interface Props {
  config: Config;
  options: BatchOptions;
  disabled?: boolean;
  onChange: (options: BatchOptions) => void;
}

/** OCR settings: languages, layout and engine. Only used for images and scanned pages. */
export function ExtractOptions({ config, options, disabled, onChange }: Props) {
  const languages = options.lang ? options.lang.split("+") : [];
  const engine = config.engines.find((item) => item.name === options.engine);
  const arabicRisk = languages.includes("ara") && engine && !engine.reliable_for_arabic;

  function toggleLanguage(code: string) {
    const next = languages.includes(code) ? languages.filter((item) => item !== code) : [...languages, code];
    // Keep the order of the config list so "ara+fra" is always written the same way.
    const ordered = config.languages.map((item) => item.code).filter((item) => next.includes(item));
    onChange({ ...options, lang: ordered.join("+") });
  }

  return (
    <fieldset className={styles.options} disabled={disabled}>
      <legend className="visually-hidden">OCR options</legend>

      <div className={styles.group}>
        <span className={styles.title}>OCR languages</span>
        {config.languages.map((language) => (
          <label key={language.code} className={styles.choice}>
            <input
              type="checkbox"
              checked={languages.includes(language.code)}
              onChange={() => toggleLanguage(language.code)}
            />
            {language.label}
          </label>
        ))}
        {languages.length === 0 && <span className={styles.hint}>Pick at least one language.</span>}
      </div>

      <div className={styles.group}>
        <span className={styles.title}>Layout</span>
        <label className={styles.choice}>
          <input
            type="checkbox"
            checked={options.page_mode === "single_block"}
            onChange={(event) => onChange({ ...options, page_mode: event.target.checked ? "single_block" : "auto" })}
          />
          Simple layout (one column): forms, letters, certificates
        </label>
      </div>

      <div className={styles.group}>
        <span className={styles.title}>OCR engine</span>
        {config.engines.map((item) => (
          <label key={item.name} className={styles.choice} title={item.label}>
            <input
              type="radio"
              name="engine"
              value={item.name}
              checked={options.engine === item.name}
              disabled={!item.available}
              onChange={() => onChange({ ...options, engine: item.name })}
            />
            {item.label}
            {!item.available && (
              <span className={styles.hint}>
                not installed: run <code>ollama pull {item.name}</code>
              </span>
            )}
          </label>
        ))}
      </div>

      {arabicRisk && (
        <p className={styles.warning} role="status">
          This AI engine can invent Arabic text that is not on the page (measured in our benchmark). Its Arabic pages
          will be flagged for review. Tesseract is safer for Arabic.
        </p>
      )}
    </fieldset>
  );
}
