// JSON shapes shared with the backend. Source of truth: docs/API.md.

export type FileStatus = "pending" | "processing" | "done" | "failed";
export type Method = "pdf_parser" | "ocr" | "pdf_parser+ocr";
export type PageMode = "auto" | "single_block";
export type ReviewReason = "low_confidence" | "no_text" | "ai_ocr_arabic";

export interface Engine {
  name: string;
  label: string;
  available: boolean;
  reliable_for_arabic: boolean;
}

export interface Config {
  engines: Engine[];
  default_engine: string;
  /** installed: false when Tesseract on the server has no model for it (shown greyed out). */
  languages: { code: string; label: string; installed: boolean }[];
  default_language: string;
  page_modes: { value: PageMode; label: string }[];
  max_file_size_mb: number;
}

export interface DriveFile {
  id: string;
  name: string;
  mime_type: string;
  type: string;
  size: number | null;
}

export interface FolderListing {
  folder_id: string;
  folder_name: string | null;
  skipped: number;
  files: DriveFile[];
}

export interface PageResult {
  number: number;
  method: Method;
  confidence: number | null;
  needs_review: boolean;
  review_reason: ReviewReason | null;
  text: string;
}

export interface ExtractionResult {
  method: Method;
  ocr_engine: string | null;
  confidence: number | null;
  needs_review: boolean;
  pages_count: number;
  warnings: string[];
  text: string;
  pages: PageResult[];
}

export interface BatchOptions {
  lang: string;
  page_mode: PageMode;
  engine: string;
}

export interface BatchFile {
  id: string;
  name: string;
  type: string;
  size: number | null;
  status: FileStatus;
  error: string | null;
  duration_ms: number | null;
  result: ExtractionResult | null;
}

export interface Batch {
  batch_id: string;
  folder_id: string;
  folder_name: string | null;
  created_at: string;
  options: BatchOptions;
  status: "running" | "completed";
  counts: Record<FileStatus, number>;
  files: BatchFile[];
}

export interface BatchRequest extends BatchOptions {
  url: string;
  file_ids: string[];
}
