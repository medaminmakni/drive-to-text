import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Drive-to-Text",
  description: "Extract the text of the PDFs and images of a public Google Drive folder.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
