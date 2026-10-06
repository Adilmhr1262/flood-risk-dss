import Link from "next/link";
import {
  Waves,
  BellRing,
  Map as MapIcon,
  Users,
  ShieldAlert,
  HeartHandshake,
  Database,
  Satellite,
  BrainCircuit,
  Megaphone,
  ArrowRight,
  PhoneCall,
  CheckCircle2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { LiveSituationSection } from "@/components/LiveSituationSection";

const stats = [
  { value: "12", label: "Districts monitored across Sindh" },
  { value: "2010–2024", label: "Historical flood record coverage" },
  { value: "3", label: "Prediction models (RF · XGBoost · MLP)" },
  { value: "24/7", label: "Automated early-warning watch" },
];

const features = [
  {
    icon: BrainCircuit,
    title: "Data-driven risk prediction",
    text: "Machine learning models trained on verified flood events and monsoon weather data score every district's flood probability for the season.",
  },
  {
    icon: BellRing,
    title: "Automated early warnings",
    text: "A scheduled watch cycle ingests fresh weather forecasts, runs the prediction engine, and issues advisories, warnings, and emergency alerts.",
  },
  {
    icon: MapIcon,
    title: "GIS decision support",
    text: "Interactive risk, vulnerability, shelter, and infrastructure layers give authorities a live operational picture of exposed areas.",
  },
  {
    icon: Megaphone,
    title: "Community reporting",
    text: "Citizens and volunteers report flood water, blocked roads, and rescue requests from the field; authorities triage every report.",
  },
  {
    icon: Database,
    title: "Open research data",
    text: "A documented 180 district-year dataset (2010–2024) with per-row source citations underpins every model and publication figure.",
  },
  {
    icon: Satellite,
    title: "Forecast ingestion",
    text: "Operational weather forecasts flow into the same feature pipeline the models were trained on, keeping predictions current.",
  },
];

const steps = [
  {
    n: "01",
    title: "Observe",
    text: "Monsoon rainfall, river discharge, and soil moisture are collected from meteorological feeds and the historical event archive.",
  },
  {
    n: "02",
    title: "Assess",
    text: "The prediction engine scores flood probability per district and combines it with vulnerability indicators into a risk level.",
  },
  {
    n: "03",
    title: "Warn",
    text: "When risk crosses thresholds, the early-warning cycle issues advisories and emergency alerts to authorities and the public.",
  },
  {
    n: "04",
    title: "Respond",
    text: "Authorities coordinate shelters and resources on the GIS console while volunteers report ground conditions in real time.",
  },
];

const roles = [
  {
    icon: Users,
    title: "Public",
    text: "Live risk maps, active alerts, safety guidance, and a direct line to report flooding in your area.",
    href: "/register",
    cta: "Join as a citizen",
  },
  {
    icon: ShieldAlert,
    title: "Authority",
    text: "Command overview, alert management, field-report triage, and resource allocation across districts.",
    href: "/register",
    cta: "Request authority access",
  },
  {
    icon: HeartHandshake,
    title: "NGO / Volunteer",
    text: "Submit field reports, find shelters and emergency contacts, and coordinate relief with local teams.",
    href: "/register",
    cta: "Volunteer with us",
  },
];

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col bg-white">
      <Navbar />

      {/* ---------- Hero ---------- */}
      <section className="relative overflow-hidden bg-navy-950 text-white">
        <div
          className="pointer-events-none absolute inset-0 opacity-20"
          style={{
            backgroundImage:
              "radial-gradient(circle at 20% 30%, #1f4c8a 0, transparent 40%), radial-gradient(circle at 80% 20%, #ea580c 0, transparent 35%)",
          }}
        />
        <div className="relative mx-auto max-w-7xl px-4 py-20 sm:px-6 sm:py-28">
          <Badge variant="warning" className="mb-6">
            Early warning decision support system
          </Badge>
          <h1 className="max-w-3xl text-4xl font-extrabold tracking-tight sm:text-5xl lg:text-6xl">
            Flood risk prediction and early warning for{" "}
            <span className="text-brand-500">Pakistan</span>
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-relaxed text-navy-100">
            FloodSafe Pakistan turns environmental data, historical flood
            records, and geographic intelligence into district-level risk
            assessments and timely alerts — so authorities, volunteers, and
            communities can act before the water rises.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link href="/register">
              <Button variant="brand" size="lg">
                Get started <ArrowRight />
              </Button>
            </Link>
            <Link href="/login">
              <Button
                size="lg"
                variant="outline"
                className="border-navy-700 bg-transparent text-white hover:bg-navy-800"
              >
                Sign in
              </Button>
            </Link>
          </div>

          <div className="mt-14 grid grid-cols-2 gap-4 sm:grid-cols-4">
            {stats.map((s) => (
              <div
                key={s.label}
                className="rounded-xl border border-navy-800 bg-navy-900/60 p-4"
              >
                <p className="text-2xl font-bold text-white sm:text-3xl">
                  {s.value}
                </p>
                <p className="mt-1 text-xs text-navy-100 sm:text-sm">{s.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ---------- Live situation ---------- */}
      <LiveSituationSection />

      {/* ---------- Features ---------- */}
      <section id="features" className="bg-slate-50 py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6">
          <p className="text-sm font-semibold uppercase tracking-wider text-brand-600">
            Capabilities
          </p>
          <h2 className="mt-2 text-3xl font-bold tracking-tight text-navy-950">
            One platform, from forecast to field response
          </h2>
          <p className="mt-3 max-w-2xl text-slate-600">
            Every capability is backed by the operational FastAPI backend and
            the published research dataset — no mock data, no placeholders.
          </p>
          <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((f) => (
              <Card key={f.title} className="transition-shadow hover:shadow-md">
                <CardContent className="p-6">
                  <span className="flex h-11 w-11 items-center justify-center rounded-lg bg-navy-900 text-white">
                    <f.icon className="h-5 w-5" />
                  </span>
                  <h3 className="mt-4 font-semibold text-navy-950">{f.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-slate-600">
                    {f.text}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* ---------- How it works ---------- */}
      <section id="how-it-works" className="bg-white py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6">
          <p className="text-sm font-semibold uppercase tracking-wider text-brand-600">
            How it works
          </p>
          <h2 className="mt-2 text-3xl font-bold tracking-tight text-navy-950">
            From observation to response in four steps
          </h2>
          <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {steps.map((s) => (
              <div
                key={s.n}
                className="relative rounded-xl border border-slate-200 bg-slate-50 p-6"
              >
                <span className="text-4xl font-extrabold text-navy-100">
                  {s.n}
                </span>
                <h3 className="mt-3 font-semibold text-navy-950">{s.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-600">
                  {s.text}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ---------- Emergency purpose ---------- */}
      <section id="emergency" className="bg-navy-950 py-20 text-white">
        <div className="mx-auto max-w-7xl px-4 sm:px-6">
          <div className="grid items-center gap-10 lg:grid-cols-2">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wider text-brand-500">
                Emergency purpose
              </p>
              <h2 className="mt-2 text-3xl font-bold tracking-tight">
                Built for the hours that matter most
              </h2>
              <p className="mt-4 leading-relaxed text-navy-100">
                Pakistan&apos;s monsoon floods — 2010, 2022, and every season
                since — have shown that the gap between a forecast and a saved
                life is measured in hours. FloodSafe Pakistan exists to close
                that gap: district risk scores before the clouds gather,
                warnings while there is still time to move, and a shared
                operational picture while rescue teams are in the field.
              </p>
              <ul className="mt-6 space-y-3">
                {[
                  "District-level risk levels updated through the monsoon season",
                  "Severity-graded alerts: advisory, watch, warning, emergency",
                  "Shelter locations and rescue contacts one tap away",
                ].map((t) => (
                  <li key={t} className="flex items-start gap-2 text-navy-100">
                    <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-brand-500" />
                    <span className="text-sm">{t}</span>
                  </li>
                ))}
              </ul>
            </div>
            <Card className="border-navy-800 bg-navy-900 text-white">
              <CardContent className="p-8">
                <PhoneCall className="h-10 w-10 text-brand-500" />
                <h3 className="mt-4 text-xl font-bold">
                  In an emergency, call first
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-navy-100">
                  This platform supports official response — it never replaces
                  it. If lives are at risk, contact rescue services
                  immediately.
                </p>
                <div className="mt-6 space-y-2 text-sm">
                  <p className="flex justify-between border-b border-navy-800 pb-2">
                    <span>Rescue 1122 (nationwide)</span>
                    <span className="font-bold text-brand-500">1122</span>
                  </p>
                  <p className="flex justify-between border-b border-navy-800 pb-2">
                    <span>PDMA Sindh</span>
                    <span className="font-bold text-brand-500">1736</span>
                  </p>
                  <p className="flex justify-between">
                    <span>National emergency helpline</span>
                    <span className="font-bold text-brand-500">911</span>
                  </p>
                </div>
                <Link href="/emergency">
                  <Button
                    variant="outline"
                    className="mt-6 w-full border-navy-700 bg-transparent text-white hover:bg-navy-800"
                  >
                    Open emergency help page <ArrowRight className="h-4 w-4" />
                  </Button>
                </Link>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* ---------- Roles ---------- */}
      <section className="bg-slate-50 py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6">
          <p className="text-sm font-semibold uppercase tracking-wider text-brand-600">
            Who it serves
          </p>
          <h2 className="mt-2 text-3xl font-bold tracking-tight text-navy-950">
            A workspace for every role in disaster response
          </h2>
          <div className="mt-10 grid gap-5 md:grid-cols-3">
            {roles.map((r) => (
              <Card key={r.title} className="flex flex-col">
                <CardContent className="flex flex-1 flex-col p-6">
                  <span className="flex h-11 w-11 items-center justify-center rounded-lg bg-brand-600 text-white">
                    <r.icon className="h-5 w-5" />
                  </span>
                  <h3 className="mt-4 text-lg font-semibold text-navy-950">
                    {r.title}
                  </h3>
                  <p className="mt-2 flex-1 text-sm leading-relaxed text-slate-600">
                    {r.text}
                  </p>
                  <Link href={r.href} className="mt-5">
                    <Button variant="outline" className="w-full">
                      {r.cta} <ArrowRight />
                    </Button>
                  </Link>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* ---------- CTA ---------- */}
      <section className="bg-white py-16">
        <div className="mx-auto max-w-4xl px-4 text-center sm:px-6">
          <Waves className="mx-auto h-10 w-10 text-navy-800" />
          <h2 className="mt-4 text-3xl font-bold tracking-tight text-navy-950">
            Know your district&apos;s risk before the monsoon does
          </h2>
          <p className="mt-3 text-slate-600">
            Create a free account to follow live alerts, explore the risk map,
            and report conditions from your community.
          </p>
          <div className="mt-6 flex justify-center gap-3">
            <Link href="/register">
              <Button variant="brand" size="lg">
                Create account
              </Button>
            </Link>
            <Link href="/dashboard">
              <Button variant="outline" size="lg">
                View public dashboard
              </Button>
            </Link>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
