import { Show, type JSX } from "solid-js";

type AlertVariant = "info" | "success" | "warning" | "error";

interface AlertProps {
  variant?: AlertVariant;
  title?: string;
  children: JSX.Element;
}

export function Alert(props: AlertProps) {
  return (
    <section class={`ui-alert ui-alert--${props.variant ?? "info"}`} role="status" aria-live="polite">
      <Show when={props.title}>
        <p class="ui-alert__title">{props.title}</p>
      </Show>
      <div class="ui-alert__body">{props.children}</div>
    </section>
  );
}
