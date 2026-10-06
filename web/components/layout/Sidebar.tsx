"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Map as MapIcon,
  BellRing,
  FileText,
  Megaphone,
  ClipboardList,
  HeartHandshake,
  PhoneCall,
  Siren,
  Warehouse,
  BarChart3,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { Role } from "@/lib/api/types";

interface NavItem {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

const NAV: Record<string, NavItem[]> = {
  public: [
    { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
    { href: "/dashboard#risk-map", label: "Risk Map", icon: MapIcon },
    { href: "/dashboard#alerts", label: "Alerts", icon: BellRing },
    { href: "/dashboard#safety", label: "Safety Guidance", icon: FileText },
  ],
  authority: [
    { href: "/authority", label: "Command Overview", icon: LayoutDashboard },
    { href: "/authority/incidents", label: "Incidents", icon: Siren },
    { href: "/authority/resources", label: "Resources", icon: Warehouse },
    { href: "/authority/reports", label: "Field Reports", icon: ClipboardList },
    { href: "/authority/analytics", label: "Analytics", icon: BarChart3 },
    { href: "/authority/map", label: "Command Map", icon: MapIcon },
  ],
  volunteer: [
    { href: "/volunteer", label: "My Portal", icon: LayoutDashboard },
    { href: "/volunteer#report", label: "Report an Event", icon: Megaphone },
    { href: "/volunteer#shelters", label: "Shelters & Contacts", icon: PhoneCall },
    { href: "/volunteer#community", label: "Community", icon: HeartHandshake },
  ],
};

function groupFor(role: Role | undefined): NavItem[] {
  if (role === "authority") return NAV.authority;
  if (role === "ngo" || role === "volunteer") return NAV.volunteer;
  return NAV.public;
}

export function Sidebar({ role }: { role: Role | undefined }) {
  const pathname = usePathname();
  const items = groupFor(role);

  return (
    <aside className="hidden w-60 shrink-0 border-r border-slate-200 bg-navy-950 text-white lg:block">
      <nav className="sticky top-[104px] flex flex-col gap-1 p-4">
        <p className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-navy-100">
          {role === "authority"
            ? "Authority Console"
            : role === "ngo" || role === "volunteer"
              ? "Volunteer Portal"
              : "Public Dashboard"}
        </p>
        {items.map((item) => {
          const active =
            pathname === item.href.split("#")[0] &&
            (item.href.includes("#") ? false : true);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                active
                  ? "bg-brand-600 text-white"
                  : "text-navy-100 hover:bg-navy-800 hover:text-white",
              )}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
        <div className="mt-6 rounded-lg border border-navy-800 bg-navy-900 p-4">
          <p className="text-xs font-semibold text-white">Emergency contacts</p>
          <p className="mt-1 text-xs text-navy-100">
            Rescue 1122 · PDMA helplines are listed under the volunteer portal.
          </p>
        </div>
      </nav>
    </aside>
  );
}
