import { For } from "solid-js";
import { Card } from "../components/ui/Card";
import { PageContainer } from "../components/ui/PageContainer";

const principles = [
  {
    title: "Neden var?",
    text: "Kafede calisma deneyimi kisiden kisiye degisir. Bu proje, karar surecini deneme-yanilma yerine veri ve topluluk geri bildirimiyle iyilestirir.",
  },
  {
    title: "Nasil calisir?",
    text: "Kullanicilar kafe detaylarini goruntuler, yoneticiler icerik kalitesini korur, moderatorler ilgili kafeleri guncel tutar.",
  },
  {
    title: "Vizyon",
    text: "Sehir bazli, guvenilir ve surekli guncel bir kafede calisma rehberi olusturmak.",
  },
];

export default function AboutPage() {
  return (
    <PageContainer
      title="Hakkimizda"
      subtitle="Kahvesiz Calisma, laptop ile verimli calismak isteyenler icin topluluk odakli bir platformdur."
    >
      <Card>
        <p class="paragraph">
          Platformda listelenen kafeler; priz, Wi-Fi, sessizlik, cagri uygunlugu ve oturma duzeni gibi
          calisma deneyimini dogrudan etkileyen olcutlerle paylasilir.
        </p>
        <p class="paragraph">
          Boylece kullanicilar kendilerine en uygun mekani daha hizli bulabilir; admin ve moderator
          rolleri de bilginin guncel kalmasina yardim eder.
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
