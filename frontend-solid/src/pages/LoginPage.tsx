import { Card } from "../components/ui/Card";
import { PageContainer } from "../components/ui/PageContainer";

export default function LoginPage() {
  return (
    <PageContainer title="Login" subtitle="Session + CSRF uyumlu login formu bu rotaya tasinacak.">
      <Card>
        <p class="paragraph paragraph--compact">
          Bu rota su an Faz 2 kapsaminda yer tutucu olarak aciktir. Form ve API entegrasyonu sonraki
          adimda eklenecek.
        </p>
      </Card>
    </PageContainer>
  );
}
