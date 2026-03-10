import { A } from "@solidjs/router";
import { Card } from "../components/ui/Card";
import { PageContainer } from "../components/ui/PageContainer";

export default function NotFoundPage() {
  return (
    <PageContainer title="Rota bulunamadi" subtitle="Bu adres frontend-solid icinde tanimli degil.">
      <Card>
        <A class="ui-link" href="/">
          Ana sayfaya don
        </A>
      </Card>
    </PageContainer>
  );
}
