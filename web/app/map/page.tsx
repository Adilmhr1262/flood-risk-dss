"use client";

import { Suspense } from "react";
import dynamic from "next/dynamic";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { Skeleton } from "@/components/ui/skeleton";
import { MapPin } from "lucide-react";

const PublicMap = dynamic(
  () => import("@/components/PublicMap").then((m) => m.PublicMap),
  {
    ssr: false,
    loading: () => <Skeleton className="h-[62vh] w-full rounded-xl" />,
  },
);

/**
 * Public GIS map page — no login required. Citizens can view flood risk
 * zones, shelters, hospitals, rescue centres, and historical floods, with
 * layer controls, district search, and information popups.
 */
export default function MapPage() {
  return (
    <div className="flex min-h-screen flex-col bg-slate-50">
      <Navbar />
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-8 sm:px-6">
        <div className="mb-6">
          <p className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-brand-700">
            <MapPin className="h-4 w-4" /> Public map
          </p>
          <h1 className="mt-2 text-3xl font-extrabold tracking-tight text-navy-950">
            Flood risk &amp; relief map
          </h1>
          <p className="mt-2 max-w-3xl text-slate-600">
            Explore current flood risk zones and find nearby shelters,
            hospitals, and rescue centres. Toggle layers on and off, search for
            your district, and tap any marker for details. Shelter and facility
            locations marked as illustrative should be confirmed with local
            authorities before travelling.
          </p>
        </div>
        <Suspense
          fallback={<Skeleton className="h-[62vh] w-full rounded-xl" />}
        >
          <PublicMap />
        </Suspense>
      </main>
      <Footer />
    </div>
  );
}
