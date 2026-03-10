import { type JSX } from "solid-js";
import { Footer } from "./Footer";
import { Navbar } from "./Navbar";

interface AppLayoutProps {
  children: JSX.Element;
}

export function AppLayout(props: AppLayoutProps) {
  return (
    <div class="app-shell">
      <Navbar />
      <main class="page-content">
        <div class="container">{props.children}</div>
      </main>
      <Footer />
    </div>
  );
}
