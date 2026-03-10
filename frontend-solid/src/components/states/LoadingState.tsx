import { Card } from "../ui/Card";

interface LoadingStateProps {
  title?: string;
  description?: string;
}

export function LoadingState(props: LoadingStateProps) {
  return (
    <Card>
      <div class="state-block" aria-live="polite" aria-busy="true">
        <p class="state-block__title">{props.title ?? "Yukleniyor"}</p>
        <p class="state-block__description">
          {props.description ?? "Icerik hazirlaniyor, lutfen bekleyin."}
        </p>
      </div>
    </Card>
  );
}
