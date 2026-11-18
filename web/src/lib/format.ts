import type { FileStatus, Method, ReviewReason } from "./types";

export function formatSize(bytes: number | null): string {
  if (bytes == null) return "unknown";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatDuration(ms: number | null): string {
  if (ms == null) return "";
  return ms < 1000 ? `${ms} ms` : `${(ms / 1000).toFixed(1)} s`;
}

export const METHOD_LABEL: Record<Method, string> = {
  pdf_parser: "PDF parser",
  ocr: "OCR",
  "pdf_parser+ocr": "PDF parser + OCR",
};

export const STATUS_LABEL: Record<FileStatus, string> = {
  pending: "Pending",
  processing: "Processing",
  done: "Done",
  failed: "Failed",
};

export const REVIEW_LABEL: Record<ReviewReason, string> = {
  low_confidence: "Low OCR confidence",
  no_text: "No text found",
  ai_ocr_arabic: "AI OCR on Arabic: may invent text",
};
