import { splitProps, type JSX } from "solid-js";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
type ButtonSize = "sm" | "md";

interface ButtonProps extends JSX.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  fullWidth?: boolean;
}

function cx(parts: Array<string | false | null | undefined>) {
  return parts.filter(Boolean).join(" ");
}

export function Button(props: ButtonProps) {
  const [local, rest] = splitProps(props, ["variant", "size", "fullWidth", "class"]);

  return (
    <button
      class={cx([
        "ui-button",
        `ui-button--${local.variant ?? "primary"}`,
        `ui-button--${local.size ?? "md"}`,
        local.fullWidth ? "ui-button--block" : "",
        local.class,
      ])}
      {...rest}
    />
  );
}
