import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Tugarak.uz LMS",
  description: "Professional ta'lim boshqaruv tizimi"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="uz">
      <body>{children}</body>
    </html>
  );
}
