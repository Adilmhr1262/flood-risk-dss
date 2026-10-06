"use client";

import dynamic from "next/dynamic";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { CommandNav } from "@/components/authority/CommandNav";
import { Skeleton } from "@/components/ui/skeleton";

const CommandMap = dynamic(
  () => import("@/components/authority/CommandMap").then((m) => m.CommandMap),
  {
    ssr: false,
    loading: () => <Skeleton className="h-[62vh] w-full rounded-xl" />,
  },
);

/**
 * Authority-only GIS command map: risk zones, active incidents, field
 * reports, shelters and response teams — with layer controls.
 */
export default function CommandMapPage() {
  return (
    <DashboardShell
      title="Command Map"
      subtitle="Operational GIS view — authority eyes only"
      allowedRoles={["authority"]}
    >
      <CommandNav />
      <CommandMap />
      <p className="mt-3 text-xs text-slate-500">
        Incident and report layers are visible only to authority accounts. Facility
        locations are operational records, not public guidance.
      </p>
    </DashboardShell>
  );
}
