/**
 * Brand mark (concept A, "Folder to text"): a folder that holds lines of text.
 * The same drawing is used by the header, the welcome animation and src/app/icon.svg.
 */
export const LOGO = {
  folder: "M14 22a4 4 0 0 1 4-4h9l4 4h15a4 4 0 0 1 4 4v16a4 4 0 0 1-4 4H18a4 4 0 0 1-4-4z",
  line1: "M21 31h22",
  line2: "M21 38h13",
};

export function LogoMark({ size = 36 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" aria-hidden="true">
      <rect width="64" height="64" rx="16" fill="var(--brand)" />
      <g fill="none" stroke="#fff" strokeWidth={3.5} strokeLinecap="round" strokeLinejoin="round">
        <path d={LOGO.folder} />
        <path d={`${LOGO.line1}M${LOGO.line2.slice(1)}`} />
      </g>
    </svg>
  );
}
