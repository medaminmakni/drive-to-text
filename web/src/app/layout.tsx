import type { Metadata } from "next";

import { Welcome } from "@/components/Welcome";
import { WELCOME_SCRIPT } from "@/lib/welcome";

import "./globals.css";

export const metadata: Metadata = {
  title: "Drive-to-Text",
  description: "Extract the text of the PDFs and images of a public Google Drive folder.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    // suppressHydrationWarning: the script below may add data-welcome to <html> before React hydrates.
    <html lang="en" suppressHydrationWarning>
      <head>
        {/* Runs once while the HTML is parsed. "text/plain" in the browser only stops React's
            dev warning about script tags (pattern from the Next.js "Preventing Flash" guide). */}
        <script
          type={typeof window === "undefined" ? "text/javascript" : "text/plain"}
          suppressHydrationWarning
          dangerouslySetInnerHTML={{ __html: WELCOME_SCRIPT }}
        />
      </head>
      <body>
        <Welcome />
        {children}
      </body>
    </html>
  );
}
