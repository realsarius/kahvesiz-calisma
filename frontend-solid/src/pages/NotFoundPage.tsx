import { A } from "@solidjs/router";

export default function NotFoundPage() {
  return (
    <section class="state-panel">
      <p class="state-title">Rota bulunamadi.</p>
      <p class="state-description">Bu adres frontend-solid router icinde tanimli degil.</p>
      <A class="btn" href="/">
        Ana sayfaya don
      </A>
    </section>
  );
}
