import type { Metadata } from "next";
import { IBM_Plex_Sans, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";

const ibmPlexSans = IBM_Plex_Sans({
  variable: "--font-sans",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
});

const ibmPlexMono = IBM_Plex_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

export const metadata: Metadata = {
  title: "GraphSentinel | AML Fraud Detection",
  description:
    "AI-Powered AML investigative platform for detecting cyclic fraud and smurfing through knowledge graphs.",
  openGraph: {
    title: "GraphSentinel AML Detection",
    description:
      "AI-Powered AML investigative platform for detecting cyclic fraud and smurfing through knowledge graphs.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${ibmPlexSans.variable} ${ibmPlexMono.variable} antialiased`}
      >
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:top-0 focus:left-0 focus:z-50 focus:p-4 focus:bg-background focus:text-foreground"
        >
          Skip to main content
        </a>
        <main id="main-content" className="min-h-screen">
          {children}
        </main>
      </body>
    </html>
  );
}
