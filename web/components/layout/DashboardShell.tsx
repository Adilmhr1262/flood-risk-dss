"use client";

import { useEffect, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { Navbar } from "./Navbar";
import { Sidebar } from "./Sidebar";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/lib/auth/AuthProvider";
import type { Role } from "@/lib/api/types";

interface DashboardShellProps {
  children: ReactNode;
  /** Roles allowed to view this shell. Defaults to any signed-in user. */
  allowedRoles?: Role[];
  title: string;
  subtitle?: string;
  /** Optional header actions (e.g. Emergency Mode toggle). */
  actions?: ReactNode;
}

/**
 * Authenticated dashboard frame: top navbar, role sidebar, content area.
 * Redirects unauthenticated users to /login and wrong-role users home.
 */
export function DashboardShell({
  children,
  allowedRoles,
  title,
  subtitle,
  actions,
}: DashboardShellProps) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    if (allowedRoles && !allowedRoles.includes(user.role)) {
      router.replace("/");
    }
  }, [user, loading, allowedRoles, router]);

  if (loading || !user) {
    return (
      <div className="min-h-screen bg-slate-50">
        <div className="h-16 bg-navy-950" />
        <div className="mx-auto max-w-7xl space-y-4 p-6">
          <Skeleton className="h-10 w-64" />
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-28" />
            ))}
          </div>
          <Skeleton className="h-96" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <div className="mx-auto flex max-w-[1400px]">
        <Sidebar role={user.role} />
        <main className="min-w-0 flex-1 p-4 sm:p-6 lg:p-8">
          <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-navy-950 sm:text-3xl">
                {title}
              </h1>
              {subtitle && (
                <p className="mt-1 text-sm text-slate-500">{subtitle}</p>
              )}
            </div>
            {actions}
          </div>
          {children}
        </main>
      </div>
    </div>
  );
}
