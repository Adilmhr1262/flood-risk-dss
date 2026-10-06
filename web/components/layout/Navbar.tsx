"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Waves, LogOut, LayoutDashboard, ShieldAlert, Users, Menu, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth, homeForRole } from "@/lib/auth/AuthProvider";
import { cn } from "@/lib/utils";

const publicLinks = [
  { href: "/", label: "Home" },
  { href: "/risk-check", label: "Risk check" },
  { href: "/map", label: "Risk map" },
  { href: "/history", label: "Flood history" },
  { href: "/emergency", label: "Emergency" },
  { href: "/learn", label: "Safety guide" },
];

export function Navbar() {
  const pathname = usePathname();
  const { user, loading, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 w-full border-b border-navy-800 bg-navy-950 text-white">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6">
        <Link href={user ? homeForRole(user.role) : "/"} className="flex items-center gap-2.5">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-600">
            <Waves className="h-5 w-5 text-white" />
          </span>
          <span className="leading-tight">
            <span className="block text-base font-bold tracking-tight">
              FloodSafe Pakistan
            </span>
            <span className="block text-[11px] font-medium text-navy-100 hidden min-[400px]:block">
              Flood Risk Prediction &amp; Early Warning
            </span>
          </span>
        </Link>

        {!user && !loading && (
          <nav className="hidden items-center gap-6 md:flex">
            {publicLinks.map((l) => (
              <Link
                key={l.href}
                href={l.href}
                className={cn(
                  "text-sm font-medium text-navy-100 transition-colors hover:text-white",
                  pathname === l.href && "text-white",
                )}
              >
                {l.label}
              </Link>
            ))}
          </nav>
        )}

        <div className="flex items-center gap-2">
          {!user && !loading && (
            <button
              onClick={() => setMenuOpen((o) => !o)}
              aria-label={menuOpen ? "Close menu" : "Open menu"}
              className="rounded-lg p-2 text-navy-100 hover:bg-navy-800 md:hidden"
            >
              {menuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          )}
          {loading ? null : user ? (
            <>
              <span className="hidden items-center gap-1.5 rounded-full bg-navy-800 px-3 py-1 text-xs font-medium text-navy-100 sm:inline-flex">
                {user.role === "authority" ? (
                  <ShieldAlert className="h-3.5 w-3.5" />
                ) : user.role === "ngo" || user.role === "volunteer" ? (
                  <Users className="h-3.5 w-3.5" />
                ) : (
                  <LayoutDashboard className="h-3.5 w-3.5" />
                )}
                {user.role.charAt(0).toUpperCase() + user.role.slice(1)}
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={logout}
                className="text-navy-100 hover:bg-navy-800 hover:text-white"
              >
                <LogOut className="h-4 w-4" />
                <span className="hidden sm:inline">Sign out</span>
              </Button>
            </>
          ) : (
            <>
              <Link href="/login" className="hidden sm:inline">
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-navy-100 hover:bg-navy-800 hover:text-white"
                >
                  Sign in
                </Button>
              </Link>
              <Link href="/register">
                <Button variant="brand" size="sm">
                  Create account
                </Button>
              </Link>
            </>
          )}
        </div>
      </div>
      {/* Mobile menu (public links) */}
      {!user && !loading && menuOpen && (
        <nav className="border-t border-navy-800 bg-navy-950 px-4 py-3 md:hidden">
          <div className="mb-2 flex gap-2 sm:hidden">
            <Link
              href="/login"
              onClick={() => setMenuOpen(false)}
              className="flex-1 rounded-lg border border-navy-700 px-3 py-2.5 text-center text-sm font-medium text-navy-100 hover:bg-navy-800 hover:text-white"
            >
              Sign in
            </Link>
          </div>
          {publicLinks.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              onClick={() => setMenuOpen(false)}
              className={cn(
                "block rounded-lg px-3 py-2.5 text-sm font-medium text-navy-100 hover:bg-navy-800 hover:text-white",
                pathname === l.href && "bg-navy-800 text-white",
              )}
            >
              {l.label}
            </Link>
          ))}
        </nav>
      )}
      {/* Emergency strip */}
      <div className="bg-alert-600 px-4 py-1 text-center text-[11px] font-semibold tracking-wide text-white sm:text-xs">
        FLOOD EMERGENCY HELPLINE — PDMA / Rescue 1122 — Always verify alerts
        through official channels
      </div>
    </header>
  );
}
