import { A } from "@solidjs/router";

export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer class="footer">
      <div class="container footer-inner">
        <nav class="footer-links" aria-label="Alt bağlantılar">
          <A href="/about">Hakkımızda</A>
          <A href="/privacy">Gizlilik</A>
          <A href="/license">Lisans</A>
          <A href="/contact">Bize Ulaşın</A>
        </nav>
        <p>
          © {currentYear} <A href="/">Kahvesiz Çalışma</A>. Tüm hakları saklıdır.
        </p>
      </div>
    </footer>
  );
}
