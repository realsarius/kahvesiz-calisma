import { Show, type JSX } from "solid-js";

interface PageContainerProps {
  title: string;
  subtitle?: string;
  actions?: JSX.Element;
  children: JSX.Element;
}

export function PageContainer(props: PageContainerProps) {
  return (
    <section class="page-container">
      <header class="page-container__header">
        <div>
          <p class="page-container__title">{props.title}</p>
          <Show when={props.subtitle}>
            <p class="page-container__subtitle">{props.subtitle}</p>
          </Show>
        </div>
        <Show when={props.actions}>
          <div class="page-container__actions">{props.actions}</div>
        </Show>
      </header>
      <div class="page-container__body">{props.children}</div>
    </section>
  );
}
