import { For } from "solid-js";
import { Card } from "../components/ui/Card";
import { PageContainer } from "../components/ui/PageContainer";

const principles = [
  {
    title: "Neden var?",
    text: "Kafede çalışma deneyimi kişiden kişiye değişir. Bu proje, karar sürecini deneme-yanılma yerine veri ve topluluk geri bildirimiyle iyileştirir.",
  },
  {
    title: "Nasıl çalışır?",
    text: "Kullanıcılar kafe detaylarını görüntüler, yöneticiler içerik kalitesini korur, moderatörler ilgili kafeleri güncel tutar.",
  },
  {
    title: "Vizyon",
    text: "Şehir bazlı, güvenilir ve sürekli güncel bir kafede çalışma rehberi oluşturmak.",
  },
];

export default function AboutPage() {
  return (
    <PageContainer
      title="Hakkımızda"
      subtitle="Kahvesiz Çalışma, laptop ile verimli çalışmak isteyenler için topluluk odaklı bir platformdur."
    >
      <Card>
        <p class="paragraph">
          Platformda listelenen kafeler; priz, Wi-Fi, sessizlik, çağrı uygunluğu ve oturma düzeni gibi çalışma
          deneyimini doğrudan etkileyen ölçütlerle paylaşılır.
        </p>
        <p class="paragraph">
          Böylece kullanıcılar kendilerine en uygun mekanı daha hızlı bulabilir; admin ve moderatör rolleri de
          bilginin güncel kalmasına yardım eder.
        </p>
      </Card>

      <div class="grid-three-columns">
        <For each={principles}>
          {(item) => (
            <Card title={item.title}>
              <p class="paragraph paragraph--compact">{item.text}</p>
            </Card>
          )}
        </For>
      </div>
    </PageContainer>
  );
}
