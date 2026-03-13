import { A } from "@solidjs/router";

export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer class="footer">
      <div class="container footer-inner">
        <p>© {currentYear} Kahvesiz Calisma. Tum haklari saklidir.</p>
        <nav class="footer-links" aria-label="Alt baglantilar">
          <A href="/about">Hakkinda</A>
          <A href="/privacy">Gizlilik</A>
          <A href="/license">Lisans</A>
          <A href="/contact">Iletisim</A>
        </nav>
      </div>
    </footer>
  );
}
