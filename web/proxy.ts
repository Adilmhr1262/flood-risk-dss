import { NextRequest, NextResponse } from "next/server";

/**
 * Optimistic route guard. Reads the lightweight session cookies written by
 * the AuthProvider at login (the real JWT lives in localStorage and is sent
 * as a Bearer token by the API client).
 */

const PUBLIC_ROUTES = ["/", "/login", "/register"];

function routeRole(pathname: string): "authority" | "volunteer" | "public" | null {
  if (pathname === "/authority" || pathname.startsWith("/authority/"))
    return "authority";
  if (pathname === "/volunteer" || pathname.startsWith("/volunteer/"))
    return "volunteer";
  if (pathname === "/dashboard" || pathname.startsWith("/dashboard/"))
    return "public";
  return null;
}

function homeForRole(role: string | undefined): string {
  if (role === "authority") return "/authority";
  if (role === "ngo" || role === "volunteer") return "/volunteer";
  return "/dashboard";
}

export default async function proxy(req: NextRequest) {
  const { pathname } = req.nextUrl;
  const authed = req.cookies.get("floodsafe_auth")?.value === "1";
  const role = req.cookies.get("floodsafe_role")?.value;

  const needed = routeRole(pathname);

  // Protected route without a session -> login.
  if (needed && !authed) {
    return NextResponse.redirect(new URL("/login", req.nextUrl));
  }

  // Wrong role for the area -> send to the role's home.
  if (needed && authed) {
    const allowed =
      needed === "authority"
        ? role === "authority"
        : needed === "volunteer"
          ? role === "ngo" || role === "volunteer"
          : true; // /dashboard is open to every signed-in role
    if (!allowed) {
      return NextResponse.redirect(new URL(homeForRole(role), req.nextUrl));
    }
  }

  // Signed-in users visiting login/register/landing auth pages go home.
  if (authed && (pathname === "/login" || pathname === "/register")) {
    return NextResponse.redirect(new URL(homeForRole(role), req.nextUrl));
  }

  if (PUBLIC_ROUTES.includes(pathname)) return NextResponse.next();
  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|.*\\.png$|.*\\.ico$).*)"],
};
