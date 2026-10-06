import Link from "next/link";
import { Waves } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t border-navy-800 bg-navy-950 text-navy-100">
      <div className="mx-auto grid max-w-7xl gap-8 px-4 py-12 sm:px-6 md:grid-cols-4">
        <div className="md:col-span-2">
          <div className="flex items-center gap-2.5">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-600">
              <Waves className="h-5 w-5 text-white" />
            </span>
            <span className="text-base font-bold text-white">
              FloodSafe Pakistan
            </span>
          </div>
          <p className="mt-4 max-w-md text-sm leading-relaxed">
            A public flood risk prediction and early warning decision support
            platform for Pakistan. Built on environmental data, geographic
            information, and historical flood records to help authorities,
            volunteers, and communities act before disaster strikes.
          </p>
        </div>
        <div>
          <h3 className="text-sm font-semibold uppercase tracking-wider text-white">
            Platform
          </h3>
          <ul className="mt-4 space-y-2 text-sm">
            <li>
              <Link href="/dashboard" className="hover:text-white">
                Public dashboard
              </Link>
            </li>
            <li>
              <Link href="/authority" className="hover:text-white">
                Authority console
              </Link>
            </li>
            <li>
              <Link href="/volunteer" className="hover:text-white">
                Volunteer portal
              </Link>
            </li>
          </ul>
        </div>
        <div>
          <h3 className="text-sm font-semibold uppercase tracking-wider text-white">
            Emergency
          </h3>
          <ul className="mt-4 space-y-2 text-sm">
            <li>Rescue 1122 (nationwide)</li>
            <li>PDMA Sindh helpline</li>
            <li>NDMA situation room</li>
            <li>
              <Link href="/risk-check" className="hover:text-white">
                Check flood risk
              </Link>
            </li>
            <li>
              <Link href="/map" className="hover:text-white">
                Risk &amp; relief map
              </Link>
            </li>
            <li>
              <Link href="/learn" className="hover:text-white">
                Flood safety guide
              </Link>
            </li>
            <li>
              <Link href="/status" className="hover:text-white">
                System status
              </Link>
            </li>
          </ul>
          <p className="mt-4 text-xs">
            In an emergency call 1122 first — this platform supports, but never
            replaces, official rescue services.
          </p>
        </div>
      </div>
      <div className="border-t border-navy-800 py-4 text-center text-xs">
        FloodSafe Pakistan · Research &amp; public-safety platform · Data-driven
        prediction for disaster management
      </div>
    </footer>
  );
}
