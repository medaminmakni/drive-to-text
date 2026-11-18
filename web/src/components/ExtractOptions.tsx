"use client";

import type { BatchOptions, Config } from "@/lib/types";

import styles from "./ExtractOptions.module.css";
import { AlertIcon, CheckIcon } from "./icons";

interface Props {
  config: Config;
  options: BatchOptions;
  disabled?: boolean;
  onChange: (options: BatchOptions) => void;
}

const ENGINE_INFO: Record<string, { title: string; text: string; tags: string[] }> = {
  tesseract: {
    title: "Tesseract",
    text: "Open-source OCR. Fast on CPU, reads Arabic, French and English, gives a confidence score.",
    tags: ["Default", "Fast"],
  },
  "glm-ocr": {
    title: "GLM-OCR (AI)",
    text: "Vision model via Ollama. Strong on French/English layouts, slower, no confidence score.",
    tags: ["AI", "Not for Arabic"],
  },
};

/** OCR settings, used for images and scanned pages. Native PDF pages are read exactly by the parser. */
export function ExtractOptions({ config, options, disabled, onChange }: Props) {
  const languages = options.lang ? options.lang.split("+") : [];
  const engine = config.engines.find((item) => item.name === options.engine);
  const arabicRisk = languages.includes("ara") && engine && !engine.reliable_for_arabic;
  const simpleLayout = options.page_mode === "single_block";
  const missing = config.languages.filter((item) => !item.installed).map((item) => item.label);

  function toggleLanguage(code: string) {
    const next = languages.includes(code) ? languages.filter((item) => item !== code) : [...languages, code];
    // Keep the order of the config list, so the same choice is always written the same way.
    const ordered = config.languages.map((item) => item.code).filter((item) => next.includes(item));
    onChange({ ...options, lang: ordered.join("+") });
  }

  return (
    <div className={styles.options}>
      <section className={styles.block}>
        <h3>Document language</h3>
        <div className={styles.pills} role="group" aria-label="OCR languages">
          {config.languages.map((language) => {
            const on = languages.includes(language.code);
            return (
              <button
                key={language.code}
                type="button"
                className={`${styles.pill} ${on ? styles.pillOn : ""} ${language.installed ? "" : styles.pillMissing}`}
                aria-pressed={on}
                disabled={disabled || !language.installed}
                title={language.installed ? undefined : "Not installed in Tesseract on the server"}
                onClick={() => toggleLanguage(language.code)}
              >
                {on && <CheckIcon size={14} />}
                {language.label}
                {!language.installed && <span className={styles.pillHint}>not installed</span>}
              </button>
            );
          })}
        </div>
        <p className={styles.note}>
          {languages.length === 0 ? "Pick at least one language." : "Pick every language that appears in the documents."}
        </p>
        {missing.length > 0 && (
          <p className={styles.missing}>
            <AlertIcon size={14} />
            <span>
              {missing.join(" and ")} {missing.length === 1 ? "is" : "are"} not installed in Tesseract on the server.
              See README, <strong>OCR languages</strong>.
            </span>
          </p>
        )}
      </section>

      <section className={styles.block}>
        <h3>Layout</h3>
        <button
          type="button"
          role="switch"
          aria-checked={simpleLayout}
          className={styles.switchRow}
          disabled={disabled}
          onClick={() => onChange({ ...options, page_mode: simpleLayout ? "auto" : "single_block" })}
        >
          <span className={`${styles.switch} ${simpleLayout ? styles.switchOn : ""}`}>
            <span className={styles.knob} />
          </span>
          <span>
            <strong>Simple layout (one column)</strong>
            <span className={styles.note}>
              For forms, letters and certificates, especially with Arabic and French mixed. Leave off for multi-column
              pages.
            </span>
          </span>
        </button>
      </section>

      <section className={`${styles.block} ${styles.full}`}>
        <h3>OCR engine</h3>
        <div className={styles.engines} role="radiogroup" aria-label="OCR engine">
          {config.engines.map((item) => {
            const info = ENGINE_INFO[item.name] ?? { title: item.name, text: item.label, tags: [] };
            const checked = options.engine === item.name;
            return (
              <label
                key={item.name}
                className={`${styles.engine} ${checked ? styles.engineOn : ""} ${item.available ? "" : styles.engineOff}`}
              >
                <input
                  type="radio"
                  name="engine"
                  className="visually-hidden"
                  checked={checked}
                  disabled={disabled || !item.available}
                  onChange={() => onChange({ ...options, engine: item.name })}
                />
                <span className={styles.engineHead}>
                  <strong>{info.title}</strong>
                  <span className={styles.radio} />
                </span>
                <span className={styles.note}>{info.text}</span>
                <span className={styles.tags}>
                  {(item.available ? info.tags : ["Not installed"]).map((tag) => (
                    <span key={tag} className="tag">
                      {tag}
                    </span>
                  ))}
                </span>
                {!item.available && (
                  <span className={styles.note}>
                    Install Ollama, then run <code>ollama pull {item.name}</code>.
                  </span>
                )}
              </label>
            );
          })}
        </div>
      </section>

      {arabicRisk && (
        <p className={styles.warning} role="status">
          <AlertIcon size={16} />
          This AI engine can invent Arabic text that is not on the page (measured in our benchmark). Its Arabic pages
          will be flagged for review. Tesseract is safer for Arabic.
        </p>
      )}
    </div>
  );
}
