import { ErrorState } from "./states/ErrorState";

interface GlobalErrorFallbackProps {
  error: unknown;
  reset: () => void;
}

function toMessage(error: unknown) {
  if (error instanceof Error) {
    return error.message;
  }

  return "Beklenmeyen bir hata oluştu.";
}

export function GlobalErrorFallback(props: GlobalErrorFallbackProps) {
  return (
    <ErrorState
      title="Uygulama beklenmeyen bir hatayla karşılaştı"
      description={toMessage(props.error)}
      actionLabel="Tekrar dene"
      onAction={props.reset}
    />
  );
}
