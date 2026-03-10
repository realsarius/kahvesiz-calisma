import { useAuth } from "../auth/AuthContext";

const checklistItems = [
  "Vite + Solid + TypeScript kuruldu.",
  "Router ve temel layout shell aktif.",
  "API istemcisi credentials include + timeout ile tanimli.",
  "Auth context iskeleti ve global 401 dinleyicisi hazir.",
  "Route bazli code splitting lazy import ile acik.",
];

export default function HomePage() {
  const auth = useAuth();

  return (
    <section class="content-grid">
      <article class="panel">
        <p class="panel-title">Faz 1 Durumu</p>
        <ul class="checklist">
          {checklistItems.map((item) => (
            <li>{item}</li>
          ))}
        </ul>
      </article>

      <article class="panel">
        <p class="panel-title">Auth Bootstrap</p>
        <dl class="meta-list">
          <div>
            <dt>loading</dt>
            <dd>{String(auth.state.loading)}</dd>
          </div>
          <div>
            <dt>isAuthenticated</dt>
            <dd>{String(auth.state.isAuthenticated)}</dd>
          </div>
          <div>
            <dt>sessionExpired</dt>
            <dd>{String(auth.state.sessionExpired)}</dd>
          </div>
          <div>
            <dt>user</dt>
            <dd>{auth.state.user ? auth.state.user.email : "null"}</dd>
          </div>
        </dl>
      </article>
    </section>
  );
}
