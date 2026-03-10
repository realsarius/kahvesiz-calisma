import { A } from "@solidjs/router";

export function Footer() {
  return (
    <footer class="footer">
      <div class="container footer-inner">
        <p>Kahvesiz Calisma Solid frontend</p>
        <nav class="footer-links" aria-label="Alt baglantilar">
          <A href="/privacy">Gizlilik</A>
          <A href="/license">Lisans</A>
          <A href="/contact">Iletisim</A>
        </nav>
      </div>
    </footer>
  );
}
