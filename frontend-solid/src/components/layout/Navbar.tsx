import { A, useLocation } from "@solidjs/router";
import { For } from "solid-js";
import { useAuth } from "../../auth/AuthContext";

interface NavItem {
  href: string;
  label: string;
}

const navItems: NavItem[] = [
  { href: "/", label: "Ana Sayfa" },
  { href: "/cafes", label: "Cafes" },
  { href: "/about", label: "Hakkinda" },
  { href: "/contact", label: "Iletisim" },
  { href: "/login", label: "Login" },
  { href: "/signup", label: "Signup" },
];

function isActive(pathname: string, href: string) {
  if (href === "/") {
    return pathname === "/";
  }

  return pathname === href || pathname.startsWith(`${href}/`);
}

export function Navbar() {
  const location = useLocation();
  const auth = useAuth();

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
          </ul>
        </nav>

        <div class="session-chip" role="status" aria-live="polite">
          {auth.state.loading
            ? "Oturum kontrol ediliyor"
            : auth.state.isAuthenticated
              ? "Oturum acik"
              : "Misafir"}
        </div>
      </div>
    </header>
  );
}
