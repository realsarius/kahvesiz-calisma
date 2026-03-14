import { type JSX } from "solid-js";
import { CookieBanner } from "../CookieBanner";
import { Footer } from "./Footer";
import { Navbar } from "./Navbar";

interface AppLayoutProps {
  children: JSX.Element;
}

export function AppLayout(props: AppLayoutProps) {
  return (
    <div class="app-shell">
      <Navbar />
      <div class="shell-stage">
        <div class="shell-glow shell-glow--top" aria-hidden="true" />
        <main class="page-content">{props.children}</main>
        <CookieBanner />
        <div class="shell-glow shell-glow--bottom" aria-hidden="true" />
      </div>
      <Footer />
    </div>
  );
}
