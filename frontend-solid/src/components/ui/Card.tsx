import { Show, type JSX } from "solid-js";

interface CardProps {
  title?: string;
  description?: string;
  children: JSX.Element;
  class?: string;
}

function cx(parts: Array<string | false | null | undefined>) {
  return parts.filter(Boolean).join(" ");
}

export function Card(props: CardProps) {
  return (
    <article class={cx(["ui-card", props.class])}>
      <Show when={props.title || props.description}>
        <header class="ui-card__header">
          <Show when={props.title}>
            <p class="ui-card__title">{props.title}</p>
          </Show>
          <Show when={props.description}>
            <p class="ui-card__description">{props.description}</p>
          </Show>
        </header>
      </Show>
      <div class="ui-card__body">{props.children}</div>
    </article>
  );
}
