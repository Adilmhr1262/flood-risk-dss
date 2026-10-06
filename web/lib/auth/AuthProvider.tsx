"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { usePathname, useRouter } from "next/navigation";
import { ApiError, type Role, type UserOut } from "@/lib/api/types";
import { authApi } from "@/lib/api/endpoints";
import { clearTokens, getAccessToken, setTokens } from "@/lib/api/client";

const ROLE_COOKIE = "floodsafe_role";
const AUTH_COOKIE = "floodsafe_auth";

function writeSessionCookies(role: Role | null) {
  if (typeof document === "undefined") return;
  if (role) {
    document.cookie = `${AUTH_COOKIE}=1; path=/; max-age=604800; SameSite=Lax`;
    document.cookie = `${ROLE_COOKIE}=${role}; path=/; max-age=604800; SameSite=Lax`;
  } else {
    document.cookie = `${AUTH_COOKIE}=; path=/; max-age=0`;
    document.cookie = `${ROLE_COOKIE}=; path=/; max-age=0`;
  }
}

export function homeForRole(role: Role): string {
  switch (role) {
    case "authority":
      return "/authority";
    case "ngo":
    case "volunteer":
      return "/volunteer";
    default:
      return "/dashboard";
  }
}

interface AuthContextValue {
  user: UserOut | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (input: {
    name: string;
    email: string;
    password: string;
    role: Role;
    location?: string;
  }) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

/** Routes that require a signed-in user; the proxy guards these server-side. */
function isProtectedRoute(pathname: string): boolean {
  return (
    pathname === "/dashboard" ||
    pathname.startsWith("/dashboard/") ||
    pathname === "/authority" ||
    pathname.startsWith("/authority/") ||
    pathname === "/volunteer" ||
    pathname.startsWith("/volunteer/")
  );
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserOut | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    let cancelled = false;
    // No stored session: stay anonymous. Public pages must never bounce
    // visitors to /login just for loading the site. All session state
    // updates happen inside the async loader (never synchronously in the
    // effect body) to avoid cascading renders.
    async function loadSession() {
      if (!getAccessToken()) {
        if (!cancelled) {
          setUser(null);
          writeSessionCookies(null);
          setLoading(false);
        }
        return;
      }
      try {
        const u = await authApi.me();
        if (!cancelled) {
          setUser(u);
          writeSessionCookies(u.role);
        }
      } catch {
        if (!cancelled) {
          setUser(null);
          writeSessionCookies(null);
        }
      }
      if (!cancelled) setLoading(false);
    }
    void loadSession();

    const onUnauthorized = () => {
      setUser(null);
      clearTokens();
      writeSessionCookies(null);
      // Only bounce to /login from protected routes; on public pages the
      // session simply ends silently (proxy.ts guards the protected ones).
      if (isProtectedRoute(pathname)) router.replace("/login");
    };
    window.addEventListener("floodsafe:unauthorized", onUnauthorized);
    return () => {
      cancelled = true;
      window.removeEventListener("floodsafe:unauthorized", onUnauthorized);
    };
  }, [router, pathname]);

  const login = useCallback(
    async (email: string, password: string) => {
      try {
        const tokens = await authApi.login({ email, password });
        setTokens(tokens.access_token, tokens.refresh_token);
        const me = await authApi.me();
        setUser(me);
        writeSessionCookies(me.role);
        router.replace(homeForRole(me.role));
      } catch (err) {
        clearTokens();
        throw err instanceof ApiError ? err : new Error("Login failed.");
      }
    },
    [router],
  );

  const register = useCallback(
    async (input: {
      name: string;
      email: string;
      password: string;
      role: Role;
      location?: string;
    }) => {
      try {
        const tokens = await authApi.register({
          name: input.name,
          email: input.email,
          password: input.password,
          role: input.role,
          location_name: input.location || null,
        });
        setTokens(tokens.access_token, tokens.refresh_token);
        const me = await authApi.me();
        setUser(me);
        writeSessionCookies(me.role);
        router.replace(homeForRole(me.role));
      } catch (err) {
        clearTokens();
        throw err instanceof ApiError ? err : new Error("Registration failed.");
      }
    },
    [router],
  );

  const logout = useCallback(() => {
    authApi.logout().catch(() => undefined);
    setUser(null);
    clearTokens();
    writeSessionCookies(null);
    router.replace("/");
  }, [router]);

  const value = useMemo(
    () => ({ user, loading, login, register, logout }),
    [user, loading, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
