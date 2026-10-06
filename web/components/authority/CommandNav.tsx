"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Siren,
  Warehouse,
  ClipboardList,
  BarChart3,
  Map as MapIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";

const ITEMS = [
  { href: "/authority", label: "Overview", icon: LayoutDashboard },
  { href: "/authority/incidents", label: "Incidents", icon: Siren },
  { href: "/authority/resources", label: "Resources", icon: Warehouse },
  { href: "/authority/reports", label: "Reports", icon: ClipboardList },
  { href: "/authority/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/authority/map", label: "Map", icon: MapIcon },
];

/** Horizontal tab strip for the command center on small screens (sidebar is desktop-only). */
export function CommandNav() {
  const pathname = usePathname();
  return (
    <nav className="mb-6 flex gap-2 overflow-x-auto pb-1 lg:hidden" aria-label="Command center">
      {ITEMS.map((item) => {
        const active = pathname === item.href;
        const Icon = item.icon;
        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex shrink-0 items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-semibold transition-colors",
              active
                ? "border-navy-950 bg-navy-950 text-white"
                : "border-slate-300 bg-white text-slate-600 hover:border-navy-600",
            )}
          >
            <Icon className="h-3.5 w-3.5" />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
