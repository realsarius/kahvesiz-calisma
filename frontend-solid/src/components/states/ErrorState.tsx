import { Show } from "solid-js";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";

interface ErrorStateProps {
  title?: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
}

export function ErrorState(props: ErrorStateProps) {
  return (
    <Card>
      <div class="state-block" aria-live="assertive">
        <p class="state-block__title">{props.title ?? "Bir hata oluştu"}</p>
        <p class="state-block__description">
          {props.description ?? "İstek tamamlanamadı. Lütfen tekrar deneyin."}
        </p>
        <Show when={props.onAction && props.actionLabel}>
          <Button variant="danger" onClick={props.onAction}>
            {props.actionLabel}
          </Button>
        </Show>
      </div>
    </Card>
  );
}
