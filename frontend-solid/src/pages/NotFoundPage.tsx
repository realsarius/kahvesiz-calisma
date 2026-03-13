import { A } from "@solidjs/router";
import { Card } from "../components/ui/Card";
import { PageContainer } from "../components/ui/PageContainer";

export default function NotFoundPage() {
  return (
    <PageContainer title="Rota bulunamadı" subtitle="Bu adres frontend-solid içinde tanımlı değil.">
      <Card>
        <A class="ui-link" href="/">
          Ana sayfaya dön
        </A>
      </Card>
    </PageContainer>
  );
}
