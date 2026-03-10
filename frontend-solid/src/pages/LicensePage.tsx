import { A } from "@solidjs/router";
import { Card } from "../components/ui/Card";
import { PageContainer } from "../components/ui/PageContainer";

export default function LicensePage() {
  return (
    <PageContainer title="Lisans" subtitle="Proje MIT lisansi ile dagitilir.">
      <Card>
        <p class="paragraph">
          Bu proje MIT lisansi ile dagitilir. Lisans, kodun kullanilmasina, degistirilmesine ve
          dagitilmasina izin verir. Baglayici metin icin repo kokundeki LICENSE dosyasi esas alinir.
        </p>

        <div class="policy-section">
          <p class="policy-section__title">Kisa ozet</p>
          <ul class="simple-list">
            <li>Kaynak kodu kullanabilir, degistirebilir ve dagitabilirsiniz.</li>
            <li>Lisans bildirimi ve telif notu korunmalidir.</li>
            <li>Yazilim garanti verilmeden oldugu gibi sunulur.</li>
          </ul>
        </div>

        <div class="policy-section">
          <p class="policy-section__title">Lisans dosyasi</p>
          <p class="paragraph paragraph--compact">
            Tam lisans metni repo kokundeki <code>LICENSE</code> dosyasinda yer alir.
          </p>
        </div>

        <p class="paragraph paragraph--compact">
          Lisans ve kullanim sorulari icin <A class="ui-link" href="/contact">iletisim</A> sayfasi
          kullanilabilir.
        </p>
      </Card>
    </PageContainer>
  );
}
