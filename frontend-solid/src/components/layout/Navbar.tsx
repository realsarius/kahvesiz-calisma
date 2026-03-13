import { A, useLocation, useNavigate } from "@solidjs/router";
import { FiCoffee, FiGrid, FiHome, FiLogIn, FiMail } from "solid-icons/fi";
import type { JSX } from "solid-js";
import { For, Show, createSignal, onCleanup, onMount } from "solid-js";
import { useAuth } from "../../auth/AuthContext";
import { apiPost } from "../../lib/api";

interface NavItem {
  href: string;
  label: string;
  icon: (props: Record<string, unknown>) => JSX.Element;
}

const navItems: NavItem[] = [
  { href: "/", label: "Ana Sayfa", icon: FiHome },
  { href: "/cafes", label: "Kafeler", icon: FiGrid },
  { href: "/contact", label: "Bize Ulaşın", icon: FiMail },
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
  const [isHidden, setIsHidden] = createSignal(false);
  let headerRef: HTMLElement | undefined;

  onMount(() => {
    let lastY = window.scrollY;
    let ticking = false;

    const updateTopbarHeight = () => {
      const height = headerRef?.offsetHeight ?? 76;
      document.documentElement.style.setProperty("--topbar-height", `${height}px`);
    };

    const processScroll = () => {
      const currentY = window.scrollY;
      const deltaY = currentY - lastY;

      if (currentY <= 10) {
        setIsHidden(false);
        lastY = currentY;
        return;
      }

      if (Math.abs(deltaY) < 6) {
        return;
      }

      if (deltaY > 0 && currentY > 110) {
        setIsHidden(true);
      } else if (deltaY < 0) {
        setIsHidden(false);
      }

      lastY = currentY;
    };

    const onScroll = () => {
      if (ticking) {
        return;
      }

      ticking = true;
      window.requestAnimationFrame(() => {
        processScroll();
        ticking = false;
      });
    };

    updateTopbarHeight();
    window.addEventListener("resize", updateTopbarHeight);
    window.addEventListener("scroll", onScroll, { passive: true });

    onCleanup(() => {
      window.removeEventListener("resize", updateTopbarHeight);
      window.removeEventListener("scroll", onScroll);
      document.documentElement.style.removeProperty("--topbar-height");
    });
  });

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
    <header
      ref={(element) => {
        headerRef = element;
      }}
      classList={{ topbar: true, "topbar--hidden": isHidden() }}
    >
      <div class="container topbar-inner">
        <A class="brand" href="/">
          <FiCoffee class="brand-logo" aria-hidden="true" />
          <span class="brand-title">Kahvesiz Çalışma</span>
        </A>

        <nav aria-label="Ana menü">
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
                    <item.icon class="nav-link__icon" aria-hidden="true" />
                    {item.label}
                  </A>
                </li>
              )}
            </For>
          </ul>
        </nav>

        <div class="session-area">
          <Show
            when={auth.state.isAuthenticated}
            fallback={
              <A class="auth-button" href="/login">
                <FiLogIn class="auth-button__icon" aria-hidden="true" />
                Giriş
              </A>
            }
          >
            <div class="session-chip" role="status" aria-live="polite">
              {auth.state.user?.name || "Kullanıcı"}
            </div>
            <Show when={auth.state.user?.isAdmin}>
              <A class="nav-link nav-link--admin" href="/admin">
                Yönetim
              </A>
            </Show>
            <button class="nav-link nav-button-link" type="button" onClick={() => void onLogout()} disabled={loggingOut()}>
              {loggingOut() ? "Çıkış..." : "Çıkış"}
            </button>
          </Show>
        </div>
      </div>
    </header>
  );
}
