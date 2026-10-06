import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors",
  {
    variants: {
      variant: {
        default: "border-transparent bg-navy-900 text-white",
        low: "border-transparent bg-emerald-100 text-emerald-800",
        medium: "border-transparent bg-amber-100 text-amber-800",
        high: "border-transparent bg-red-100 text-red-800",
        info: "border-transparent bg-sky-100 text-sky-800",
        watch: "border-transparent bg-amber-100 text-amber-800",
        warning: "border-transparent bg-orange-100 text-orange-800",
        emergency: "border-transparent bg-red-600 text-white",
        outline: "border-slate-300 text-navy-900",
      },
    },
    defaultVariants: { variant: "default" },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
