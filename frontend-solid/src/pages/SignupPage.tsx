import { Card } from "../components/ui/Card";
import { PageContainer } from "../components/ui/PageContainer";

export default function SignupPage() {
  return (
    <PageContainer title="Signup" subtitle="Signup formu API sozlesmesine uygun sekilde buraya alinacak.">
      <Card>
        <p class="paragraph paragraph--compact">
          Bu rota su an Faz 2 kapsaminda yer tutucu olarak aciktir. Form dogrulama ve hata akislari
          sonraki adimda eklenecek.
        </p>
      </Card>
    </PageContainer>
  );
}
