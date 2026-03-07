import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "KiranaStudio",
  description: "Video-to-catalog pipeline for kirana stores",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${geistSans.variable} ${geistMono.variable}`}>
        <header className="header">
          <div>
            <div className="header-title">KiranaStudio</div>
            <div className="header-subtitle">Video to Catalog</div>
          </div>
        </header>
        {children}
      </body>
    </html>
  );
}
