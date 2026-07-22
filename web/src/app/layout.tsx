import type { Metadata } from "next";
import Script from "next/script";
import {CursorBubble} from "@/components/CursorBubble";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000"),
  title: { default: "Newift — What’s trending now, delivered swift.", template: "%s | Newift" },
  description: "Fast, easy-to-read coverage of trending stories, viral events, technology, pop culture, and breaking updates.",
  keywords: ["trending news", "viral stories", "technology", "pop culture", "breaking updates"],
  openGraph: { type: "website", siteName: "Newift", title: "Newift — What’s trending now, delivered swift.", description: "The modern pulse on what’s happening right now." },
  twitter: { card: "summary_large_image" },
  icons: {
    icon: [{url: "/newift-icon.svg", type: "image/svg+xml"}],
    shortcut: "/newift-icon.svg",
    apple: "/newift-icon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" data-theme="light">
      <head>
        <Script id="google-tag-manager" strategy="beforeInteractive">{`(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src='https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);})(window,document,'script','dataLayer','GTM-KHNHD7DS');`}</Script>
        <meta name="google-site-verification" content="b7Ibb-CurAzWO4WPTgf-8-9oXrcBSzSO5wbmrnf_NwY" />
        <meta name="google-adsense-account" content="ca-pub-9668645091104713" />
        <Script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-9668645091104713" crossOrigin="anonymous" strategy="afterInteractive" />
      </head>
      <body><noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-KHNHD7DS" height="0" width="0" style={{display: "none", visibility: "hidden"}} /></noscript>{children}<CursorBubble /></body>
    </html>
  );
}
