import { A } from "@solidjs/router";
import { Card } from "../components/ui/Card";
import { PageContainer } from "../components/ui/PageContainer";

export default function LicensePage() {
  return (
    <PageContainer title="Lisans" subtitle="Proje MIT lisansı ile dağıtılır.">
      <Card>
        <p class="paragraph">
          Bu proje MIT lisansı ile dağıtılır. Lisans, kodun kullanılmasına, değiştirilmesine ve dağıtılmasına izin
          verir. Bağlayıcı metin için repo kökündeki LICENSE dosyası esas alınır.
        </p>

        <div class="policy-section">
          <p class="policy-section__title">Kısa özet</p>
          <ul class="simple-list">
            <li>Kaynak kodu kullanabilir, değiştirebilir ve dağıtabilirsiniz.</li>
            <li>Lisans bildirimi ve telif notu korunmalıdır.</li>
            <li>Yazılım garanti verilmeden olduğu gibi sunulur.</li>
          </ul>
        </div>

        <div class="policy-section">
          <p class="policy-section__title">Lisans dosyası</p>
          <p class="paragraph paragraph--compact">
            Tam lisans metni repo kökündeki <code>LICENSE</code> dosyasında yer alır.
          </p>
        </div>

        <p class="paragraph paragraph--compact">
          Lisans ve kullanım soruları için <A class="ui-link" href="/contact">iletişim</A> sayfası kullanılabilir.
        </p>
      </Card>
    </PageContainer>
  );
}
