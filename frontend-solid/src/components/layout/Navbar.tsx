import { A, useLocation, useNavigate } from "@solidjs/router";
import { For, Show, createSignal } from "solid-js";
import { useAuth } from "../../auth/AuthContext";
import { apiPost } from "../../lib/api";

interface NavItem {
  href: string;
  label: string;
}

const navItems: NavItem[] = [
  { href: "/", label: "Ana Sayfa" },
  { href: "/cafes", label: "Cafes" },
  { href: "/about", label: "Hakkinda" },
  { href: "/contact", label: "Iletisim" },
];

function isActive(pathname: string, href: string) {
  if (href === "/") {
    return pathname === "/";
  }

  return pathname === href || pathname.startsWith(`${href}/`);
}

export function Navbar() {
  const location = useLocation();
  const navigate = useNavigate();
  const auth = useAuth();
  const [loggingOut, setLoggingOut] = createSignal(false);

  const onLogout = async () => {
    if (loggingOut()) {
      return;
    }

    setLoggingOut(true);
    try {
      await apiPost<{ message?: string } | null>(
        "/api/logout",
        {},
        {
          retries: 0,
          timeoutMs: 8_000,
          emitAuthEvent: false,
        },
      );
      auth.clearSession(false);
      void navigate("/login", { replace: true });
    } catch {
      window.location.href = "/logout";
    } finally {
      setLoggingOut(false);
    }
  };

  return (
    <header class="topbar">
      <div class="container topbar-inner">
        <A class="brand" href="/">
          Kahvesiz Calisma
        </A>

        <nav aria-label="Ana menu">
          <ul class="nav-list">
            <For each={navItems}>
              {(item) => (
                <li>
                  <A
                    classList={{
                      "nav-link": true,
                      active: isActive(location.pathname, item.href),
                    }}
                    href={item.href}
                  >
                    {item.label}
                  </A>
                </li>
              )}
            </For>
            <Show when={auth.state.user?.isAdmin}>
              <li>
                <A classList={{ "nav-link": true, active: isActive(location.pathname, "/admin") }} href="/admin">
                  Admin
                </A>
              </li>
            </Show>
          </ul>
        </nav>

        <div class="session-area">
          <div class="session-chip" role="status" aria-live="polite">
            {auth.state.loading
              ? "Oturum kontrol ediliyor"
              : auth.state.isAuthenticated
                ? "Oturum acik"
                : "Misafir"}
          </div>

          <Show
            when={auth.state.isAuthenticated}
            fallback={
              <>
                <A class="nav-link" href="/login">
                  Login
                </A>
                <A class="nav-link" href="/signup">
                  Signup
                </A>
              </>
            }
          >
            <button class="nav-link nav-button-link" type="button" onClick={() => void onLogout()} disabled={loggingOut()}>
              {loggingOut() ? "Cikis..." : "Logout"}
            </button>
          </Show>
        </div>
      </div>
    </header>
  );
}
