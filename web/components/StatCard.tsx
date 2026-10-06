import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

interface StatCardProps {
  label: string;
  value: string | number;
  hint?: string;
  icon?: React.ComponentType<{ className?: string }>;
  accent?: "navy" | "orange" | "red" | "emerald";
  loading?: boolean;
  /** When set, the card becomes a clickable action card linking here. */
  href?: string;
}

const accentBar: Record<NonNullable<StatCardProps["accent"]>, string> = {
  navy: "border-l-navy-700",
  orange: "border-l-brand-600",
  red: "border-l-alert-600",
  emerald: "border-l-emerald-600",
};

export function StatCard({
  label,
  value,
  hint,
  icon: Icon,
  accent = "navy",
  loading = false,
  href,
}: StatCardProps) {
  if (loading) return <Skeleton className="h-28 rounded-xl" />;

  const body = (
    <Card
      className={cn(
        "border-l-4 transition-all duration-200",
        accentBar[accent],
        href &&
          "group cursor-pointer hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-lg",
      )}
    >
      <CardContent className="p-5">
        <div className="flex items-center justify-between">
          <p className="text-sm font-medium text-slate-500">{label}</p>
          <span className="flex items-center gap-1">
            {Icon && <Icon className="h-5 w-5 text-navy-600" />}
            {href && (
              <ArrowUpRight className="h-4 w-4 text-slate-300 transition-all group-hover:translate-x-0.5 group-hover:-translate-y-0.5 group-hover:text-brand-600" />
            )}
          </span>
        </div>
        <p className="mt-2 text-3xl font-bold tracking-tight text-navy-950">
          {value}
        </p>
        {hint && <p className="mt-1 text-xs text-slate-500">{hint}</p>}
      </CardContent>
    </Card>
  );

  return href ? <Link href={href}>{body}</Link> : body;
}
