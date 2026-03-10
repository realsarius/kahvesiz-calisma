interface GlobalErrorFallbackProps {
  error: unknown;
  reset: () => void;
}

function toMessage(error: unknown) {
  if (error instanceof Error) {
    return error.message;
  }

  return "Beklenmeyen bir hata olustu.";
}

export function GlobalErrorFallback(props: GlobalErrorFallbackProps) {
  return (
    <section class="state-panel" aria-live="assertive">
      <p class="state-title">Uygulama beklenmeyen bir hatayla karsilasti.</p>
      <p class="state-description">{toMessage(props.error)}</p>
      <button class="btn" type="button" onClick={props.reset}>
        Tekrar dene
      </button>
    </section>
  );
}
