"use client";

import { useState } from "react";
import Link from "next/link";
import {
  GraduationCap,
  ClipboardCheck,
  Waves,
  LifeBuoy,
  ArrowRight,
  CheckCircle2,
  TriangleAlert,
} from "lucide-react";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type PhaseKey = "before" | "during" | "after";

const PHASES: {
  key: PhaseKey;
  label: string;
  tagline: string;
  icon: typeof ClipboardCheck;
}[] = [
  {
    key: "before",
    label: "Before a flood",
    tagline: "Preparation saves lives — most flood deaths are preventable with early action.",
    icon: ClipboardCheck,
  },
  {
    key: "during",
    label: "During a flood",
    tagline: "Water is deceptive: 15 cm of fast-moving water can knock you down, 60 cm can sweep away a car.",
    icon: Waves,
  },
  {
    key: "after",
    label: "After a flood",
    tagline: "The danger is not over when the water recedes — disease and damaged structures kill after floods.",
    icon: LifeBuoy,
  },
];

const CONTENT: Record<
  PhaseKey,
  { heading: string; items: string[]; warning?: string }[]
> = {
  before: [
    {
      heading: "Know your risk",
      items: [
        "Check your district's flood risk on the FloodSafe risk checker — especially during the monsoon season (July–September).",
        "Find out whether your home is in a low-lying area, near a riverbank, or on a known flood path. Ask elders about past floods in your area.",
        "Learn the location of the nearest shelter, high ground, and hospital — see the relief map.",
      ],
    },
    {
      heading: "Prepare an emergency kit",
      items: [
        "Drinking water (at least 3 litres per person per day for 3 days), dry food, and ORS sachets.",
        "Torch, batteries, a charged power bank, and a battery or solar radio.",
        "Important documents in a waterproof bag: CNIC, land papers, children's B-forms.",
        "First-aid supplies, essential medicines, and mosquito nets.",
        "A whistle — it carries farther than shouting if you are trapped.",
      ],
    },
    {
      heading: "Protect your home and family",
      items: [
        "Move valuables, documents, and livestock feed to the highest floor or roof.",
        "Agree a family meeting point on high ground in case you are separated.",
        "Keep vehicle fuel tanks at least half full so you can evacuate at short notice.",
        "Save emergency numbers in every family member's phone: Rescue 1122, PDMA Sindh 1736.",
      ],
    },
  ],
  during: [
    {
      heading: "If water is rising",
      items: [
        "Move to the highest floor or roof immediately. Do not wait for official orders if water is entering your home.",
        "Turn off electricity and gas at the main switch if it is safe to reach — never touch switches while standing in water.",
        "Call Rescue 1122 if anyone is trapped. Give your village, nearest landmark, and number of people.",
      ],
      warning:
        "Never walk, swim, or drive through flood water. Six inches of fast water can knock an adult down; two feet can float a car.",
    },
    {
      heading: "If you must evacuate",
      items: [
        "Take only your emergency kit, documents, and medicines. Lock your home.",
        "Use the highest available route — avoid underpasses, nullahs, and river crossings.",
        "Do not let children play in or near flood water; it hides open manholes, ditches, and snakes.",
        "If your vehicle stalls in water, abandon it immediately and move to higher ground.",
      ],
    },
    {
      heading: "In a shelter or relief camp",
      items: [
        "Register with the camp management so your family can be accounted for.",
        "Drink only boiled or chlorinated water; use ORS at the first sign of diarrhoea.",
        "Keep children and elderly within sight; flood camps are crowded and disorienting.",
      ],
    },
  ],
  after: [
    {
      heading: "Returning home safely",
      items: [
        "Wait for authorities to declare it safe before returning. Flooded buildings can collapse.",
        "Do not enter a home where water still surrounds electrical fittings. Have wiring checked before switching power on.",
        "Wear boots and gloves while cleaning — flood water carries sewage, chemicals, and sharp debris.",
        "Throw away any food that touched flood water, including sealed packets with damaged seals.",
      ],
      warning:
        "Flood water is contaminated. Diarrhoea, cholera, skin infections, and malaria spike after floods — seek care early.",
    },
    {
      heading: "Health and hygiene",
      items: [
        "Boil drinking water for at least one full minute or use chlorine tablets.",
        "Clear stagnant water around your home to stop mosquito breeding.",
        "Watch children for fever, diarrhoea, or skin rashes in the weeks after a flood.",
      ],
    },
    {
      heading: "Recover and prepare for next time",
      items: [
        "Document damage with photos before cleaning — you may need them for relief claims.",
        "Report flood damage and blocked drainage to your district administration.",
        "Review what worked in your emergency kit and family plan, and fix what did not.",
      ],
    },
  ],
};

