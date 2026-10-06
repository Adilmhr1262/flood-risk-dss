"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { Waves, Loader2, TriangleAlert } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useAuth } from "@/lib/auth/AuthProvider";
import type { Role } from "@/lib/api/types";
import { cn } from "@/lib/utils";

const roleOptions: { value: Role; title: string; text: string }[] = [
  {
    value: "public",
    title: "Public",
    text: "Follow alerts, explore the risk map, report flooding.",
  },
  {
    value: "volunteer",
    title: "Volunteer",
    text: "Join field reporting and community relief coordination.",
  },
  {
    value: "ngo",
    title: "NGO",
    text: "Coordinate relief work with verified field data.",
  },
  {
    value: "authority",
    title: "Authority",
    text: "Disaster management officials. Granted the authority role at registration.",
  },
];

export default function RegisterPage() {
  const { register } = useAuth();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [location, setLocation] = useState("");
  const [role, setRole] = useState<Role>("public");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await register({
        name: name.trim(),
        email: email.trim(),
        password,
        role,
        location: location.trim() || undefined,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed.");
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-navy-950">
      <div className="flex flex-1 items-center justify-center px-4 py-12">
        <Card className="w-full max-w-xl">
          <CardHeader className="text-center">
            <Link href="/" className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-xl bg-brand-600">
              <Waves className="h-6 w-6 text-white" />
            </Link>
            <CardTitle className="text-2xl">Create your account</CardTitle>
            <CardDescription>
              Join FloodSafe Pakistan as a citizen, volunteer, NGO, or authority
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={onSubmit} className="space-y-4">
              {error && (
                <Alert variant="destructive">
                  <TriangleAlert />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <div>
                <Label className="mb-2 block">I am joining as</Label>
                <div className="grid gap-2 sm:grid-cols-2">
                  {roleOptions.map((o) => (
                    <button
                      key={o.value}
                      type="button"
                      onClick={() => setRole(o.value)}
                      className={cn(
                        "rounded-lg border p-3 text-left transition-colors cursor-pointer",
                        role === o.value
                          ? "border-brand-600 bg-brand-50 ring-1 ring-brand-600"
                          : "border-slate-300 hover:border-navy-600",
                      )}
                    >
                      <p className="text-sm font-semibold text-navy-950">{o.title}</p>
                      <p className="mt-0.5 text-xs text-slate-500">{o.text}</p>
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="name">Full name</Label>
                  <Input
                    id="name"
                    required
                    placeholder="Aadil Ali Mahar"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email address</Label>
                  <Input
                    id="email"
                    type="email"
                    autoComplete="email"
                    required
                    placeholder="you@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="password">Password</Label>
                  <Input
                    id="password"
                    type="password"
                    autoComplete="new-password"
                    required
                    minLength={8}
                    placeholder="Minimum 8 characters"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="location">District / city (optional)</Label>
                  <Input
                    id="location"
                    placeholder="e.g. Dadu"
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                  />
                </div>
              </div>

              <Button type="submit" variant="brand" className="w-full" disabled={busy}>
                {busy && <Loader2 className="animate-spin" />}
                {busy ? "Creating account…" : "Create account"}
              </Button>
            </form>
            <p className="mt-6 text-center text-sm text-slate-500">
              Already have an account?{" "}
              <Link href="/login" className="font-semibold text-navy-700 hover:underline">
                Sign in
              </Link>
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
