import { Show } from "solid-js";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";

interface EmptyStateProps {
  title?: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
}

export function EmptyState(props: EmptyStateProps) {
  return (
    <Card>
      <div class="state-block" aria-live="polite">
        <p class="state-block__title">{props.title ?? "Kayit bulunamadi"}</p>
        <p class="state-block__description">
          {props.description ?? "Bu filtreyle eslesen bir sonuc bulunmuyor."}
        </p>
        <Show when={props.onAction && props.actionLabel}>
          <Button variant="secondary" onClick={props.onAction}>
            {props.actionLabel}
          </Button>
        </Show>
      </div>
    </Card>
  );
}
