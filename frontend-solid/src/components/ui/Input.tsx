import { splitProps, type JSX } from "solid-js";

interface InputProps extends Omit<JSX.InputHTMLAttributes<HTMLInputElement>, "id"> {
  id: string;
  label: string;
  hint?: string;
  error?: string;
}

function cx(parts: Array<string | false | null | undefined>) {
  return parts.filter(Boolean).join(" ");
}

export function Input(props: InputProps) {
  const [local, rest] = splitProps(props, ["id", "label", "hint", "error", "class"]);

  return (
    <div class="ui-field">
      <label class="ui-field__label" for={local.id}>
        {local.label}
      </label>
      <input
        id={local.id}
        class={cx(["ui-input", local.error ? "ui-input--error" : "", local.class])}
        {...rest}
      />
      {local.error ? (
        <p class="ui-field__error" role="alert">
          {local.error}
        </p>
      ) : local.hint ? (
        <p class="ui-field__hint">{local.hint}</p>
      ) : null}
    </div>
  );
}
