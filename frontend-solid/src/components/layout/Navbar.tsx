import { A, useLocation, useNavigate } from "@solidjs/router";
import { For, Show, createSignal, onCleanup, onMount } from "solid-js";
import { useAuth } from "../../auth/AuthContext";
import { apiPost } from "../../lib/api";

interface NavItem {
  href: string;
  label: string;
}

const navItems: NavItem[] = [
  { href: "/", label: "Ana Sayfa" },
  { href: "/cafes", label: "Kafeler" },
  { href: "/contact", label: "Bize Ulaşın" },
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
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="brand-logo"
            viewBox="0 0 64 64"
            aria-hidden="true"
          >
            <path
              style={{ fill: "rgb(210, 180, 140)" }}
              d="m61.948 19.134-.885 4.764H30.075l-.885-4.764h32.758zm-19.45 26.555v2.2c0 3.028-1.302 5.751-3.369 7.659h16.054l1.829-9.86H42.498zM10.639 31.593V47.89c0 4.799 3.905 8.704 8.704 8.704H32.05c4.804 0 8.709-3.905 8.709-8.704V31.593h-30.12z"
            />
            <path
              style={{ fill: "rgb(139, 104, 72)" }}
              d="M38.481 31.449v16.297c0 4.799-3.905 8.704-8.709 8.704h3.542c4.804 0 8.709-3.905 8.709-8.704V31.449h-3.542z"
            />
            <path
              style={{ fill: "rgb(160, 122, 84)" }}
              d="M63.798 24.221a.87.87 0 0 0-.669-.323h-.297l.943-5.069a.87.87 0 0 0 .221-.567v-5.866a.87.87 0 0 0-.868-.868h-.562l-3.54-5.468a.865.865 0 0 0-.726-.398H32.842a.868.868 0 0 0-.73.398l-3.542 5.468h-.558a.87.87 0 0 0-.872.868v5.866c0 .217.089.412.221.567l.943 5.069h-.292a.887.887 0 0 0-.677.323.883.883 0 0 0-.173.731l1.009 4.901H9.767a.87.87 0 0 0-.868.868v3.391C3.985 34.138 0 38.141 0 43.068 0 48 4.011 52.016 8.943 52.016h.806c1.603 3.715 5.3 6.322 9.594 6.322H32.05c1.625 0 3.157-.385 4.525-1.045h19.33a.873.873 0 0 0 .863-.717l2.019-10.887h.217a.878.878 0 0 0 .854-.7l4.126-20.038a.885.885 0 0 0-.186-.73zM8.943 50.272c-3.971 0-7.203-3.232-7.203-7.212 0-3.958 3.205-7.177 7.159-7.203V47.89c0 .823.102 1.616.283 2.382h-.239zM33.316 7.406h24.51l2.67 4.122h-29.85l2.67-4.122zM32.05 56.594H19.343c-4.799 0-8.704-3.905-8.704-8.704V31.593h30.119V47.89c0 4.799-3.905 8.704-8.708 8.704zm23.133-1.045H39.129a10.393 10.393 0 0 0 3.369-7.659v-2.2h14.513l-1.828 9.859zM41.972 29.924a6.016 6.016 0 0 1 3.599-1.195c3.343 0 6.066 2.723 6.066 6.07s-2.723 6.066-6.066 6.066a6 6 0 0 1-3.073-.841V30.72a.865.865 0 0 0-.526-.796zm16.319 14.021H42.498v-1.979a7.731 7.731 0 0 0 3.073.642c4.303 0 7.805-3.507 7.805-7.81 0-4.308-3.502-7.81-7.805-7.81a7.77 7.77 0 0 0-6.021 2.865h-9.607l-.868-4.21h32.984l-3.768 18.302zM29.19 19.134h32.758l-.885 4.764H30.075l-.885-4.764zm33.068-1.744H28.88v-4.122h33.378v4.122z"
            />
          </svg>
          <span class="brand-title">Kahvesiz Çalışma</span>
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
          </ul>
        </nav>

        <div class="session-area">
          <Show
            when={auth.state.isAuthenticated}
            fallback={
              <A class="auth-button" href="/login">
                Giriş
              </A>
            }
          >
            <div class="session-chip" role="status" aria-live="polite">
              {auth.state.user?.name || "Kullanici"}
            </div>
            <Show when={auth.state.user?.isAdmin}>
              <A class="nav-link nav-link--admin" href="/admin">
                Dashboard
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
