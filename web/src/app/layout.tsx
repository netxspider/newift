import type { Metadata } from "next";
import {CursorBubble} from "@/components/CursorBubble";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000"),
  title: { default: "Newift — What’s trending now, delivered swift.", template: "%s | Newift" },
  description: "Fast, easy-to-read coverage of trending stories, viral events, technology, pop culture, and breaking updates.",
  keywords: ["trending news", "viral stories", "technology", "pop culture", "breaking updates"],
  openGraph: { type: "website", siteName: "Newift", title: "Newift — What’s trending now, delivered swift.", description: "The modern pulse on what’s happening right now." },
  twitter: { card: "summary_large_image" },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" data-theme="light">
      <body>{children}<CursorBubble /></body>
    </html>
  );
}
