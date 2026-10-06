import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/lib/auth/AuthProvider";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "FloodSafe Pakistan — Flood Risk Prediction & Early Warning",
    template: "%s · FloodSafe Pakistan",
  },
  description:
    "Public flood risk prediction and early warning decision support platform for Pakistan. Data-driven risk assessment for authorities, volunteers, and communities.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  // Read at request time (not build time) so the API target can change
  // without a rebuild — updated via the API_BASE_URL env var.
  const apiBaseUrl =
    process.env.API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE_URL || "";
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `window.__API_BASE_URL__=${JSON.stringify(apiBaseUrl)};`,
          }}
        />
      </head>
      <body className="min-h-full flex flex-col">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
