import Link from "next/link";
import { Waves } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-navy-950 px-4 text-center text-white">
      <Waves className="h-12 w-12 text-brand-500" />
      <h1 className="mt-6 text-5xl font-extrabold">404</h1>
      <p className="mt-3 max-w-md text-navy-100">
        This page was washed away — the address you requested does not exist on
        FloodSafe Pakistan.
      </p>
      <Link href="/" className="mt-8">
        <Button variant="brand">Back to home</Button>
      </Link>
    </div>
  );
}
