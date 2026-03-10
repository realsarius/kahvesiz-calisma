import { A, useLocation } from "@solidjs/router";
import { useAuth } from "../../auth/AuthContext";

const navItems = [
  { href: "/", label: "Ana Sayfa" },
  { href: "/about", label: "Hakkinda" },
  { href: "/login", label: "Login" },
  { href: "/signup", label: "Signup" },
];

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
            {navItems.map((item) => (
              <li>
                <A classList={{ "nav-link": true, active: location.pathname === item.href }} href={item.href}>
                  {item.label}
                </A>
              </li>
            ))}
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