/**
 * Disaster education section — static preparedness content in three phases:
 * before, during, and after a flood. Written for ordinary citizens in
 * flood-prone districts of Pakistan.
 */
export default function LearnPage() {
  const [phase, setPhase] = useState<PhaseKey>("before");
  const meta = PHASES.find((p) => p.key === phase)!;

  return (
    <div className="flex min-h-screen flex-col bg-slate-50">
      <Navbar />
      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-10 sm:px-6">
        <div className="text-center">
          <p className="flex items-center justify-center gap-2 text-sm font-semibold uppercase tracking-wider text-brand-700">
            <GraduationCap className="h-4 w-4" /> Flood safety guide
          </p>
          <h1 className="mt-2 text-3xl font-extrabold tracking-tight text-navy-950 sm:text-4xl">
            What to do before, during, and after a flood
          </h1>
          <p className="mx-auto mt-3 max-w-2xl text-slate-600">
            Practical guidance for families in flood-prone areas. Read it once
            now — in an emergency there is no time to search.
          </p>
        </div>

        {/* Phase tabs */}
        <div className="mx-auto mt-8 grid max-w-3xl grid-cols-3 gap-2">
          {PHASES.map((p) => {
            const Icon = p.icon;
            const active = phase === p.key;
            return (
              <button
                key={p.key}
                onClick={() => setPhase(p.key)}
                className={cn(
                  "flex flex-col items-center gap-1.5 rounded-xl border px-3 py-4 text-sm font-semibold transition-colors",
                  active
                    ? "border-navy-950 bg-navy-950 text-white shadow"
                    : "border-slate-300 bg-white text-slate-600 hover:border-navy-700 hover:text-navy-950",
                )}
              >
                <Icon className="h-5 w-5" />
                <span className="text-xs sm:text-sm">{p.label}</span>
              </button>
            );
          })}
        </div>

        <p className="mx-auto mt-6 max-w-3xl rounded-xl border border-brand-200 bg-brand-50 p-4 text-center text-sm text-brand-900">
          {meta.tagline}
        </p>

        {/* Content cards */}
        <div className="mt-8 grid gap-6 md:grid-cols-3">
          {CONTENT[phase].map((section) => (
            <Card key={section.heading}>
              <CardHeader>
                <CardTitle className="text-base">{section.heading}</CardTitle>
              </CardHeader>
              <CardContent>
                {section.warning && (
                  <p className="mb-4 flex items-start gap-2 rounded-lg bg-red-50 p-3 text-xs font-medium text-red-800">
                    <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" />
                    {section.warning}
                  </p>
                )}
                <ul className="space-y-3">
                  {section.items.map((item, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                      <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="mt-10 flex flex-col items-center gap-4 rounded-2xl bg-navy-950 p-8 text-center text-white">
          <h2 className="text-xl font-bold">Knowledge is only useful before the flood.</h2>
          <p className="max-w-xl text-sm text-navy-100">
            Check your district&apos;s current risk, find your nearest shelter on
            the map, and share this guide with your family today.
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            <Link href="/risk-check">
              <Button variant="brand">
                Check my district <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link href="/emergency">
              <Button
                variant="outline"
                className="border-navy-700 bg-transparent text-white hover:bg-navy-800"
              >
                Emergency help
              </Button>
            </Link>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}
